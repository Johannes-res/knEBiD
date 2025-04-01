import pandas as pd
import holidays


#%% Daten laden
#lädt die Zeitreihen der Nettostromerzeugung in Deutschland für das Jahr 2022
df_energy_charts = pd.read_excel(r'data\energy-charts\energy-charts_Öffentliche_Nettostromerzeugung_in_Deutschland_2022.xlsx')

#lädt die Endenergiebedarfsdaten für das Jahr 2022
df_AGEB = pd.read_excel(r'data\Endenergiebedarf_AGEB\EBD22e.xlsx')

#lädt die Lastprofile Haushalte H25 und Gewerbe G25
df_Lastprofil_H25 = pd.read_excel(r'data\Kopie_von_Repräsentative_Profile_BDEW_H25_G25_L25_P25_S25_Veröffentlichung.xlsx', sheet_name="H25")
df_Lastprofil_G25 = pd.read_excel(r'data\Kopie_von_Repräsentative_Profile_BDEW_H25_G25_L25_P25_S25_Veröffentlichung.xlsx', sheet_name="G25")


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

#%% Lastprofile aufbereiten
def prepare_lastprofile(df):
    """
    Bereitet einen DataFrame mit Lastprofilen vor:
    - Entfernt die erste Zeile.
    - Kürzt die Zeitspalte auf die ersten 5 Zeichen, wandelt sie in datetime um und setzt sie als Index.
    - Entfernt unnötige Spalten.
    - Extrahiert Monatszahlen aus einer Zeile und setzt sie als Spaltenüberschriften.
    - Kombiniert die ersten zwei Zeilen zu neuen Spaltenüberschriften.
    - Entfernt die ersten zwei Zeilen aus dem DataFrame.

    Parameter:
        df (pd.DataFrame): Der zu bearbeitende DataFrame.

    Rückgabe:
        pd.DataFrame: Der aufbereitete DataFrame.
    """
    # Entferne die erste Zeile
    df.drop(index=0, inplace=True)

    # Extrahiere Monatszahlen aus der ersten Zeile
    df.iloc[0] = pd.to_datetime(df.iloc[0]).dt.strftime('%m')  # Konvertiere in Monatszahlen
    
    # Kombiniere die ersten zwei Zeilen zu neuen Spaltenüberschriften
    new_columns = df.iloc[:2].apply(lambda x: '_'.join(x.dropna().astype(str)), axis=0)
    
    # Setze die neuen Spaltenüberschriften
    df.columns = new_columns
    
    # Entferne die ersten zwei Zeilen aus dem DataFrame
    df = df.iloc[2:].reset_index(drop=True)

    # Kürze die Zeitspalte auf die ersten 5 Zeichen, wandle sie in datetime um und setze sie als Index
    df.iloc[:, 1] = df.iloc[:, 1].astype(str)  # Ensure the column contains strings
    df.index = pd.to_datetime(df.iloc[:, 1].str[:5], format='%H:%M').dt.time
    df.drop(df.columns[1], axis=1, inplace=True)  # Entferne die ursprüngliche Zeitspalte
    df.drop(df.columns[0], axis=1, inplace=True)
    
    return df

df_Lastprofil_G25 = prepare_lastprofile(df_Lastprofil_G25)
df_Lastprofil_H25 = prepare_lastprofile(df_Lastprofil_H25)

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
    ('Haushalte','Unnamed: 34'),
    ('Gewerbe, Handel, Dienstleistungen','Unnamed: 34'),
   
]

df_answer = get_values_from_dataframe(df_AGEB, queries)


df_EEB_Sektoren=pd.DataFrame()
df_EEB_Sektoren['Summe'] = df_answer.set_index('Row')['Value']  # Setzt 'Row' als Index und übernimmt die Werte aus 'Value'


# Stromverbrauch
queries = [
    ('ENDENERGIEVERBRAUCH', 'Unnamed: 29'),
    ('Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe', 'Unnamed: 29'),
    ('Verkehr insgesamt', 'Unnamed: 29'),
    ('Haushalte','Unnamed: 29'),
    ('Gewerbe, Handel, Dienstleistungen','Unnamed: 29'),
   
]

df_answer = get_values_from_dataframe(df_AGEB, queries)
df_EEB_Sektoren['Strom'] = df_answer.set_index('Row')['Value']  # Ergänzt die Werte aus 'Value' passend zum Index


#Anteile der einzelnen Sektoren am Gesamtverbrauch berechnen

df_EEB_Sektoren.loc['Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe','Anteil_Summe']=df_EEB_Sektoren.loc['Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe','Summe']/df_EEB_Sektoren.loc['ENDENERGIEVERBRAUCH','Summe']
df_EEB_Sektoren.loc['Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe','Anteil_Strom']=df_EEB_Sektoren.loc['Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe','Strom']/df_EEB_Sektoren.loc['ENDENERGIEVERBRAUCH','Strom']

df_EEB_Sektoren.loc['Verkehr insgesamt','Anteil_Summe']=df_EEB_Sektoren.loc['Verkehr insgesamt','Summe']/df_EEB_Sektoren.loc['ENDENERGIEVERBRAUCH','Summe']
df_EEB_Sektoren.loc['Verkehr insgesamt','Anteil_Strom']=df_EEB_Sektoren.loc['Verkehr insgesamt','Strom']/df_EEB_Sektoren.loc['ENDENERGIEVERBRAUCH','Strom']

df_EEB_Sektoren.loc['Haushalte','Anteil_Summe']=df_EEB_Sektoren.loc['Haushalte','Summe']/df_EEB_Sektoren.loc['ENDENERGIEVERBRAUCH','Summe']
df_EEB_Sektoren.loc['Haushalte','Anteil_Strom']=df_EEB_Sektoren.loc['Haushalte','Strom']/df_EEB_Sektoren.loc['ENDENERGIEVERBRAUCH','Strom']

df_EEB_Sektoren.loc['Gewerbe, Handel, Dienstleistungen','Anteil_Summe']=df_EEB_Sektoren.loc['Gewerbe, Handel, Dienstleistungen','Summe']/df_EEB_Sektoren.loc['ENDENERGIEVERBRAUCH','Summe']
df_EEB_Sektoren.loc['Gewerbe, Handel, Dienstleistungen','Anteil_Strom']=df_EEB_Sektoren.loc['Gewerbe, Handel, Dienstleistungen','Strom']/df_EEB_Sektoren.loc['ENDENERGIEVERBRAUCH','Strom']


#Hier wird die Gesamtenergie für 2022 berechnet

df_Last_22 = pd.DataFrame()
df_Last_22 ['Last [MW]']=df_Nettostromerzeugung_22['Last']

df_Last_22 = df_Last_22.astype(float)  # Konvertiert die Werte in float, falls sie als Strings gespeichert sind
df_Last_22 = df_Last_22.dropna()  # Entfernt NaN-Werte

df_Last_22['Energie [MWh]'] = df_Last_22['Last [MW]']/4

var_Summe_Last_22 = df_Last_22['Energie [MWh]'].sum()  # Berechnet die Summe der Energie

var_Summe_Last_22_TWh = var_Summe_Last_22 / 1000000  # Umwandlung in TWh
var_Summe_Last_22_TWh = round(var_Summe_Last_22_TWh, 2)  # Rundet auf 2 Dezimalstellen



#Hier wird die Gesamtenergie auf die Sektoren aufgeteilt

df_EEB_Sektoren ['Energiemenge_anteilig [MWh]'] = df_EEB_Sektoren['Anteil_Strom']*var_Summe_Last_22

print('Die Energiemenge für 2022 beträgt:', var_Summe_Last_22_TWh, 'TWh')



#%% Funktion, welche einem Dataframe mit datetime-Index Tagesnamen (Werktag/Feiertag/Samstag) hinzufügt und den Monat angibt

def add_day_type(df):
    """
    Fügt dem DataFrame eine Spalte hinzu, die den Typ des Tages angibt (Werktag/Sonntag/Samstag) und identifiziert, ob es sich um Sommer/Winter/Übergangszeit handelt.
    :param df: DataFrame mit einem Datetime-Index."""

    # Erstelle eine Kopie des DataFrames, um die Originaldaten nicht zu verändern
    df_copy = df.copy()

    # Feiertage für Deutschland laden
    german_holidays = holidays.Germany()

    # Füge eine neue Spalte 'day_type' hinzu und initialisiere sie mit 'Werktag'
    df_copy['Tagestyp'] = 'WT'  # Standardmäßig Werktag

    # Setze den Typ des Tages auf 'Sonntag' oder 'Samstag' basierend auf dem Wochentag
    df_copy.loc[df_copy.index.weekday == 6, 'Tagestyp'] = 'FT'  # Sonntag
    df_copy.loc[df_copy.index.weekday == 5, 'Tagestyp'] = 'SA'  # Samstag

    # # Setze den Typ des Tages auf 'Feiertag' oder 'Werktag', falls noch nicht gesetzt
    # df_copy['Tagestyp'] = df_copy['Tagestyp'].fillna(
    #     df_copy.index.map(lambda date: "Feiertag" if date in german_holidays else "Werktag")
    # )


    # Füge eine neue Spalte 'Monat' hinzu, die den Monat des Datetime-Index enthält
    df_copy['Monat'] = df_copy.index.month
    df_copy['Monat'] = df_copy['Monat'].astype(str)  # Konvertiere den Monatswert in einen String
    df_copy['Monat'] = df_copy['Monat'].str.zfill(2)  # Stelle sicher, dass der Monatswert immer 2-stellig ist

    # Füge eine neue Spalte 'Monats_Tageskennung' hinzu, die die Spalte 'Tagestyp ' und 'Monat' kombiniert
    df_copy['Monats_Tageskennung'] = df_copy['Monat'].astype(str) + '_' + df_copy['Tagestyp'].astype(str)

    


   

    return df_copy

df_Last_22 = add_day_type(df_Last_22)








#%% dem Lastgang die Sektorspezifischen Lastprofile hinzufügen

def ergänze_lastprofile(df_last, df_g25, df_h25):
    """
    Ergänzt den DataFrame df_last mit den Spalten G25 und H25, basierend auf den Werten
    aus df_g25 und df_h25 entsprechend der Spalte Monats_Tageskennung und den Uhrzeiten.

    :param df_last: Der DataFrame, der ergänzt werden soll (z. B. df_Last_22).
    :param df_g25: Der DataFrame mit den Lastprofilwerten für G25.
    :param df_h25: Der DataFrame mit den Lastprofilwerten für H25.
    :return: Der ergänzte DataFrame.
    """
    # Stelle sicher, dass die Indizes von df_g25 und df_h25 datetime.time-Objekte sind
    df_g25.index = pd.to_datetime(df_g25.index, format='%H:%M:%S').time
    df_h25.index = pd.to_datetime(df_h25.index, format='%H:%M:%S').time

    # Initialisiere die neuen Spalten G25 und H25
    df_last['G25'] = df_last.apply(
        lambda row: df_g25.loc[row.name.time(), row['Monats_Tageskennung']], axis=1
    )
    df_last['H25'] = df_last.apply(
        lambda row: df_h25.loc[row.name.time(), row['Monats_Tageskennung']], axis=1
    )
    return df_last

df_Last_22 = ergänze_lastprofile(df_Last_22, df_Lastprofil_G25, df_Lastprofil_H25)

print(df_Last_22.head())

#%%