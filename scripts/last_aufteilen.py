#%%Pakete und Module importieren

import pandas as pd
import holidays
import numpy as np

from daten_einlesen import df_Nettostromerzeugung_22
from daten_einlesen import df_Nettostromerzeugung_23
from daten_einlesen import df_AGEB_22
from daten_einlesen import df_AGEB_23
from daten_einlesen import df_Lastprofil_H25
from daten_einlesen import df_Lastprofil_G25

#%% Funktionen definieren
def verbrauchsübersicht_erstellen(df_Nettostromerzeugung, df_AGEB):

    df_übersicht = pd.DataFrame()
    df_übersicht['Last [MW]'] = df_Nettostromerzeugung['Last']
    df_übersicht['Energie [MWh]'] = df_übersicht['Last [MW]'] / 4

    var_Summe_Last = df_übersicht['Energie [MWh]'].sum()  # Berechnet die Summe der Energie

    df_AGEB.loc[:,'Anteil_Strom']=df_AGEB.loc[:,'Strom']/df_AGEB.loc['ENDENERGIEVERBRAUCH','Strom']
    df_AGEB ['Stromenergiemenge_anteilig [MWh]'] = df_AGEB['Anteil_Strom']*var_Summe_Last

    

    return df_übersicht

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

def saisonschwankungen_modellieren(t):
    """
    Simuliert saisonale Schwankungen im Stromverbrauch (x = Tag 1-365)
    Gibt relativen Verbrauchsfaktor zurück (1.0 = Durchschnitt)
    """
    # Jahreszeitliche Grundschwingung (Hauptmaximum im Winter)
    saison = 0.01 * np.cos(2*np.pi*(t - 15)/365)
    
    # Weihnachtseffekt (Spitze im Dezember)
    weihnachten = 0.1 * np.exp(-((t - 355)/10)**2)
    
    # Sommerdip mit leichtem Anstieg durch Kühlung
    sommer = -0.015 * np.exp(-((t - 200)/60)**2)
    
    # Zufällige tägliche Schwankungen (Rauschen)
    # rauschen = 0.05 * np.random.normal()
    
    return 1.0 + saison #+ weihnachten + sommer + rauschen
 


def modelliere_Sektorenzeitreihen(df_last, ESB_Industrie, ESB_GHD, ESB_Haushalte, ESB_Verkehr,ESB_E_Mob, ESB_WP, faktor_G25, faktor_H25):


    """
    #Als Übergabe muss ein Zeitreihen-Dataframe mit den Lastprofilzeitreihen übergeben werden (stammt von df_Last_22_mit_Profilen)
    #Es müssen die Jahresstrommengen für die einzelnen Sektoren übergeben werden (stammt von df_EEB_Sektoren)
    
    
    Hier werden die Lastprofile mit den Stromverbräuchen der Sektoren multipliziert
    Die Lastprofile sind auf 1Mio. kWH normiert, weswegen durch 1000 geteilt werden muss um auf 1MWh zu kommen
    Für die Flexibilität wird die Rechnung mit dem gleichverteilenden Anteil erweitert """

    t= df_last.index.dayofyear
    #Die Lastprofile sind auf 1Mio. kWH normiert, weswegen durch 1000 geteilt werden muss um auf 1MWh zu kommen. Dann wird mit dem Endstrombedarf des Sektors multipliziert
    # Die Viertelstundenwerte sind in kWh angegeben, daher wird durch 10e3 geteilt, um auf MWh zu kommen
    #Energiemenge des Sektors=      ((((Lastprofil/1000)*Endstrombedarf_Sektor)/1000)*Wichtung_des_Profils + (ESB/len(df_last))*(1-faktor))*saisonschwankungen_modellieren(t)
    df_last['Industrie'] =          ((((df_last['G25']/1e3) * ESB_Industrie)/1e3)    * faktor_G25 + (ESB_Industrie/len(df_last)) * (1-faktor_G25)) *saisonschwankungen_modellieren(t)
    df_last['GHD'] =                ((((df_last['G25']/1e3) * ESB_GHD)/1e3)          * faktor_G25 + (ESB_GHD/len(df_last))       * (1-faktor_G25)) *saisonschwankungen_modellieren(t)
    df_last['Haushalte_stat'] =     ((((df_last['H25']/1e3) * ESB_Haushalte)/1e3)    * faktor_H25 + (ESB_Haushalte/len(df_last)) * (1-faktor_H25)) *saisonschwankungen_modellieren(t)
    # df_last['Haushalte_dyn'] =    ((df_last['H25'] / 1e3) * ESB_Haushalte) * (-3.92e-10 * t**4 + 3.2e-7 * t**3 - 7.02e-5 * t + 2.1e-3*t + 1.24)/1e3 #FEHLER!!!Exponentiell ansteigend!
    df_last['Verkehr'] =            (ESB_Verkehr / len(df_last)) 
    df_last['E_Mob'] =              (ESB_E_Mob/len(df_last))                                                                                        *saisonschwankungen_modellieren(t)
    df_last['WP'] =                 (ESB_WP/len(df_last))                                                                                           *saisonschwankungen_modellieren(t)

    df_last['Summe_Sektoren_modelliert'] = (df_last['Industrie'] + df_last['GHD'] + df_last['Haushalte_stat']+df_last['Verkehr'])

    ##Hier wird der Anteil der einzelnen Sektoren, dynamisiert durch die Standardlastprofile, an der Gesamtlast für jede Viertelstunde berechnet
    df_last['Anteil_Industrie'] = df_last['Industrie'] / df_last['Summe_Sektoren_modelliert']
    df_last['Anteil_GHD'] = df_last['GHD'] / df_last['Summe_Sektoren_modelliert']
    df_last['Anteil_Haushalte_stat'] = df_last['Haushalte_stat'] / df_last['Summe_Sektoren_modelliert']
    # df_last['Anteil_Haushalte_dyn'] = df_last['Haushalte_dyn'] / df_last['Summe_Sektoren_modelliert']
    df_last['Anteil_Verkehr'] = df_last['Verkehr'] / df_last['Summe_Sektoren_modelliert']


    return df_last



#%% Variablen definieren
# Hier können Sie die Variablen definieren, die Sie in den Funktionen verwenden möchten.
ESB_Industrie_45 =          1
ESB_Haushalte_45 =          1
ESB_GHD_45 =                1
ESB_Verkehr_45 =            1
ESB_E_Mob_45 =              1
ESB_WP_45 =                 1




#%% Funktionen ausführen
df_übersicht_22 = verbrauchsübersicht_erstellen(df_Nettostromerzeugung_22,df_AGEB_22)
df_übersicht_23 = verbrauchsübersicht_erstellen(df_Nettostromerzeugung_23,df_AGEB_23)

df_übersicht_22 = add_day_type(df_übersicht_22)
df_übersicht_23 = add_day_type(df_übersicht_23)

df_übersicht_22 = ergänze_lastprofile(df_übersicht_22, df_Lastprofil_G25, df_Lastprofil_H25)
df_übersicht_23 = ergänze_lastprofile(df_übersicht_23, df_Lastprofil_G25, df_Lastprofil_H25)

df_übersicht_22 = modelliere_Sektorenzeitreihen(df_übersicht_22,ESB_Industrie_45,ESB_GHD_45, ESB_Haushalte_45, ESB_Verkehr_45, ESB_E_Mob_45, ESB_WP_45, 0.5, 0.5)
df_übersicht_23 = modelliere_Sektorenzeitreihen(df_übersicht_23,  df_AGEB_23.loc['Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe','Stromenergiemenge_anteilig [MWh]'], df_AGEB_23.loc['Gewerbe, Handel, Dienstleistungen','Stromenergiemenge_anteilig [MWh]'], df_AGEB_23.loc['Haushalte','Stromenergiemenge_anteilig [MWh]'], df_AGEB_23.loc['Verkehr insgesamt','Stromenergiemenge_anteilig [MWh]'], 0.5, 0.5)

df_übersicht_22.drop(columns=['Tagestyp','Monat','G25','Industrie','GHD','Verkehr','Haushalte_stat','H25'], inplace=True)
df_übersicht_23.drop(columns=['Tagestyp','Monat','G25','Industrie','GHD','Verkehr','Haushalte_stat','H25'], inplace=True)
print("quatsch")