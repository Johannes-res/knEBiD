import numpy as np
import pandas as pd
from scipy.optimize import minimize

# Annahmen:
# - df_demand: DataFrame mit Spalte 'demand' (Strombedarf in kW pro Viertelstunde)
# - df_generation: DataFrame mit normierten Erzeugungsprofilen (0–1) je Technologie
# - costs: Kosten pro kW installierter Leistung je Technologie (z.B. [€/kW])

df_demand = pd.read_excel(r'data\Ausgabe\Bedarf_22_klimaneutral.xlsx')

df_erzeugung = pd.read_excel(r'data\energy-charts\energy-charts_Öffentliche_Nettostromerzeugung_in_Deutschland_2022.xlsx')

#Erzeugerzeitreihe aufbereiten

df_erzeugung = df_erzeugung.iloc[1:].reset_index(drop=True)
df_erzeugung['Datum (UTC)'] = pd.to_datetime(df_erzeugung['Datum (UTC)'])
df_erzeugung = df_erzeugung.set_index('Datum (UTC)')
df_erzeugung = df_erzeugung[df_erzeugung.index.year == 2022]

# Werte der Spalten normalisieren (Maximum als Betrag)
for col in df_erzeugung.columns:
    max_val = df_erzeugung[col].abs().max()
    if max_val != 0:
        df_erzeugung[col] = df_erzeugung[col] / max_val

df_generation = pd.DataFrame()
df_generation['Solar'] = df_erzeugung['Solar']
df_generation['Wind Offshore'] = df_erzeugung['Wind Offshore']
df_generation['Wind Onshore'] = df_erzeugung['Wind Onshore']
# Beispielhafte Kosten pro kW installierter Leistung
costs = np.array([1000, 2000, 1500])  # Beispielwerte für PV, Wind, Biomasse


def optimize_capacities(df_demand, df_generation, costs):
    # Zielfunktion: Minimierung der Gesamtkosten
    def objective(x):
        return np.dot(costs, x)
    
    # Nebenbedingung: Erzeugung ≥ Bedarf zu allen Zeitpunkten
    def constraint(x):
        total_generation = df_generation.values @ x
        return total_generation - df_demand['Strom_22_org [MWh]'].values
    
    # Initiale Schätzung und Grenzen (Leistung ≥ 0)
    x0 = np.ones(len(costs))  # Startwert: 1 kW je Technologie
    bounds = [(0, None) for _ in costs]
    
    # Optimierung mit SLSQP
    result = minimize(
        objective,
        x0,
        method='SLSQP',
        bounds=bounds,
        constraints={'type': 'ineq', 'fun': constraint}
    )
    
    return result.x

installed_capacities = optimize_capacities(df_demand, df_generation, costs)

print('Ende der Optimierung')