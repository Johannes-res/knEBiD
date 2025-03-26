import pandas as pd


#%%
# Daten laden
df_energy_charts = pd.read_excel(r'data\energy-charts\energy-charts_Öffentliche_Nettostromerzeugung_in_Deutschland_2022.xlsx')
#lädt die Zeitreihen der Nettostromerzeugung in Deutschland für das Jahr 2022
df_AGEB = pd.read_excel(r'data\Endenergiebedarf_AGEB\EBD22e.xlsx')
#lädt die Endenergiebedarfsdaten für das Jahr 2022



#%% Zeitreihe aufbereiten
#Datum als Index setzen und in Datetime umwandeln sowie erste Zeile löschen

df_energy_charts.set_index('Datum (UTC)', inplace=True)
df_energy_charts.index = pd.to_datetime(df_energy_charts.index)
df_energy_charts = df_energy_charts.drop(df_energy_charts.index[0])


# Wählen Sie das gewünschte Jahr aus (z.B. 2022)
year = 2022

# Erstellen Sie Start- und Enddatum für das ausgewählte Jahr
start_date = f"{year}-01-01 00:00:00"
end_date = f"{year}-12-31 23:45:00"

# Wählen Sie die Daten für das spezifische Jahr aus
df_selected = df_energy_charts.loc[start_date:end_date]

df_Nettostromerzeugung_22 = df_selected

#%%Endenergiebedarfe für die einzelnen Sektoren aus df extrahieren
df_AGEB.set_index(df_AGEB.columns[0], inplace=True)

# Funktion, die mehrere Werte aus einem DataFrame holt
def get_values_from_dataframe(df, queries):
    """
    Holt mehrere Werte aus einem DataFrame basierend auf einer Liste von Abfragen.

    :param df: Der DataFrame, aus dem die Werte geholt werden sollen.
    :param queries: Eine Liste von Tupeln (row_name, column_name), die die gewünschten Einträge spezifizieren.
    :return: Ein DataFrame mit den Ergebnissen.
    """
    results = []
    for row_name, column_name in queries:
        try:
            value = df.loc[row_name, column_name]
            results.append({'Row': row_name, 'Column': column_name, 'Value': value})
        except KeyError:
            results.append({'Row': row_name, 'Column': column_name, 'Value': 'Fehler: Nicht gefunden'})
    return pd.DataFrame(results)

# Summe der Endenergieverbräuche
queries = [
    ('ENDENERGIEVERBRAUCH', 'Unnamed: 34'),
    ('Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe', 'Unnamed: 34'),
    ('Verkehr insgesamt', 'Unnamed: 34'),
    ('Haushalte, Gewerbe, Handel und Dienstleistungen', 'Unnamed: 34')
]

df_answer = get_values_from_dataframe(df_AGEB, queries)


df_EEB_Sektoren=pd.DataFrame()
df_EEB_Sektoren['Summe'] = df_answer.set_index('Row')['Value']  # Setzt 'Row' als Index und übernimmt die Werte aus 'Value'


# Stromverbrauch
queries = [
    ('ENDENERGIEVERBRAUCH', 'Unnamed: 29'),
    ('Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe', 'Unnamed: 29'),
    ('Verkehr insgesamt', 'Unnamed: 29'),
    ('Haushalte, Gewerbe, Handel und Dienstleistungen', 'Unnamed: 29')
]

df_answer = get_values_from_dataframe(df_AGEB, queries)
df_EEB_Sektoren['Strom'] = df_answer.set_index('Row')['Value']  # Ergänzt die Werte aus 'Value' passend zum Index


#df_EEB_Sektoren = df_EEB_Sektoren.drop(df_EEB_Sektoren.index[0])

df_EEB_Sektoren.loc['Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe','Anteil_Summe']=df_EEB_Sektoren.loc['Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe','Summe']/df_EEB_Sektoren.loc['ENDENERGIEVERBRAUCH','Summe']
df_EEB_Sektoren.loc['Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe','Anteil_Strom']=df_EEB_Sektoren.loc['Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe','Strom']/df_EEB_Sektoren.loc['ENDENERGIEVERBRAUCH','Strom']

df_EEB_Sektoren.loc['Verkehr insgesamt','Anteil_Summe']=df_EEB_Sektoren.loc['Verkehr insgesamt','Summe']/df_EEB_Sektoren.loc['ENDENERGIEVERBRAUCH','Summe']
df_EEB_Sektoren.loc['Verkehr insgesamt','Anteil_Strom']=df_EEB_Sektoren.loc['Verkehr insgesamt','Strom']/df_EEB_Sektoren.loc['ENDENERGIEVERBRAUCH','Strom']

df_EEB_Sektoren.loc['Haushalte, Gewerbe, Handel und Dienstleistungen','Anteil_Summe']=df_EEB_Sektoren.loc['Haushalte, Gewerbe, Handel und Dienstleistungen','Summe']/df_EEB_Sektoren.loc['ENDENERGIEVERBRAUCH','Summe']
df_EEB_Sektoren.loc['Haushalte, Gewerbe, Handel und Dienstleistungen','Anteil_Strom']=df_EEB_Sektoren.loc['Haushalte, Gewerbe, Handel und Dienstleistungen','Strom']/df_EEB_Sektoren.loc['ENDENERGIEVERBRAUCH','Strom']


#%%


df_Last_22=df_Nettostromerzeugung_22['Last']