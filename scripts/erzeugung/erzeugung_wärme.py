import pandas as pd


df_erzeuger_strom = pd.read_excel(r'data\energy-charts\energy-charts_Öffentliche_Nettostromerzeugung_in_Deutschland_2022.xlsx')
df_erzeuger_strom = df_erzeuger_strom.drop(index=0).reset_index(drop=True)
df_erzeuger_strom['Solar'] = df_erzeuger_strom['Solar'].astype(int)
df_erzeuger_strom['Biomasse'] = df_erzeuger_strom['Biomasse'].astype(int)
df_erzeuger_strom['Solar_normiert'] = df_erzeuger_strom['Solar'] / df_erzeuger_strom['Solar'].abs().max()  # Normalisierung der Solarwerte
df_erzeuger_strom['Biomasse_normiert'] = df_erzeuger_strom['Biomasse'] / df_erzeuger_strom['Biomasse'].abs().max()  # Normalisierung der Biomassewerte

# Erstelle einen DatetimeIndex mit 15-Minuten-Intervallen für das Jahr 2022
index = pd.date_range(start="2022-01-01 00:00", end="2022-12-31 23:45", freq="15T")

# Erstelle einen leeren DataFrame mit diesem Index und den gewünschten Spalten
df = pd.DataFrame(index=index, columns=['Flächengeothermie', 'Tiefengeothermie', 'Solarthermie', 'Biomasse'])

# Setze die Werte für Flächengeothermie und Tiefengeothermie auf 1
df['Flächengeothermie'] = 1
df['Tiefengeothermie'] = 1

# Übertrage die Werte aus der Spalte 'Solar' von df_strom auf 'Solarthermie'
# Übernehme die Werte bei passenden Index, sonst NaN
df['Solarthermie'] = pd.NA
df['Biomasse'] = pd.NA

min_len = min(len(df), len(df_erzeuger_strom))
df.loc[df.index[:min_len], 'Solarthermie'] = df_erzeuger_strom['Solar_normiert'].iloc[:min_len].values
df.loc[df.index[:min_len], 'Biomasse'] = df_erzeuger_strom['Biomasse_normiert'].iloc[:min_len].values

df.to_excel(r'data\Ausgabe\erzeugung_waerme_22.xlsx', index=True)
# Ausgabe des DataFrames
print('Ende des erzeugung_wärme.py Skripts')