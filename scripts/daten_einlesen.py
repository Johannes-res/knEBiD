import pandas as pd




#%% Daten laden
#lädt die Zeitreihen der Nettostromerzeugung in Deutschland für das Jahr 2022
df_energy_charts_22 = pd.read_excel(r'data\energy-charts\energy-charts_Öffentliche_Nettostromerzeugung_in_Deutschland_2022.xlsx')
df_energy_charts_23 = pd.read_excel(r'data\energy-charts\energy-charts_Öffentliche_Nettostromerzeugung_in_Deutschland_2023.xlsx')

#lädt die Endenergiebedarfsdaten für das Jahr 2022
df_AGEB_22_org = pd.read_excel(r'data\Endenergiebedarf_AGEB\EBD22e.xlsx')
df_AGEB_23_org = pd.read_excel(r'data\Endenergiebedarf_AGEB\EBD23e.xlsx')

#lädt die Lastprofile Haushalte H25 und Gewerbe G25
df_Lastprofil_H25 = pd.read_excel(r'data\Kopie_von_Repräsentative_Profile_BDEW_H25_G25_L25_P25_S25_Veröffentlichung.xlsx', sheet_name="H25")
df_Lastprofil_G25 = pd.read_excel(r'data\Kopie_von_Repräsentative_Profile_BDEW_H25_G25_L25_P25_S25_Veröffentlichung.xlsx', sheet_name="G25")



#%% Zeitreihe aufbereiten

def prepare_energy_charts(df, year):

#Datum als Index setzen und in Datetime umwandeln sowie erste Zeile löschen

    df.set_index('Datum (UTC)', inplace=True)
    df.index = pd.to_datetime(df.index)
    df = df.drop(df.index[0])

# Erstellen Sie Start- und Enddatum für das ausgewählte Jahr
    start_date = f"{year}-01-01 00:00:00"
    end_date = f"{year}-12-31 23:45:00"

# Wählen Sie die Daten für das spezifische Jahr aus
    df_selected = df.loc[start_date:end_date]

    

    return df_selected

df_Nettostromerzeugung_22 = prepare_energy_charts(df_energy_charts_22, 2022)
df_Nettostromerzeugung_23 = prepare_energy_charts(df_energy_charts_23, 2023)

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

def update_dataframe(df, source_df, queries, column_name, kenngröße):
    """
    Erstellt oder aktualisiert einen DataFrame, indem neue Ergebnisse als Spalte hinzugefügt werden.

    :param df: Der bestehende DataFrame, der aktualisiert werden soll (oder None, falls er neu erstellt werden soll).
    :param source_df: Der DataFrame, aus dem die Werte geholt werden sollen.
    :param queries: Eine Liste von Tupeln (row_name, column_name), die die gewünschten Einträge spezifizieren.
    :param column_name: Der Name der neuen Spalte, die hinzugefügt werden soll.
    :param kenngröße: Der Name der Kenngröße, die in die neue Spalte eingefügt wird.
    :return: Der aktualisierte DataFrame.
    """
    # Funktion, die die Werte aus dem Quell-DataFrame extrahiert
    def get_values(source_df1, queries, kenngröße):
        source_df = source_df1.copy()
        source_df.set_index(source_df.columns[0], inplace=True)
        results = []
        for row_name, column_name in queries:
            try:
                value = source_df.loc[row_name, column_name]
                results.append({'Row': row_name, 'Column': column_name, 'Value': value})
            except KeyError:
                results.append({'Row': row_name, 'Column': column_name, 'Value': 'Fehler: Nicht gefunden'})
        results_df = pd.DataFrame(results).set_index('Row')
        results_df[kenngröße] = results_df['Value']
        results_df.drop(columns=['Column', 'Value'], inplace=True)
        return results_df

    # Hole die Werte basierend auf den Queries
    new_results = get_values(source_df, queries, kenngröße)

    # Falls der DataFrame noch nicht existiert, erstelle ihn
    if df is None or df.empty:
        df = new_results.rename(columns={kenngröße: column_name})
    else:
        # Füge die neue Spalte hinzu
        df[column_name] = new_results[kenngröße]

    return df

# In die Liste queries sind die gewünschten Sektoren einzutragen. 'Unnamed: 34' ist der Index der Spalte, die die Endenergiebedarfe enthält
kenngröße_AGEB = 'Endenergieverbrauch'
queries_AGEB = [
    ('ENDENERGIEVERBRAUCH', 'Unnamed: 34'),
    ('Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe', 'Unnamed: 34'),
    ('Verkehr insgesamt', 'Unnamed: 34'),
    ('Haushalte','Unnamed: 34'),
    ('Gewerbe, Handel, Dienstleistungen','Unnamed: 34'),
   
]
df_AGEB_22 = pd.DataFrame()
df_AGEB_23 = pd.DataFrame()

df_AGEB_22 = update_dataframe(df_AGEB_22,df_AGEB_22_org, queries_AGEB, kenngröße_AGEB, kenngröße_AGEB)
df_AGEB_23 = update_dataframe(df_AGEB_23,df_AGEB_23_org, queries_AGEB, kenngröße_AGEB, kenngröße_AGEB)



# df_EEB_Sektoren=pd.DataFrame()
# df_EEB_Sektoren['Summe'] = df_answer.set_index('Row')['Value']  # Setzt 'Row' als Index und übernimmt die Werte aus 'Value'


# In die Liste queries sind die gewünschten Sektoren einzutragen. 'Unnamed: 29' ist der Index der Spalte, die die Strombedarfe enthält
kenngröße_AGEB = 'Strom'
queries_AGEB = [
    ('ENDENERGIEVERBRAUCH', 'Unnamed: 29'),
    ('Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe', 'Unnamed: 29'),
    ('Verkehr insgesamt', 'Unnamed: 29'),
    ('Haushalte','Unnamed: 29'),
    ('Gewerbe, Handel, Dienstleistungen','Unnamed: 29'),
   
]

df_AGEB_22 = update_dataframe(df_AGEB_22,df_AGEB_22_org, queries_AGEB, kenngröße_AGEB, kenngröße_AGEB)
df_AGEB_23 = update_dataframe(df_AGEB_23,df_AGEB_23_org, queries_AGEB, kenngröße_AGEB, kenngröße_AGEB)

print('wegr')
# df_EEB_Sektoren['Strom'] = df_answer.set_index('Row')['Value']  # Ergänzt die Werte aus 'Value' passend zum Index