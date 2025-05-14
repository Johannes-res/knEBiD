import pandas as pd
import numpy as np

df_bedarf = pd.read_excel(r'data\Ausgabe\Bedarf_22_klimaneutral.xlsx')
df_erzeugung = pd.read_excel(r'data\energy-charts\energy-charts_Öffentliche_Nettostromerzeugung_in_Deutschland_2022.xlsx')

#Erzeugerzeitreihe aufbereiten

df_erzeugung = df_erzeugung.iloc[1:].reset_index(drop=True)
df_erzeugung['Datum (UTC)'] = pd.to_datetime(df_erzeugung['Datum (UTC)'])
df_erzeugung = df_erzeugung.set_index('Datum (UTC)')
df_erzeugung = df_erzeugung[df_erzeugung.index.year == 2022]

df_bedarf['Datum (UTC)'] = pd.to_datetime(df_bedarf['Datum (UTC)'])
df_bedarf = df_bedarf.set_index('Datum (UTC)')
# Filter für 2022
df_bedarf = df_bedarf[df_bedarf.index.year == 2022]

# Werte der Spalten normalisieren (Maximum als Betrag)
for col in df_erzeugung.columns:
    max_val = df_erzeugung[col].abs().max()
    if max_val != 0:
        df_erzeugung[col] = df_erzeugung[col] / max_val





from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, PULP_CBC_CMD


prob = LpProblem("Kostenoptimierung", LpMinimize)

#%%Variablen
#Variablen Erzeuger
Leistung_PV = LpVariable("installierte Leistung PV", lowBound=0, upBound=1000000)  # max 1000000 MWp
Leistung_Wind_Offshore = LpVariable("installierte Leistung Wind Offshore", lowBound=0, upBound=1000000)  # max 1000000 MWp
Leistung_Wind_Onshore = LpVariable("installierte Leistung Wind Onshore", lowBound=0, upBound=1000000)  # max 1000000 MWp
Speicherkapazitaet = LpVariable("Speicherkapazitaet", lowBound=0)
# Zeitvariable Speicher
Leistung_Einspeichern_Batterie = LpVariable.dicts("Einspeichern_Batterie", df_erzeugung.index, lowBound=0)
Leistung_Ausspeichern_Batterie = LpVariable.dicts("Ausspeichern_Batterie", df_erzeugung.index, lowBound=0)
Speicherstand_Batterie = LpVariable.dicts("Speicherstand_Batterie", df_erzeugung.index, lowBound=0)

#Eingangsgrößen
Kosten_PV = 1000 #€/kwp
Kosten_Wind_Offshore = 2000 #€/kWh
Kosten_Wind_Onshore = 1500 #€/kWh
#Kosten Batteriespeicher
Kosten_Batterie = 2000 #€/kWh

# Anfangsspeicher
prob += Speicherstand_Batterie[df_erzeugung.index[0]] == 0

# Speicherbilanz
for i, t in enumerate(df_erzeugung.index):
    if i == 0:
        continue
    prev_t = df_erzeugung.index[i-1]
    prob += Speicherstand_Batterie[t] == Speicherstand_Batterie[prev_t]  + Leistung_Einspeichern_Batterie[prev_t] * 0.95 * 0.25  - Leistung_Ausspeichern_Batterie[prev_t] * 0.95 * 0.25
    prob += Speicherstand_Batterie[t] <= Speicherkapazitaet

    # Erzeugungs-/Bedarfsbilanz
for t in df_erzeugung.index:
    erzeugung = (
        df_erzeugung['Solar'][t] * Leistung_PV
        + df_erzeugung['Wind Offshore'][t] * Leistung_Wind_Offshore
        + df_erzeugung['Wind Onshore'][t] * Leistung_Wind_Onshore
    )
    last = df_bedarf['Strom_22_org [MWh]'][t]
    prob += erzeugung + Leistung_Ausspeichern_Batterie[t] >= last + Leistung_Einspeichern_Batterie[t]



#Bedingungen/Constraints
# # Erzeugung >= Bedarf zu allen Zeitpunkten
# for i in df_erzeugung.index:
#     prob += (df_erzeugung['Solar'][i] * Leistung_PV + df_erzeugung['Wind Offshore'][i] * Leistung_Wind_Offshore + df_erzeugung['Wind Onshore'][i] * Leistung_Wind_Onshore - df_bedarf['Strom_22_org [MWh]'][i]) >= 0
# Anfangsspeicherstand
prob += Speicherstand_Batterie[df_erzeugung.index[0]] == 500


#Opjective Function
prob += (
    Leistung_PV * Kosten_PV
    + Leistung_Wind_Offshore * Kosten_Wind_Offshore
    + Leistung_Wind_Onshore * Kosten_Wind_Onshore
    + Speicherkapazitaet * Kosten_Batterie
)

prob.solve(PULP_CBC_CMD())

df_results = pd.DataFrame({
    'Speicherstand': [Speicherstand_Batterie[t].varValue for t in df_erzeugung.index],
    'Ladeleistung': [Leistung_Einspeichern_Batterie[t].varValue for t in df_erzeugung.index],
    'Entladeleistung': [Leistung_Ausspeichern_Batterie[t].varValue for t in df_erzeugung.index],
    'PV Leistung': [Leistung_PV.varValue * df_erzeugung['Solar'][t] for t in df_erzeugung.index],
    'Wind Offshore Leistung': [Leistung_Wind_Offshore.varValue * df_erzeugung['Wind Offshore'][t] for t in df_erzeugung.index],
    'Wind Onshore Leistung': [Leistung_Wind_Onshore.varValue * df_erzeugung['Wind Onshore'][t] for t in df_erzeugung.index],
    }, index=df_erzeugung.index)

print("Gesamtkosten:", prob.objective.value())
print("Installierte Leistung PV:", Leistung_PV.varValue)
print("Installierte Leistung Wind Offshore:", Leistung_Wind_Offshore.varValue)
print("Installierte Leistung Wind Onshore:", Leistung_Wind_Onshore.varValue)

print('Ende der Optimierung')