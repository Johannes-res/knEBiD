import pandas as pd

from daten_einlesen import df_Nettostromerzeugung_22
from daten_einlesen import df_Nettostromerzeugung_23
from daten_einlesen import df_Nettostromerzeugung_24


from daten_einlesen import df_inst_Strom_Leistung_22
from daten_einlesen import df_inst_Strom_Leistung_23
from daten_einlesen import df_inst_Strom_Leistung_24



def erzeuger_prognose(df, prognostizierte_leistungen):
    """das Maximum der einzelnen Erzeugertechnologien wird als installierte Leistung gesehen und darauf nomiert. Danach wird mit der Prognose der installierten Leistung multipliziert
    param df: DataFrame mit den Erzeugungsdaten
    param prognostizierte_leistungen: Dictionary mit den prognostizierten Leistungen für jede Technologie
    return: DataFrame mit den prognostizierten Erzeugungsdaten
    """
    # Kopiere den DataFrame, um die Originaldaten nicht zu verändern
    df_prog = df.copy()
    
    for technologie, leistungsprognose in prognostizierte_leistungen.items():
        if technologie in df_prog.columns:
            max_wert = df_prog[technologie].abs().max()  # Maximaler Betrag
            if max_wert == 0:
                raise ValueError(f"Division by zero encountered for technology '{technologie}' as the maximum absolute value is 0.")
            
            df_prog[technologie] = (df_prog[technologie] / max_wert) * leistungsprognose
    
    return df_prog

#Dictionary mit den prognostizierten Leistungen für jede Technologie
# Die Werte sind hier nur Platzhalter und sollten durch die tatsächlichen Prognosen ersetzt werden
# Beispiel: prognostizierte_leistungen = {'Laufwasser': 1, 'Biomasse': 1, ...}
# Hier wird angenommen, dass alle Technologien eine prognostizierte Leistung von 1 haben
# Dies sollte durch die tatsächlichen Werte ersetzt werden
prognostizierte_leistungen = {
                                'Laufwasser': 1, 
                                'Biomasse': 1, 
                                'Braunkohle': 1, 
                                'Steinkohle': 1,
                                'Öl': 1,
                                'Erdgas': 1,
                                'Geothermie': 1,
                                'Speicherwasser': 1,
                                'Pumpspeicher': 1, 
                                'Pumpspeicher Verbrauch': 1,
                                'Andere': 1, 
                                'Müll': 1, 
                                'Wind Offshore': 1, 
                                'Wind Onshore': 1, 
                                'Solar': 1, 
                                'Last': 1
}


df_prognose_22 = erzeuger_prognose(df_Nettostromerzeugung_22, prognostizierte_leistungen)


def inst_Leistung_vs_max_Werte(df_zeitreihe, df_inst_Leistung):
    """Vergleicht die maximalen Werte der Zeitreihe mit den installierten Leistungen.
    param df_zeitreihe: DataFrame mit den Zeitreihendaten
    param df_inst_Leistung: DataFrame mit den installierten Leistungen
    return: Dictionary mit den maximalen Werten und den installierten Leistungen
    """
    # Konvertiere die Spaltennamen in Kleinbuchstaben für den Vergleich
    vergleich = {}
    df_zeitreihe_lower = df_zeitreihe.rename(columns=str.lower)
    df_inst_Leistung_lower = df_inst_Leistung.rename(columns=str.lower)
    
    for spalte in df_zeitreihe_lower.columns:
        if spalte in df_inst_Leistung_lower.columns:
            max_wert = df_zeitreihe_lower[spalte].max()
            inst_leistung = df_inst_Leistung_lower[spalte].iloc[1] * 1000  # Annahme: Wert der installierten Leistung ist in der zweiten Zeile und auf MW
            vergleich[spalte] = {
                'Maximalwert': max_wert,
                'Installierte Leistung': inst_leistung,
                'Verhältnis': max_wert / inst_leistung if inst_leistung != 0 else None
            }
    return vergleich

vergleich_22 = inst_Leistung_vs_max_Werte(df_Nettostromerzeugung_22, df_inst_Strom_Leistung_22)
vergleich_23 = inst_Leistung_vs_max_Werte(df_Nettostromerzeugung_23, df_inst_Strom_Leistung_23)
vergleich_24 = inst_Leistung_vs_max_Werte(df_Nettostromerzeugung_24, df_inst_Strom_Leistung_24)


#pd.DataFrame.from_dict(vergleich_22, orient='index').to_excel(r'data\Ausgabe\vergleich_maxwert_zu_inst_Leistung_22.xlsx')
#pd.DataFrame(vergleich_23).to_excel(r'data\Ausgabe\vergleich_maxwert_zu_inst_Leistung_23.xlsx')
#pd.DataFrame(vergleich_24).to_excel(r'data\Ausgabe\vergleich_maxwert_zu_inst_Leistung_24.xlsx')


def volllaststunden_berechnen(df_zeitreihe, df_inst_Leistung):
    """Berechnet die Volllaststunden für jede Technologie in der Zeitreihe.
    param df_zeitreihe: DataFrame mit den Zeitreihendaten
    param df_inst_Leistung: DataFrame mit den installierten Leistungen
    return: DataFrame mit den Volllaststunden
    """
    # Konvertiere die Spaltennamen in Kleinbuchstaben für den Vergleich
    df_zeitreihe_lower = df_zeitreihe.rename(columns=str.lower)
    df_inst_Leistung_lower = df_inst_Leistung.rename(columns=str.lower)
    
    volllaststunden = {}
    
    for spalte in df_zeitreihe_lower.columns:
        if spalte in df_inst_Leistung_lower.columns:
            sum_wert = df_zeitreihe_lower[spalte].sum()/4                  # /4 Da Viertelstundenwerte
            inst_leistung = df_inst_Leistung_lower[spalte].iloc[1] * 1000  # Annahme: Wert der installierten Leistung ist in der zweiten Zeile und auf MW
            
            if inst_leistung != 0:
                volllaststunden[spalte] = sum_wert / inst_leistung  # Umrechnung auf Stunden pro Jahr
            else:
                volllaststunden[spalte] = None
    
    return pd.DataFrame.from_dict(volllaststunden, orient='index', columns=['Volllaststunden'])


vollaststunden_22 = volllaststunden_berechnen(df_Nettostromerzeugung_22, df_inst_Strom_Leistung_22)

#Kopie der Batteriespeicherstandsfunktion aus der Studienarbeit
def modellierungsfunktion_Batteriespeicher(df, max_battery_output, max_gas_output):
    
    # Konstanten
    BATTERY_CAPACITY = max_battery_output * 2 * 4 #mal4 da in MWviertelstunden
    BATTERY_MIN = 0.5 * 25 * max_battery_output*4/3600 #T_An=25s, mal4 wg viertelstunden, /3600 wg sekunden in stunden, 0.5 lt. formel

    # Initialisierung der neuen Spalten
    df['Speicherstand'] = np.nan
    df['Batterieleistung'] = 0
    df['modellierter Gaskraftwerkseinsatz'] = 0
    df['bestehende Differenz'] = 0
    df['A: Summe_Res-Last'] = df['Summe_RES'] - df['Last [MW]']

    # Setzen des ersten Eintrags für Speicherstand
    df.loc[df.index[0], 'Speicherstand'] = max(BATTERY_CAPACITY * 0.5, BATTERY_MIN)

   
    for i in range(1, len(df)):
        current_index = df.index[i]
        prev_index = df.index[i-1]
        
        last = df.loc[current_index, 'Last [MW]']
        summe_res = df.loc[current_index, 'Summe_RES']
        prev_speicherstand = df.loc[prev_index, 'Speicherstand']
        
        if last <= summe_res:
            # Überschuss: Lade die Batterie
            new_speicherstand = prev_speicherstand + (summe_res - last)
            df.loc[current_index, 'Speicherstand'] = min(new_speicherstand, BATTERY_CAPACITY)
            
         
            
        else:
            deficit = last - summe_res
            speicher = prev_speicherstand - BATTERY_MIN
            max_battery_use = min(speicher, max_battery_output)
            
            if max_battery_use >= deficit:
                df.loc[current_index, 'Batterieleistung'] = deficit
                df.loc[current_index, 'Speicherstand'] = prev_speicherstand - deficit
                
                

            else:
                df.loc[current_index, 'Batterieleistung'] = max_battery_use
                df.loc[current_index, 'Speicherstand'] = prev_speicherstand - max_battery_use
                
                remaining_deficit = deficit - max_battery_use
                gas_use = min(max_gas_output, remaining_deficit)
                df.loc[current_index, 'modellierter Gaskraftwerkseinsatz'] = gas_use
                
                df.loc[current_index, 'bestehende Differenz'] = remaining_deficit - gas_use

    # Sicherstellen, dass Speicherstand nicht unter BATTERY_MIN fällt und die maximale Kapazität nicht überschreitet
    df['Speicherstand'] = df['Speicherstand'].clip(lower=BATTERY_MIN, upper=BATTERY_CAPACITY)
    
    return df


print('Ende des Erzeuger Skripts')