#%%Pakete und Module importieren

import pandas as pd
import holidays
import numpy as np

from daten_einlesen import df_AGEB_22_org
from daten_einlesen import df_AGEB_23_org
from daten_einlesen import df_AGEB_24_org
#%% Tabellenstruktur anpassen
# Umbenennen der Spaltennamen 
def rename_columns(df, column_mapping):
    """
    Benennt die Spalten eines DataFrames um.

    :param df: Der DataFrame, dessen Spalten umbenannt werden sollen.
    :param column_mapping: Ein Dictionary, das die alten Spaltennamen den neuen Spaltennamen zuordnet.
    :return: Der DataFrame mit umbenannten Spalten.
    """
    df.rename(columns=column_mapping, inplace=True)
    return df

column_mapping = {
    'Steinkohlen': 'Steinkohle',
    'Unnamed: 3': 'SteinBriketts',
    'Unnamed: 4': 'SteinKoks',
    'Unnamed: 5': 'Andere Steinkohlenprodukte',
    'Braunkohlen': 'Braunkohle',
    'Unnamed: 7': 'BraunBriketts',
    'Unnamed: 8': 'Andere Braunkohlenprodukte',
    'Unnamed: 9': 'Hartbraunkohle',
    'Mineralöle': 'Erdöl (roh)',
    'Unnamed: 11': 'Ottokraftstoff',
    'Unnamed: 12': 'Rohbenzin',
    'Unnamed: 13': 'Flugturbinenenkraftstoff',
    'Unnamed: 14': 'Dieselkraftstoff',
    'Unnamed: 15': 'Heizöl leicht',
    'Unnamed: 16': 'Heizöl schwer',
    'Unnamed: 17': 'Petrolkoks',
    'Unnamed: 18': 'Flüssigas',
    'Unnamed: 19': 'Raffeneriegas',
    'Unnamed: 20': 'Andere Mineralölprodukte',
    'Unnamed: 21': 'Kokereigas, Stadtgas',
    'Unnamed: 22': 'Gichtgas, Konvertergas',
    'Unnamed: 23': 'Naturgase, Erdgas, Erdölgas',
    'Unnamed: 24': 'Grubengas',
    'Erneuerbare Energien': 'Wasserkraft, Windenergie, Photovoltaik',
    'Unnamed: 26': 'Biomasse, erneuerbare Abfälle',
    'Unnamed: 27': 'Solarthermie, Geothermie, Umweltwärme',
    'Elektrischer Strom und sonstige Energieträger': 'Fossile Abfälle, Sonstige',
    'Unnamed: 29': 'Strom',
    'Unnamed: 30': 'Kernenergie',
    'Unnamed: 31': 'Fernwärme',
    'Energieträger insgesamt': 'Primärenergieträger',
    'Unnamed: 33': 'Sekundärenergieträger',
    'Unnamed: 34': 'Summe',
}

df_AGEB_benannt = rename_columns(df_AGEB_22_org, column_mapping)

#Werte zu integers umwandeln. Die ersten 2 Zeilen sind Header und die ersten 6 Spalten sind keine Zahlen.
df_AGEB_benannt.iloc[6:, 2:] = df_AGEB_benannt.iloc[6:, 2:].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
#gesamte Werte von TJ auf GWh umrechnen
df_AGEB_benannt.iloc[6:, 2:] = df_AGEB_benannt.iloc[6:, 2:] / 3.6

#%% Funktion zum Extrahieren der Werte für einen bestimmten Sektor und Zuordnung zu künftigen Energieträgern
def extrahieren_und_zuordnen(df, sektor_name, energietraeger_AGEB):
    """
    Diese Funktion extrahiert die Werte aus der Tabelle der AGEB für einen bestimmten Sektor (oder Teilsektor) aus dem DataFrame und ordnet sie den zukünftigen Energieträgern zu.
    :param df: Der DataFrame mit der Energiebilanz der AGEB.
    :param sektor_name: Der Name des Sektors, dessen Werte extrahiert werden sollen. Alternativ kann auch jede andere Zeile angegeben werden.
    :param energietraeger_AGEB: Eine Liste von Tupeln, die die alten Energieträger, neuen Energieträger und den Faktor zuordnen.
    
    :return: Ein neuer DataFrame der für den ausgewählten Sektor (bzw. Zeile in der Tabelle) die Energieträger auflistet und den neuen zuordnet.
    """
    # Zeilen mit dem gesuchten Sektor finden
    filtered = df[df.iloc[:, 0] == sektor_name]
    # Ergebnis-Liste für DataFrames
    result_rows = []
    # Für jede gefundene Zeile:
    for _, row in filtered.iterrows():
        for col_name, new_col, faktor in energietraeger_AGEB:
            row_dict = {'Energietraeger': col_name}
            # Alle neuen Spalten initialisieren mit None
            for _, nc, _ in energietraeger_AGEB:
                row_dict[nc] = None
            # Wert eintragen, falls Spalte existiert
            if col_name in df.columns:
                if faktor is not None:
                    # Wenn ein Faktor angegeben ist, multiplizieren
                    row_dict[new_col] = row[col_name] * faktor
                else:
                    # Wenn kein Faktor angegeben ist, einfach den Wert übernehmen
                    row_dict[new_col] = row[col_name]
            # Füge die Zeile dem Ergebnis hinzu
            result_rows.append(row_dict)
    # DataFrame aus allen Zeilen bauen
    if result_rows:
        result = pd.DataFrame(result_rows)
    else:
        raise ValueError("No matching rows found or no valid data to process.")
    # Doppelt vorhandene Zeilen zusammenführen
    energietraeger_order = [et[0] for et in energietraeger_AGEB]  # Originalreihenfolge speichern
    result = result.groupby('Energietraeger', as_index=False).first()
    
    # Sortierung nach ursprünglicher Reihenfolge
    result['order'] = result['Energietraeger'].apply(
        lambda x: energietraeger_order.index(x) if x in energietraeger_order else len(energietraeger_order)
    )
    result = result.sort_values('order').drop(columns='order').reset_index(drop=True)
    # Erstelle eine weitere Zeile, welche die Summe der Spalten enthält
    sum_row = result.iloc[:, 1:].sum(numeric_only=True)/1000
    sum_row['Energietraeger'] = 'Summe pro Spalte [TWh]'
    result = pd.concat([result, pd.DataFrame([sum_row])], ignore_index=True)

    return result


#Hier werden die Variablen für die Funktion 'extrahieren und zuordnen' definiert. mehr Infos in der Funktion selbst

sektor_verkehr = 'Verkehr insgesamt'
sektor_gebäude = 'Haushalte, Gewerbe, Handel und Dienstleistungen'
sektor_industrie = 'Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe'

#Hier wurde initial alle Energieträger auf 'Strom' gesetzt. Gasförmige und Biomasse Energieträger wurden auf 'Wasserstoff' gesetzt.
# Diese Zuordnung ist nicht final und muss noch ggf. angepasst werden. Die mit # angegebenen Energieträger waren in der AGEB Tabelle 2022 nicht 0.
energietraeger_verkehr = [

    ('Steinkohle',                                              'Strom', None),
    ('SteinBriketts',                                           'Strom', None),
    ('SteinKoks',                                               'Strom', None),
    ('Andere Steinkohlenprodukte',                              'Strom', None),
    ('Braunkohle',                                              'Strom', None),
    ('BraunBriketts',                                           'Strom', None),
    ('Andere Braunkohlenprodukte',                              'Strom', None),
    ('Hartbraunkohle',                                          'Strom', None),
    ('Erdöl (roh)',                                             'Strom', None),
    ('Ottokraftstoff',                                          'Strom',0.3),                        #
    ('Rohbenzin',                                               'Strom', None),
    ('Flugturbinenenkraftstoff',                                'E-Fules',1.5),            #
    ('Dieselkraftstoff',                                        'Strom',0.3),                      #
    ('Heizöl leicht',                                           'Strom', None),
    ('Heizöl schwer',                                           'Strom', None),
    ('Petrolkoks',                                              'Strom', None),
    ('Flüssigas',                                               'Wasserstoff',1.2),                       #                 
    ('Raffeneriegas',                                           'Strom', None),
    ('Andere Mineralölprodukte',                                'Strom', None),
    ('Kokereigas, Stadtgas',                                    'Strom', None),
    ('Gichtgas, Konvertergas',                                  'Strom', None),
    ('Naturgase, Erdgas, Erdölgas',                             'Wasserstoff',1.2),     #
    ('Grubengas',                                               'Strom', None),
    ('Wasserkraft, Windenergie, Photovoltaik',                  'Strom', None),
    ('Biomasse, erneuerbare Abfälle',                           'Biogas', None),  #
    ('Solarthermie, Geothermie, Umweltwärme',                   'Thermie', None),
    ('Fossile Abfälle, Sonstige',                               'Strom', None),
    ('Strom',                                                   'Strom', None),                                 #
    ('Kernenergie',                                             'Strom', None),
    ('Fernwärme',                                               'Strom', None),
   # ('Primärenergieträger',                                     'Primärenergieträger', None),
   # ('Sekundärenergieträger',                                   'Sekundärenergieträger', None),
    ('Summe',                                                   'Summe_Verkehr', 0.5),                        # Nach Studienarbeit reduziert sich der Verbrauch auf die Hälfte bis 2045. Dies liegt an der Veränderung der Mobilität, aber primär auch an der Änderung der Energieträger.
]

energietraeger_gebäude = [
    ('Steinkohle',                              'Wasserstoff', 1),#
    ('SteinBriketts',                           'Wasserstoff', 1),#
    ('SteinKoks',                               'Strom', None),
    ('Andere Steinkohlenprodukte',              'Strom', None),
    ('Braunkohle',                              'Strom', None),
    ('BraunBriketts',                           'Wasserstoff', None),#
    ('Andere Braunkohlenprodukte',              'Strom', None),
    ('Hartbraunkohle',                          'Strom', None),
    ('Erdöl (roh)',                             'Strom', None),
    ('Ottokraftstoff',                          'Wasserstoff', None),#
    ('Rohbenzin',                               'Strom', None),
    ('Flugturbinenenkraftstoff',                'E-Fules', None),#
    ('Dieselkraftstoff',                        'Wasserstoff', None),#
    ('Heizöl leicht',                           'Strom', 0.33),#
    ('Heizöl schwer',                           'Strom', None),
    ('Petrolkoks',                              'Strom', None),
    ('Flüssigas',                               'Wasserstoff', None),#
    ('Raffeneriegas',                           'Strom', None),
    ('Andere Mineralölprodukte',                'Wasserstoff', None),#
    ('Kokereigas, Stadtgas',                    'Strom', None),
    ('Gichtgas, Konvertergas',                  'Strom', None),
    ('Naturgase, Erdgas, Erdölgas',             'Strom', 0.5),#
    #('Naturgase, Erdgas, Erdölgas',             'Wasserstoff', 1),# es Kann auch durch doppelnennung eine Aufteilung innerhalb des Energieträges erreicht werden. Danach müsste
    ('Grubengas',                               'Strom', None),
    ('Wasserkraft, Windenergie, Photovoltaik',  'Strom', None),
    ('Biomasse, erneuerbare Abfälle',           'Biomasse', None),#
    ('Solarthermie, Geothermie, Umweltwärme',   'Thermie', None),
    ('Fossile Abfälle, Sonstige',               'Strom', None),
    ('Strom',                                   'Strom', None),
    ('Kernenergie',                             'Strom', None),
    ('Fernwärme',                               'Strom', 0.5),
    #('Primärenergieträger',                     'Strom', None),
    #('Sekundärenergieträger',                   'Strom', None),
    ('Summe',                                   'Summe_Gebäude', None ),# Nach Studienarbeit reduziert sich der EEB um 34% bis 2045. Dies liegt jedoch vorallem an der gebäudetechnischen Sanierung und nicht an der Änderung der Energieträger. 
]

energietraeger_industrie = [
    ('Steinkohle',                              'Wasserstoff', 1),#
    ('SteinBriketts',                           'Wasserstoff', None),
    ('SteinKoks',                               'Wasserstoff', 1),#
    ('Andere Steinkohlenprodukte',              'Strom', None),
    ('Braunkohle',                              'Strom', None),#
    ('BraunBriketts',                           'Wasserstoff', None),#
    ('Andere Braunkohlenprodukte',              'Strom', None),#
    ('Hartbraunkohle',                          'Strom', None),
    ('Erdöl (roh)',                             'Strom', None),
    ('Ottokraftstoff',                          'Wasserstoff', None),
    ('Rohbenzin',                               'Strom', None),
    ('Flugturbinenenkraftstoff',                'E-Fules', None),
    ('Dieselkraftstoff',                        'Wasserstoff', None),#
    ('Heizöl leicht',                           'Strom', 0.33),#
    ('Heizöl schwer',                           'Strom', 0.5),#
    ('Petrolkoks',                              'Strom', None),#
    ('Flüssigas',                               'Wasserstoff', None),#
    ('Raffeneriegas',                           'Strom', None),#
    ('Andere Mineralölprodukte',                'Wasserstoff', None),#
    ('Kokereigas, Stadtgas',                    'Strom', None),
    ('Gichtgas, Konvertergas',                  'Wasserstoff', None),
    ('Naturgase, Erdgas, Erdölgas',             'Strom', 0.5),#
    #('Naturgase, Erdgas, Erdölgas',             'Wasserstoff', 1),# es Kann auch durch doppelnennung eine Aufteilung innerhalb des Energieträges erreicht werden. Danach müsste
    ('Grubengas',                               'Strom', None),
    ('Wasserkraft, Windenergie, Photovoltaik',  'Strom', None),
    ('Biomasse, erneuerbare Abfälle',           'Biomasse', None),#
    ('Solarthermie, Geothermie, Umweltwärme',   'Thermie', None),
    ('Fossile Abfälle, Sonstige',               'Strom', None),
    ('Strom',                                   'Strom', None),
    ('Kernenergie',                             'Strom', None),
    ('Fernwärme',                               'Strom', None),
   # ('Primärenergieträger',                     'Strom', None),
   # ('Sekundärenergieträger',                   'Strom', None),
    ('Summe',                                   'Summe_Gebäude', 0.82 ),# Nach Studienarbeit. Nachvollziehbar durch nutzung der Umweltwärme, welche hier nicht mit umgelagert wird.
]


# Funktion aufrufen
result_verkehr = extrahieren_und_zuordnen(df_AGEB_benannt, sektor_verkehr, energietraeger_verkehr)
result_gebäude = extrahieren_und_zuordnen(df_AGEB_benannt, sektor_gebäude, energietraeger_gebäude)
result_industrie = extrahieren_und_zuordnen(df_AGEB_benannt, sektor_industrie, energietraeger_industrie)

# hier werden die Teilergebnisse aus den Sektoren zusammengefasst und in eine Tabelle geschrieben.
#dies kann die Grundlage für die EEB der Zeitreihen sein.
übersicht_gesamt = pd.DataFrame()
übersicht_gesamt['Sektor'] = ['Gebäude','Verkehr','Industrie']
übersicht_gesamt['Strom'] = result_gebäude.loc[31,'Strom'],result_verkehr.loc[31,'Strom'],result_industrie.loc[31,'Strom']
übersicht_gesamt['Wasserstoff'] = result_gebäude.loc[31,'Wasserstoff'],result_verkehr.loc[31,'Wasserstoff'],result_industrie.loc[31,'Wasserstoff']
übersicht_gesamt['Biomasse'] = result_gebäude.loc[31,'Biomasse'],result_verkehr.loc[31,'Biogas'],result_industrie.loc[31,'Biomasse']
übersicht_gesamt['E-Fuels'] = result_gebäude.loc[31,'E-Fules'],result_verkehr.loc[31,'E-Fules'],result_industrie.loc[31,'E-Fules']
übersicht_gesamt['Thermie'] = result_gebäude.loc[31,'Thermie'],result_verkehr.loc[31,'Thermie'],result_industrie.loc[31,'Thermie']
übersicht_gesamt['Summe_Sektor'] = übersicht_gesamt.iloc[:, 1:].sum(axis=1)
# Eine zusätzliche Zeile hinzufügen, die die Summe der Spalten enthält
übersicht_gesamt.loc['Summe_Energieträger'] = übersicht_gesamt.sum(numeric_only=True)


übersicht_gesamt.to_excel(r'data\Ausgabe\Energieträger_Übersicht_kn_heute.xlsx')

print("Ende des bedarf_klimaneutral_heute Skripts")
# %%
