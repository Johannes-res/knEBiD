#Hier wird Schritt für Schritt das Energiemodell und dessen Optimierung aufgebaut.
# Als erstes wird nur der Sektor Strom betrachtet.
# Die Optimierung wird mit dem Paket Pyomo durchgeführt.

import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import pandas as pd

# Daten einlesen
from daten_einlesen import df_bedarf, df_erzeuger_strom

# Parameter laden
df_parameter = pd.read_excel(r'data\Optimierungsgrößen - Copy.xlsx', index_col=0)



# Nur die Spalten aus df_erzeuger_strom übernehmen, die auch im Index von df_parameter sind
gemeinsame_techs = [t for t in df_erzeuger_strom.columns if t in df_parameter.index]
df_erzeuger_strom = df_erzeuger_strom[gemeinsame_techs]



#Modell erstellen
# zudem wird aus dem Dataframe df_bedarf der Index als Set T extrahiert, der die Zeitpunkte für die Optimierung darstellt.
def create_energy_system_model(df_bedarf):
    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=df_bedarf.index, ordered=True)
    return model


def define_variables(model, df_parameter):
    # Indizierte Variablen für Technologien erstellen
    #dazu wird zunächst aus dem Dataframe der Parameter die Technologien extrahiert
   
    model.techs = pyo.Set(initialize=df_parameter.index.tolist(), ordered=True)
    

    # model.erz_techs = pyo.Set(within=model.techs,initialize=df_parameter[df_parameter['Art'] == 'Erzeuger'].index.tolist(), ordered=True)
    # model.erz_techs_strom = pyo.Set(
    #     within=model.erz_techs,
    #     initialize=df_parameter[(df_parameter['Art'] == 'Erzeuger') & (df_parameter['Energieträger'] == 'Strom')].index.tolist(),
    #     ordered=True)
   # model.spe_techs = pyo.Set(within=model.techs,initialize=df_parameter[df_parameter['Art'] == 'Speicher'].index.tolist(), ordered=True)
   # model.wan_techs = pyo.Set(within=model.techs,initialize=df_parameter[df_parameter['Art'] == 'Wandler'].index.tolist(), ordered=True)
   
    #nun folgen die indizierten Variablen für die unterschiedlichen Technologien
   
    # Kapazitäten der Technologien als Variable
    model.leistung = pyo.Var(model.techs, within=pyo.NonNegativeReals,
                             bounds=lambda m, t: (df_parameter.loc[t, 'untere Grenze [MW]'], df_parameter.loc[t, 'obere Grenze [MW]']))
    # model.spe_kapazitaet = pyo.Var(model.spe_techs, model.T, within=pyo.NonNegativeReals,
    #                          bounds=lambda m, t: (df_parameter.loc[t, 'untere Kapagrenze [MWh]'], df_parameter.loc[t, 'obere Kapagrenze [MWh]']))
    
    return model

#Zielfunktion
#die Summe der einzelnen Kosten für t in m.techs, also jeder Technologie wird mit der leistung der Technologie multipliziert
# und die Summe wird minimiert.
def define_objective(model, df_parameter):
    # Kostenparameter
    def cost_rule(m):
        return sum(df_parameter.loc[t, 'Kosten'] *1000* m.leistung[t] for t in m.techs) #invest/Kw in MW umrechnen
    model.objective = pyo.Objective(rule=cost_rule, sense=pyo.minimize)
    return model


# Nebenbedingungen/Einschränkungen

# Vor define_constraints():
verf_dict = {}
# Nur Technologien verwenden, die sowohl in df_erzeuger_strom als auch in df_parameter vorhanden sind
gueltige_techs = [t for t in df_erzeuger_strom.columns if t in df_parameter.index]
for t in gueltige_techs:
    for ti in df_erzeuger_strom.index:
        verf_dict[(t, ti)] = df_erzeuger_strom.loc[ti, t]


def define_constraints(model, df_bedarf):
    # Strombedarf als Parameter
    model.Strombedarf = pyo.Param(model.T, initialize=df_bedarf['Strom'].to_dict())

   
    
    model.Verf = pyo.Param(model.techs, model.T, initialize=verf_dict, default=0)
    # Erzeugungsgleichung
    def generation_constraint_rule(m, time):
        return sum(
            m.leistung[t] * m.Verf[t, time]
            for t in m.techs
        ) >= m.Strombedarf[time]
    
    model.generation_constraint = pyo.Constraint(model.T, rule=generation_constraint_rule)
    return model

def solve_model(model):
    solver = SolverFactory('cbc')  # oder 'glpk'
    results = solver.solve(model, tee=True)
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        print("Optimale Lösung gefunden:")
        for t in model.techs:
            print(f"{t}: {pyo.value(model.leistung[t]/1000):.2f} GW")
            print(f"Kosten für {t}: {df_parameter.loc[t, 'Kosten'] * pyo.value(model.leistung[t]):.2f} Euro")
        print(f"Gesamtkosten: {pyo.value(model.objective):.2f} Euro")
    else:
        print("Keine optimale Lösung gefunden.")
    return model

def main():
    model = create_energy_system_model(df_bedarf)
    model = define_variables(model, df_parameter)
    model = define_objective(model, df_parameter)
    model = define_constraints(model, df_bedarf)
    solved_model = solve_model(model)
    return solved_model


print(df_erzeuger_strom[gemeinsame_techs].describe())
ergebnis_model = main()
print("Ende der Optimierung")