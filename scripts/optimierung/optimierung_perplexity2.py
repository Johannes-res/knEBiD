import pyomo.environ as pyo
import pulp
import pandas as pd
import numpy as np

df_bedarf_org = pd.read_excel(r'data\Ausgabe\Bedarf_22_klimaneutral.xlsx')
df_erzeuger_strom = pd.read_excel(r'data\energy-charts\energy-charts_Öffentliche_Nettostromerzeugung_in_Deutschland_2022.xlsx')
df_erzeuger_wärme = pd.read_excel(r'data\Ausgabe\erzeugung_waerme_22.xlsx')
df_erzeuger_strom.index = pd.to_datetime(df_erzeuger_strom.iloc[:, 0], format='%Y-%m-%d %H:%M:%S')
df_erzeuger_wärme.index = pd.to_datetime(df_erzeuger_wärme.iloc[:, 0], format='%Y-%m-%d %H:%M:%S')
# Erzeugerzeitreihe aufbereiten
df_bedarf = pd.DataFrame()
df_bedarf.index = df_bedarf_org['Datum (UTC)']
df_bedarf['Strom'] = df_bedarf_org['Last_prognose [MWh]'] * 4 + df_bedarf_org['EMobilität']*4 # Umwandlung von MWh in MW (4 Viertelstunden pro Stunde)
df_bedarf['Wasserstoff'] = df_bedarf_org['Wasserstoff'] * 4  # Umwandlung von MWh in MW
df_bedarf['Wärme'] = df_bedarf_org['Wärmepumpen'] * 4 + df_bedarf_org['Thermie']  # Umwandlung von MWh in MW beispielhaft zunächst mit der Wärmepumpenzeitreihe+Thermie
df_bedarf['E-Fuel'] = df_bedarf_org['E-Fuels'] * 4  # Umwandlung von MWh in MW
df_bedarf['Biomasse'] = df_bedarf_org['Biomasse'] * 4  # Umwandlung von MWh in MW


# Begrenze die DataFrames auf eine bestimmte Woche (z.B. Kalenderwoche 10)
# Annahme: df_bedarf hat eine Spalte 'Datum' oder einen DatetimeIndex
start_date = '2022-03-07'  # Beispiel: Montag der gewünschten Woche
end_date = '2022-03-13'    # Beispiel: Sonntag der gewünschten Woche

def begrenze_auf_zeitraum(df, start_date, end_date):
    """
    Begrenze DataFrame auf den Zeitraum zwischen start_date und end_date (inklusive).
    Annahme: Das Datum befindet sich im Index und ist vom Typ DatetimeIndex.
    """
    df = df.copy()
    df.index = pd.to_datetime(df.index)  # Sicherstellen, dass der Index ein DatetimeIndex ist])
    return df.loc[(df.index >= pd.to_datetime(start_date)) & (df.index <= pd.to_datetime(end_date))]

df_bedarf = begrenze_auf_zeitraum(df_bedarf, start_date, end_date)
df_erzeuger_strom = begrenze_auf_zeitraum(df_erzeuger_strom, start_date, end_date)
df_erzeuger_wärme = begrenze_auf_zeitraum(df_erzeuger_wärme, start_date, end_date)

# Sicherstellen, dass keine NaN-Werte in den relevanten DataFrames vorhanden sind
df_bedarf = df_bedarf.fillna(0)
df_erzeuger_strom = df_erzeuger_strom.fillna(0)
df_erzeuger_wärme = df_erzeuger_wärme.fillna(0)

# Gemeinsame Zeitbasis für alle DataFrames
common_index = df_bedarf.index.intersection(df_erzeuger_strom.index).intersection(df_erzeuger_wärme.index)
df_bedarf = df_bedarf.loc[common_index]
df_erzeuger_strom = df_erzeuger_strom.loc[common_index]
df_erzeuger_wärme = df_erzeuger_wärme.loc[common_index]

def create_energy_system_model(df_bedarf, df_erzeuger_strom, df_erzeuger_wärme):
    # Modell-Initialisierung
    model = pyo.ConcreteModel()
    
    # Zeitindex definieren
    model.T = pyo.Set(initialize=df_bedarf.index, ordered=True)
    
    return model

# Definieren der maximalen Kapazitäten für die Erzeuger und Speicher
max_capacities = {}
max_kernenergie = 15000  # Beispielwert in MW
max_laufwasser = 10000  # Beispielwert in MW
max_biomasse = 5000    # Beispielwert in MW
max_geothermie = 3000  # Beispielwert in MW
max_speicherwasser = 2000  # Beispielwert in MW
max_muell = 1500       # Beispielwert in MW
max_wind_offshore = 8000  # Beispielwert in MW
max_wind_onshore = 12000  # Beispielwert in MW
max_solar = 10000      # Beispielwert in MW
max_flaechengeothermie = 2000  # Beispielwert in MW
max_tiefengeothermie = 1000  # Beispielwert in MW
max_solarthermie = 500  # Beispielwert in MW
max_biomasse_waerme = 1000  # Beispielwert in MW
max_batterie = 1000  # Beispielwert in MW
max_pump = 500  # Beispielwert in MW
max_h2_kaverne = 2000  # Beispielwert in MW
max_h2_druck = 1000  # Beispielwert in MW
max_batterie_kap = 1000  # Beispielwert in MW
max_pump_kap = 500  # Beispielwert in MW
max_h2_kaverne_kap = 2000  # Beispielwert in MW
max_h2_druck_kap = 1000  # Beispielwert in MW   
max_waerme_sp = 5000  # Beispielwert in MW
max_waerme_kap = 5000  # Beispielwert in MW
# Kosten für die Erzeuger und Speicher
costs = {
    'ces1': 1000,  # Kosten Kernenergie pro kW
    'ces2': 800,   # Kosten Laufwasser pro kW
    'ces3': 600,   # Kosten Biomasse pro kW
    'ces4': 700,   # Kosten Geothermie pro kW
    'ces5': 500,   # Kosten Speicherwasser pro kW
    'ces6': 400,   # Kosten Müll pro kW
    'ces7': 900,   # Kosten Wind Offshore pro kW
    'ces8': 850,   # Kosten Wind Onshore pro kW
    'ces9': 950,   # Kosten Solar pro kW
    'cewä1': 300,  # Kosten Flächengeothermie pro kW
    'cewä2': 350,  # Kosten Tiefengeothermie pro kW
    'cewä3': 250,  # Kosten Solarthermie pro kW
    'cewä4': 400,  # Kosten Biomasse Wärme pro kW
    'cspks1': 50,  # Kosten Batteriespeicher pro kW
    'cspks2': 60,  # Kosten Pumpspeicher pro kW
    'cspks31': 70, # Kosten Wasserstoffspeicher Kaverne pro kW
    'cspks32': 80, # Kosten Wasserstoffspeicher Druckgas pro kW
    'cspkwä1': 40, # Kosten Wärmespeicher pro kW
    'cw1sh': 200,  # Kosten Elektrolyseur pro kW
    'cw2hs': 300,  # Kosten Brennstoffzelle pro kW
    'cw3hw': 250,  # Kosten Wasserstoffheizung pro kW
    'cw41sw': 150, # Kosten Luft-Wasser-Wärmepumpe pro kW
    'cw42sw': 180  # Kosten Sole-Wasser-Wärmepumpe pro kW
}
# Effizienzwerte für die Wandler
efficiencies = {
    'ef_w1_sh': 0.7,  # Effizienz Elektrolyseur
    'ef_w2_hs': 0.6,  # Effizienz Brennstoffzelle
    'ef_w3_hw': 0.8,  # Effizienz Wasserstoffheizung
    'ef_w41_sw': 0.9, # Effizienz Luft-Wasser-Wärmepumpe
    'ef_w42_sw': 0.85, # Effizienz Sole-Wasser-Wärmepumpe
}


def define_variables(model):
    # Stromerzeuger-Kapazitäten
    model.es1 = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_kernenergie))  # Kernenergie
    model.es2 = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_laufwasser))
    model.es3 = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_biomasse))
    model.es4 = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_geothermie))
    model.es5 = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_speicherwasser))
    model.es6 = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_muell))
    model.es7 = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_wind_offshore))
    model.es8 = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_wind_onshore))
    model.es9 = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_solar))
    
    # Wärmeerzeuger-Kapazitäten
    model.ewä1 = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_flaechengeothermie))
    model.ewä2 = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_tiefengeothermie))
    model.ewä3 = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_solarthermie))
    model.ewä4 = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_biomasse_waerme))
    
    # Speicher-Lade/Entladeleistung (zeitabhängig)
    model.sps1 = pyo.Var(model.T, within=pyo.Reals, bounds=(-max_batterie, max_batterie))
    model.sps2 = pyo.Var(model.T, within=pyo.Reals, bounds=(-max_pump, max_pump))
    model.sps31 = pyo.Var(model.T, within=pyo.Reals, bounds=(-max_h2_kaverne, max_h2_kaverne))
    model.sps32 = pyo.Var(model.T, within=pyo.Reals, bounds=(-max_h2_druck, max_h2_druck))
    model.spwä1 = pyo.Var(model.T, within=pyo.Reals, bounds=(-max_waerme_sp, max_waerme_sp))
    model.spf1 = pyo.Var(model.T, within=pyo.Reals)
    model.spbm1 = pyo.Var(model.T, within=pyo.Reals)
    
    # Speicherstand (zeitabhängig)
    model.spks1 = pyo.Var(model.T, within=pyo.NonNegativeReals, bounds=(0, max_batterie_kap))
    model.spks2 = pyo.Var(model.T, within=pyo.NonNegativeReals, bounds=(0, max_pump_kap))
    model.spks31 = pyo.Var(model.T, within=pyo.NonNegativeReals, bounds=(0, max_h2_kaverne_kap))
    model.spks32 = pyo.Var(model.T, within=pyo.NonNegativeReals, bounds=(0, max_h2_druck_kap))
    model.spkwä1 = pyo.Var(model.T, within=pyo.NonNegativeReals, bounds=(0, max_waerme_kap))
    model.spkf1 = pyo.Var(model.T, within=pyo.NonNegativeReals)
    model.spkbm1 = pyo.Var(model.T, within=pyo.NonNegativeReals)
    
    # Wandler-Kapazitäten
    model.w1_sh = pyo.Var(within=pyo.NonNegativeReals)  # Elektrolyseur
    model.w2_hs = pyo.Var(within=pyo.NonNegativeReals)  # Brennstoffzelle
    model.w3_hw = pyo.Var(within=pyo.NonNegativeReals)  # Wasserstoffheizung
    model.w41_sw = pyo.Var(within=pyo.NonNegativeReals)  # Luft-Wasser-Wärmepumpe
    model.w42_sw = pyo.Var(within=pyo.NonNegativeReals)  # Sole-Wasser-Wärmepumpe

    # Speicher-Maximum-Variablen für die Kostenfunktion
    model.spks1_max = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_batterie_kap))
    model.spks2_max = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_pump_kap))
    model.spks31_max = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_h2_kaverne_kap))
    model.spks32_max = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_h2_druck_kap))
    model.spkwä1_max = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, max_waerme_kap))

    # Constraints, damit die Maximalvariablen wirklich das Maximum der Speicherstände sind
    def max_storage_constraint_rule(model, t):
        return model.spks1_max >= model.spks1[t]
    model.spks1_max_constraint = pyo.Constraint(model.T, rule=max_storage_constraint_rule)

    def max_storage2_constraint_rule(model, t):
        return model.spks2_max >= model.spks2[t]
    model.spks2_max_constraint = pyo.Constraint(model.T, rule=max_storage2_constraint_rule)

    def max_storage31_constraint_rule(model, t):
        return model.spks31_max >= model.spks31[t]
    model.spks31_max_constraint = pyo.Constraint(model.T, rule=max_storage31_constraint_rule)

    def max_storage32_constraint_rule(model, t):
        return model.spks32_max >= model.spks32[t]
    model.spks32_max_constraint = pyo.Constraint(model.T, rule=max_storage32_constraint_rule)

    def max_storagewae1_constraint_rule(model, t):
        return model.spkwä1_max >= model.spkwä1[t]
    model.spkwä1_max_constraint = pyo.Constraint(model.T, rule=max_storagewae1_constraint_rule)

def define_objective(model, costs):
    # Erzeugerkosten
    generator_costs = (
        costs['ces1'] * model.es1 + costs['ces2'] * model.es2 + 
        costs['ces3'] * model.es3 + costs['ces4'] * model.es4 + 
        costs['ces5'] * model.es5 + costs['ces6'] * model.es6 + 
        costs['ces7'] * model.es7 + costs['ces8'] * model.es8 + 
        costs['ces9'] * model.es9 + costs['cewä1'] * model.ewä1 + 
        costs['cewä2'] * model.ewä2 + costs['cewä3'] * model.ewä3 + 
        costs['cewä4'] * model.ewä4
    )
    
    # Speicherkosten (basierend auf maximaler Kapazität)
    storage_costs = (
        costs['cspks1'] * model.spks1_max +
        costs['cspks2'] * model.spks2_max +
        costs['cspks31'] * model.spks31_max +
        costs['cspks32'] * model.spks32_max +
        costs['cspkwä1'] * model.spkwä1_max
    )
    
    # Wandlerkosten
    converter_costs = (
        costs['cw1sh'] * model.w1_sh + costs['cw2hs'] * model.w2_hs + 
        costs['cw3hw'] * model.w3_hw + costs['cw41sw'] * model.w41_sw + 
        costs['cw42sw'] * model.w42_sw
    )
    
    model.objective = pyo.Objective(
        expr=generator_costs + storage_costs + converter_costs,
        sense=pyo.minimize
    )

def define_energy_balances(model, df_bedarf, df_erzeuger_strom, df_erzeuger_wärme, efficiencies):
    # Strombilanz für jeden Zeitpunkt
    def electricity_balance_rule(model, t):
        # Stromerzeugung
        generation = (
            model.es1 * df_erzeuger_strom.loc[t, 'Kernenergie'] +
            model.es2 * df_erzeuger_strom.loc[t, 'Laufwasser'] +
            model.es3 * df_erzeuger_strom.loc[t, 'Biomasse'] +
            model.es4 * df_erzeuger_strom.loc[t, 'Geothermie'] +
            model.es5 * df_erzeuger_strom.loc[t, 'Speicherwasser'] +
            model.es6 * df_erzeuger_strom.loc[t, 'Müll'] +
            model.es7 * df_erzeuger_strom.loc[t, 'Wind Offshore'] +
            model.es8 * df_erzeuger_strom.loc[t, 'Wind Onshore'] +
            model.es9 * df_erzeuger_strom.loc[t, 'Solar']
        )
        
        # Speicherentladung (negativ = Entladung)
        storage_discharge = -(model.sps1[t] + model.sps2[t])
        
        # Stromerzeugende Wandler
        converters_to_electricity = model.w2_hs * efficiencies['ef_w2_hs']
        
        # Stromverbrauchende Wandler  
        converters_from_electricity = (
            model.w1_sh + model.w41_sw + model.w42_sw
        )
        
        return generation + storage_discharge + converters_to_electricity - converters_from_electricity >= df_bedarf.loc[t, 'Strom']
    
    model.electricity_balance = pyo.Constraint(model.T, rule=electricity_balance_rule)
    
    # Wasserstoffbilanz
    def hydrogen_balance_rule(model, t):
        # Wasserstofferzeugung durch Elektrolyse
        h2_generation = model.w1_sh * efficiencies['ef_w1_sh']
        
        # Wasserstoffspeicher-Entladung
        h2_storage_discharge = -(model.sps31[t] + model.sps32[t])
        
        # Wasserstoffverbrauch
        h2_consumption = (
            model.w2_hs / efficiencies['ef_w2_hs'] +
            model.w3_hw / efficiencies['ef_w3_hw']
        )
        
        return h2_generation + h2_storage_discharge - h2_consumption >= df_bedarf.loc[t, 'Wasserstoff']
    
    model.hydrogen_balance = pyo.Constraint(model.T, rule=hydrogen_balance_rule)
    
    # Wärmebilanz
    def heat_balance_rule(model, t):
        # Wärmeerzeugung
        heat_generation = (
            model.ewä1 * df_erzeuger_wärme.loc[t, 'Flächengeothermie'] +
            model.ewä2 * df_erzeuger_wärme.loc[t, 'Tiefengeothermie'] +
            model.ewä3 * df_erzeuger_wärme.loc[t, 'Solarthermie'] +
            model.ewä4 * df_erzeuger_wärme.loc[t, 'Biomasse']
        )
        
        # Wärme aus Wandlern
        heat_from_converters = (
            model.w3_hw * efficiencies['ef_w3_hw'] +
            model.w41_sw * efficiencies['ef_w41_sw'] +
            model.w42_sw * efficiencies['ef_w42_sw']
        )
        
        # Wärmespeicher-Entladung
        heat_storage_discharge = -model.spwä1[t]
        
        return heat_generation + heat_from_converters + heat_storage_discharge >= df_bedarf.loc[t, 'Wärme']
    
    model.heat_balance = pyo.Constraint(model.T, rule=heat_balance_rule)

def define_storage_dynamics(model):
    # Batteriespeicher-Dynamik
    def battery_state_rule(model, t):
        if t == model.T.first():
            return model.spks1[t] == model.sps1[t] * 0.25  # Startwert + erste Ladung
        else:
            t_prev = model.T.prev(t)
            return model.spks1[t] == model.spks1[t_prev] + model.sps1[t_prev] * 0.25
    
    model.battery_state = pyo.Constraint(model.T, rule=battery_state_rule)
    
    # Pumpspeicher-Dynamik
    def pumped_storage_state_rule(model, t):
        if t == model.T.first():
            return model.spks2[t] == model.sps2[t] * 0.25
        else:
            t_prev = model.T.prev(t)
            return model.spks2[t] == model.spks2[t_prev] + model.sps2[t_prev] * 0.25
    
    model.pumped_storage_state = pyo.Constraint(model.T, rule=pumped_storage_state_rule)
    
    # Wasserstoffspeicher Kaverne
    def h2_cavern_state_rule(model, t):
        if t == model.T.first():
            return model.spks31[t] == model.sps31[t] * 0.25
        else:
            t_prev = model.T.prev(t)
            return model.spks31[t] == model.spks31[t_prev] + model.sps31[t_prev] * 0.25
    
    model.h2_cavern_state = pyo.Constraint(model.T, rule=h2_cavern_state_rule)
    
    # Wasserstoffspeicher Druckgas
    def h2_pressure_state_rule(model, t):
        if t == model.T.first():
            return model.spks32[t] == model.sps32[t] * 0.25
        else:
            t_prev = model.T.prev(t)
            return model.spks32[t] == model.spks32[t_prev] + model.sps32[t_prev] * 0.25
    
    model.h2_pressure_state = pyo.Constraint(model.T, rule=h2_pressure_state_rule)
    
    # Wärmespeicher-Dynamik
    def heat_storage_state_rule(model, t):
        if t == model.T.first():
            return model.spkwä1[t] == model.spwä1[t] * 0.25
        else:
            t_prev = model.T.prev(t)
            return model.spkwä1[t] == model.spkwä1[t_prev] + model.spwä1[t_prev] * 0.25
    
    model.heat_storage_state = pyo.Constraint(model.T, rule=heat_storage_state_rule)

def solve_energy_system_optimization(df_bedarf, df_erzeuger_strom, df_erzeuger_wärme, 
                                   costs, efficiencies, max_capacities):
    """
    Hauptfunktion zur Lösung des Energiesystem-Optimierungsproblems
    """
    # Modell erstellen
    model = create_energy_system_model(df_bedarf, df_erzeuger_strom, df_erzeuger_wärme)
    
    # Variablen definieren
    define_variables(model)
    
    # Zielfunktion definieren
    define_objective(model, costs)
    
    # Energiebilanzen definieren
    define_energy_balances(model, df_bedarf, df_erzeuger_strom, df_erzeuger_wärme, efficiencies)
    
    # Speicherdynamik definieren
    define_storage_dynamics(model)
    
    # Solver-Optionen
    solver = pyo.SolverFactory('cbc')  # oder 'glpk', 'cplex', 'gurobi'
    solver.options['seconds'] = 3600  # 1 Stunde Zeitlimit (cbc uses 'seconds')
    # CBC does not use 'MIPGap' but 'ratioGap'
    solver.options['ratioGap'] = 0.01     # 1% Optimierungslücke
    
    # Modell lösen
    results = solver.solve(model, tee=True)
    
    # Ergebnisse extrahieren
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        return extract_results(model, df_bedarf.index)
    else:
        raise RuntimeError(f"Optimization failed: {results.solver.termination_condition}")

def extract_results(model, time_index):
    """
    Extrahierung der Optimierungsergebnisse
    """
    results = {}
    
    # Installierte Kapazitäten
    results['generator_capacities'] = {
        'Kernenergie': pyo.value(model.es1),
        'Laufwasser': pyo.value(model.es2),
        'Biomasse': pyo.value(model.es3),
        'Geothermie': pyo.value(model.es4),
        'Speicherwasser': pyo.value(model.es5),
        'Müll': pyo.value(model.es6),
        'Wind_Offshore': pyo.value(model.es7),
        'Wind_Onshore': pyo.value(model.es8),
        'Solar': pyo.value(model.es9)
    }
    
    # Speicher-Zeitreihen erstellen
    df_storage_results = pd.DataFrame(index=time_index)
    df_storage_results['Batteriespeicherladung'] = [pyo.value(model.sps1[t]) for t in time_index]
    df_storage_results['Batteriespeicherstand'] = [pyo.value(model.spks1[t]) for t in time_index]
    df_storage_results['Pumpspeicherladung'] = [pyo.value(model.sps2[t]) for t in time_index]
    df_storage_results['Pumpspeicherstand'] = [pyo.value(model.spks2[t]) for t in time_index]
    
    results['storage_timeseries'] = df_storage_results
    results['total_cost'] = pyo.value(model.objective)
    
    return results

ergebnisse= solve_energy_system_optimization(df_bedarf, df_erzeuger_strom, df_erzeuger_wärme, 
                                   costs, efficiencies, max_capacities=None)


ergebnisse_df = pd.DataFrame(ergebnisse['generator_capacities'], index=[0])
ergebnisse_df = pd.concat([ergebnisse_df, ergebnisse['storage_timeseries']], axis=1)
ergebnisse_df.to_excel(r'data\Ausgabe\optimierung_ergebnisse.xlsx', index=True)
print('Ende der Optimierung')
