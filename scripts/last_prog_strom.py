#%%Pakete und Module importieren

import pandas as pd
import holidays
import numpy as np

from daten_einlesen import df_Nettostromerzeugung_22
from daten_einlesen import df_Nettostromerzeugung_23
from daten_einlesen import df_Nettostromerzeugung_24
from daten_einlesen import df_AGEB_22
from daten_einlesen import df_AGEB_23
from daten_einlesen import df_AGEB_24
from daten_einlesen import df_Lastprofil_H25
from daten_einlesen import df_Lastprofil_G25
from lastprofile_modellieren import df_Lastprofil_EMob_jahr as df_e_mod
from lastprofile_modellieren import df_Lastprofil_WP_jahr as df_WP

from klimaneutral_heute import übersicht_gesamt as kn_heute_ü

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

def ergänze_lastprofile(df_last, df_profil, name):

    """
    Ergänzt den DataFrame df_last mit der Spalte 'Name', basierend auf den Werten
    aus df_profil entsprechend der Spalte Monats_Tageskennung und den Uhrzeiten.
    

    :param df_last: Der DataFrame, der ergänzt werden soll (z. B. df_Last_22).
    :param df_profil: Der DataFrame mit den Lastprofilwerten.
    
    :return: Der ergänzte DataFrame.
    """
    # Stelle sicher, dass die Indizes von df_Lastprofildatetime.time-Objekte sind
    df_profil.index = pd.to_datetime(df_profil.index, format='%H:%M:%S').time


    # Initialisiere die neuen Spalten G25 und H25
    df_last[name] = df_last.apply(
        lambda row: df_profil.loc[row.name.time(), row['Monats_Tageskennung']], axis=1
        )
    return df_last

def saisonschwankungen_modellieren(t):
    """
    Simuliert saisonale Schwankungen im Stromverbrauch (x = Tag 1-365)
    Gibt relativen Verbrauchsfaktor zurück (1.0 = Durchschnitt)
    """
    # Jahreszeitliche Grundschwingung (Hauptmaximum im Winter)
    saison = 0.1 * np.cos(2*np.pi*(t - 15)/365)
    
    # Weihnachtseffekt (Spitze im Dezember)
    weihnachten = 0.1 * np.exp(-((t - 355)/10)**2)
    
    # Sommerdip mit leichtem Anstieg durch Kühlung
    sommer = -0.015 * np.exp(-((t - 200)/60)**2)
    
    # Zufällige tägliche Schwankungen (Rauschen)
    # rauschen = 0.05 * np.random.normal()
    
    return 1.0 + saison #+ weihnachten + sommer + rauschen

def modelliere_Sektorenzeitreihen(df_last,ESB_gesamt, ESB_Industrie, ESB_GHD, ESB_Haushalte, ESB_Verkehr, ESB_Emob,ESB_WP, faktor_G25, faktor_H25, faktor_Emob, faktor_WP):


    """
    #Als Übergabe muss ein Zeitreihen-Dataframe mit den Lastprofilzeitreihen übergeben werden (stammt von df_Last_22_mit_Profilen)
    #Es müssen die Jahresstrommengen für die einzelnen Sektoren übergeben werden (stammt von df_EEB_Sektoren)
    
    
    Hier werden die Lastprofile mit den Stromverbräuchen der Sektoren multipliziert
    Die Standardlastprofile sind auf 1Mio. kWH normiert, weswegen durch 1000 geteilt werden muss um auf 1MWh zu kommen.
    Die modellierten Profile und daraus entstehenden Zeitreihen sind auf 1/15-min Wert normiert und können so als Faktor angesehen werden.
    Für die Flexibilität wird die Rechnung mit dem gleichverteilenden Anteil erweitert """

    t= df_last.index.dayofyear
    #Die Lastprofile sind auf 1Mio. kWH normiert, weswegen durch 1000 geteilt werden muss um auf 1MWh zu kommen. Dann wird mit dem Endstrombedarf des Sektors multipliziert
    # Die Viertelstundenwerte sind in kWh angegeben, daher wird durch 10e3 geteilt, um auf MWh zu kommen

    #Hier wird die Last mit dem Gesamtstrombedarf multipliziert, so dass man die Änderung abbilden kann
    df_last['Last_prognose [MWh]']= df_last['Energie [MWh]']* (ESB_gesamt/df_last['Energie [MWh]'].sum())

    #Energiemenge des Sektors=      ((((Lastprofil/1000)*Endstrombedarf_Sektor)/1000)*Wichtung_des_Profils + (ESB/len(df_last))*(1-faktor))*saisonschwankungen_modellieren(t)
    df_last['Industrie'] =          ((((df_last['G25']/1e3) * ESB_Industrie)/1e3)    * faktor_G25 + (ESB_Industrie/len(df_last)) * (1-faktor_G25)) *(0.9+0.1*saisonschwankungen_modellieren(t))
    df_last['GHD'] =                ((((df_last['G25']/1e3) * ESB_GHD)/1e3)          * faktor_G25 + (ESB_GHD/len(df_last))       * (1-faktor_G25)) *(0.9+0.1*saisonschwankungen_modellieren(t))
    df_last['Haushalte_stat'] =     ((((df_last['H25']/1e3) * ESB_Haushalte)/1e3)    * faktor_H25 + (ESB_Haushalte/len(df_last)) * (1-faktor_H25)) *(0.9+0.1*saisonschwankungen_modellieren(t))
    # df_last['Haushalte_dyn'] =    ((df_last['H25'] / 1e3) * ESB_Haushalte) * (-3.92e-10 * t**4 + 3.2e-7 * t**3 - 7.02e-5 * t + 2.1e-3*t + 1.24)/1e3 #FEHLER!!!Exponentiell ansteigend!
    df_last['Verkehr'] =            (ESB_Verkehr / len(df_last))
    
    #prognose zeitreihen der zusätzlichen Verbraucher mit Normierung mittels Teilung durch das Integral der Lastprofile
    df_last['EMobilität']=         (((df_last['EMob']/df_last['EMob'].sum())        * ESB_Emob)             * faktor_Emob + (ESB_Emob/len(df_last))     *(1-faktor_Emob))   *(0.9+0.1*saisonschwankungen_modellieren(t))
    df_last['Wärmepumpen']=        (((df_last['WP']/df_last['WP'].sum())           * ESB_WP)                * faktor_WP   + (ESB_WP/len(df_last))       *(1-faktor_WP))       *(1.0*saisonschwankungen_modellieren(t))

    df_last['Summe_Sektoren_modelliert'] = (df_last['Industrie']
                                            +df_last['GHD']
                                            +df_last['Haushalte_stat']
                                            +df_last['Verkehr']
                                            +df_last['EMobilität']
                                            +df_last['Wärmepumpen'])

    ##Hier wird der Anteil der einzelnen Sektoren, dynamisiert durch die Standardlastprofile, an der Gesamtlast für jede Viertelstunde berechnet
    df_last['Anteil_Industrie'] = df_last['Industrie'] / df_last['Summe_Sektoren_modelliert']
    df_last['Anteil_GHD'] = df_last['GHD'] / df_last['Summe_Sektoren_modelliert']
    df_last['Anteil_Haushalte_stat'] = df_last['Haushalte_stat'] / df_last['Summe_Sektoren_modelliert']
    # df_last['Anteil_Haushalte_dyn'] = df_last['Haushalte_dyn'] / df_last['Summe_Sektoren_modelliert']
    df_last['Anteil_Verkehr'] = df_last['Verkehr'] / df_last['Summe_Sektoren_modelliert']
    df_last['Anteil_EMobilität'] = df_last['EMobilität'] / df_last['Summe_Sektoren_modelliert']
    df_last['Anteil_Wärmepumpen'] = df_last['Wärmepumpen'] / df_last['Summe_Sektoren_modelliert']


    return df_last



#%% Funktionen ausführen
df_übersicht_22 = verbrauchsübersicht_erstellen(df_Nettostromerzeugung_22,df_AGEB_22)
df_übersicht_23 = verbrauchsübersicht_erstellen(df_Nettostromerzeugung_23,df_AGEB_23)
df_übersicht_24 = verbrauchsübersicht_erstellen(df_Nettostromerzeugung_24,df_AGEB_24)

df_übersicht_22 = add_day_type(df_übersicht_22)
df_übersicht_23 = add_day_type(df_übersicht_23)
df_übersicht_24 = add_day_type(df_übersicht_24)

df_übersicht_22 = ergänze_lastprofile(df_übersicht_22, df_Lastprofil_G25, 'G25')
df_übersicht_22 = ergänze_lastprofile(df_übersicht_22, df_Lastprofil_H25, 'H25')
df_übersicht_22 = ergänze_lastprofile(df_übersicht_22, df_e_mod, 'EMob')
df_übersicht_22 = ergänze_lastprofile(df_übersicht_22, df_WP, 'WP')

df_übersicht_23 = ergänze_lastprofile(df_übersicht_23, df_Lastprofil_G25, 'G25')
df_übersicht_23 = ergänze_lastprofile(df_übersicht_23, df_Lastprofil_H25, 'H25')
df_übersicht_23 = ergänze_lastprofile(df_übersicht_23, df_e_mod, 'EMob')
df_übersicht_23 = ergänze_lastprofile(df_übersicht_23, df_WP, 'WP')

df_übersicht_24 = ergänze_lastprofile(df_übersicht_24, df_Lastprofil_G25, 'G25')
df_übersicht_24 = ergänze_lastprofile(df_übersicht_24, df_Lastprofil_H25, 'H25')
df_übersicht_24 = ergänze_lastprofile(df_übersicht_24, df_e_mod, 'EMob')
df_übersicht_24 = ergänze_lastprofile(df_übersicht_24, df_WP, 'WP')

#Hier werden die Zeitreihen der Sektoren mit den Endstrombedarfen der Sektoren ergänzt
#Die Endstrombedarfe stammen aus dem AGEB und sind auf die Jahre 2022 und 2023 bezogen
#Die Werte für die E-Mobilität und Wärmepumpen sind noch nicht berücksichtigt, da diese erst in den Jahren 2045/46 relevant werden  


df_übersicht_22 = modelliere_Sektorenzeitreihen(
     df_übersicht_22,                                                                                           #Zeitreihe, welche ergänzt werden soll
     df_übersicht_22['Energie [MWh]'].sum(),                                                                      #Gesamtstrombedarf
     df_AGEB_22.loc['Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe','Stromenergiemenge_anteilig [MWh]'],   #Endstrombedarf der Industrie
     df_AGEB_22.loc['Gewerbe, Handel, Dienstleistungen','Stromenergiemenge_anteilig [MWh]'],                    #Endstrombedarf des GHD
     df_AGEB_22.loc['Haushalte','Stromenergiemenge_anteilig [MWh]'],                                            #Endstrombedarf der Haushalte
     df_AGEB_22.loc['Verkehr insgesamt','Stromenergiemenge_anteilig [MWh]'],                                    #Endstrombedarf des Verkehrs
     0,                                                                                                      #Endstrombedarf der E-Mobilität
     0,                                                                                                       #Endstrombedarf der Wärmepumpen
     0.5,                                                                                                       #Wichtung des Profils G25
     0.5,                                                                                                       #Wichtung des Profils H25
     0.5,                                                                                                       #Wichtung des Profils E-Mobilität
     0.5                                                                                                        #Wichtung des Profils Wärmepumpen
    )

df_übersicht_23 = modelliere_Sektorenzeitreihen(
     df_übersicht_23,                                                                                           #Zeitreihe, welche ergänzt werden soll
     df_übersicht_23['Energie [MWh]'].sum(),                                                                      #Gesamtstrombedarf
     df_AGEB_23.loc['Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe','Stromenergiemenge_anteilig [MWh]'],   #Endstrombedarf der Industrie
     df_AGEB_23.loc['Gewerbe, Handel, Dienstleistungen','Stromenergiemenge_anteilig [MWh]'],                    #Endstrombedarf des GHD
     df_AGEB_23.loc['Haushalte','Stromenergiemenge_anteilig [MWh]'],                                            #Endstrombedarf der Haushalte
     df_AGEB_23.loc['Verkehr insgesamt','Stromenergiemenge_anteilig [MWh]'],                                    #Endstrombedarf des Verkehrs
     0,                                                                                                      #Endstrombedarf der E-Mobilität
     0,                                                                                                       #Endstrombedarf der Wärmepumpen
     0.5,                                                                                                       #Wichtung des Profils G25
     0.5,                                                                                                       #Wichtung des Profils H25
     0.5,                                                                                                       #Wichtung des Profils E-Mobilität
     0.5                                                                                                        #Wichtung des Profils Wärmepumpen
    )



df_übersicht_24 = modelliere_Sektorenzeitreihen(
     df_übersicht_24,                                                                                           #Zeitreihe, welche ergänzt werden soll
     df_übersicht_24['Energie [MWh]'].sum(),                                                                      #Gesamtstrombedarf
     df_AGEB_24.loc['Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe','Stromenergiemenge_anteilig [MWh]'],   #Endstrombedarf der Industrie
     df_AGEB_24.loc['Gewerbe, Handel, Dienstleistungen','Stromenergiemenge_anteilig [MWh]'],                    #Endstrombedarf des GHD
     df_AGEB_24.loc['Haushalte','Stromenergiemenge_anteilig [MWh]'],                                            #Endstrombedarf der Haushalte
     df_AGEB_24.loc['Verkehr insgesamt','Stromenergiemenge_anteilig [MWh]'],                                    #Endstrombedarf des Verkehrs
     0,                                                                                                      #Endstrombedarf der E-Mobilität
     0,                                                                                                       #Endstrombedarf der Wärmepumpen
     0.5,                                                                                                       #Wichtung des Profils G25
     0.5,                                                                                                       #Wichtung des Profils H25
     0.5,                                                                                                       #Wichtung des Profils E-Mobilität
     0.5                                                                                                        #Wichtung des Profils Wärmepumpen
    )

#Für die Strombedarfe des Jahres 2045 wurden die Mittelwerte der Metastudien von Agora und EWI (DENA) verwendet
df_übersicht_45_22 = modelliere_Sektorenzeitreihen(
     df_übersicht_22,                                                                                           #Zeitreihe, welche ergänzt werden soll
     767500000,                                                                                                 #Gesamtstrombedarf
     351330000,                                                                                                 #Endstrombedarf der Industrie
     90010000,                                                                                                  #Endstrombedarf des GHD
     183590000,                                                                                                 #Endstrombedarf der Haushalte
     100000000,                                                                                                 #Endstrombedarf des Verkehrs
     42500000,                                                                                                  #Endstrombedarf der E-Mobilität
     1,                                                                                                         #Endstrombedarf der Wärmepumpen
     0.5,                                                                                                       #Wichtung des Profils G25
     0.5,                                                                                                       #Wichtung des Profils H25
     0.5,                                                                                                       #Wichtung des Profils E-Mobilität
     0.5                                                                                                        #Wichtung des Profils Wärmepumpen
    )

df_übersicht_45_23 = modelliere_Sektorenzeitreihen(
     df_übersicht_23,                                                                                           #Zeitreihe, welche ergänzt werden soll
     767500000,                                                                                                 #Gesamtstrombedarf
     351330000,                                                                                                 #Endstrombedarf der Industrie
     90010000,                                                                                                  #Endstrombedarf des GHD
     183590000,                                                                                                 #Endstrombedarf der Haushalte
     100000000,                                                                                                 #Endstrombedarf des Verkehrs
     42500000,                                                                                                  #Endstrombedarf der E-Mobilität
     1,                                                                                                         #Endstrombedarf der Wärmepumpen
     0.5,                                                                                                       #Wichtung des Profils G25
     0.5,                                                                                                       #Wichtung des Profils H25
     0.5,                                                                                                       #Wichtung des Profils E-Mobilität
     0.5                                                                                                        #Wichtung des Profils Wärmepumpen
    )


df_übersicht_45_24 = modelliere_Sektorenzeitreihen(
     df_übersicht_24,                                                                                           #Zeitreihe, welche ergänzt werden soll
     767500000,                                                                                                 #Gesamtstrombedarf
     351330000,                                                                                                 #Endstrombedarf der Industrie
     90010000,                                                                                                  #Endstrombedarf des GHD
     183590000,                                                                                                 #Endstrombedarf der Haushalte
     100000000,                                                                                                 #Endstrombedarf des Verkehrs
     42500000,                                                                                                  #Endstrombedarf der E-Mobilität
     1,                                                                                                         #Endstrombedarf der Wärmepumpen
     0.5,                                                                                                       #Wichtung des Profils G25
     0.5,                                                                                                       #Wichtung des Profils H25
     0.5,                                                                                                       #Wichtung des Profils E-Mobilität
     0.5                                                                                                        #Wichtung des Profils Wärmepumpen
    )

df_übersicht_22_klimaneutral = modelliere_Sektorenzeitreihen(
     df_übersicht_22,                                                                                           #Zeitreihe, welche ergänzt werden soll
     kn_heute_ü.loc['Summe_Energieträger', 'Strom']*1e6,                                                                                                 #Gesamtstrombedarf
     kn_heute_ü.loc[2, 'Strom']*1e6,                                                                                                 #Endstrombedarf der Industrie
     kn_heute_ü.loc[0, 'Strom']*1e6*0.4,                                                                                                  #Endstrombedarf des GHD
     kn_heute_ü.loc[0, 'Strom']*1e6*0.4,                                                                                                 #Endstrombedarf der Haushalte
     kn_heute_ü.loc[1, 'Strom']*1e6*0.4,                                                                                                 #Endstrombedarf des Verkehrs
     kn_heute_ü.loc[1, 'Strom']*1e6*0.6,                                                                                                  #Endstrombedarf der E-Mobilität
     kn_heute_ü.loc[0, 'Strom']*1e6*0.2,                                                                                                         #Endstrombedarf der Wärmepumpen
     0.5,                                                                                                       #Wichtung des Profils G25
     0.5,                                                                                                       #Wichtung des Profils H25
     0.5,                                                                                                       #Wichtung des Profils E-Mobilität
     0.5                                                                                                        #Wichtung des Profils Wärmepumpen
    )


df_22=df_übersicht_22.copy()
df_23=df_übersicht_23.copy()
df_24=df_übersicht_24.copy()
df_45_22=df_übersicht_45_22.copy()
df_45_23=df_übersicht_45_23.copy()
df_45_24=df_übersicht_45_24.copy()
df_22_kn=df_übersicht_22_klimaneutral.copy()


#Erstellen eines zweijährigen DataFrames mit den Zeitreihen der Jahre 22 und 23 als Basis
df_45_46=pd.concat([df_45_22, df_45_23], axis=0)
df_45_46_47=pd.concat([df_45_22, df_45_23, df_45_24], axis=0)

def drop_für_Übersicht(df):
    df.drop(columns=['Last [MW]','Summe_Sektoren_modelliert','Tagestyp','Monat','G25','Industrie','GHD','Verkehr','Haushalte_stat','H25','EMob','WP','Anteil_Industrie', 'Anteil_GHD', 'Anteil_Haushalte_stat', 'Anteil_Verkehr', 'Anteil_EMobilität', 'Anteil_Wärmepumpen'], inplace=True)
    return df
df_strom_22 = drop_für_Übersicht(df_22)
df_strom_23 = drop_für_Übersicht(df_23)
df_strom_34 = drop_für_Übersicht(df_24)
df_strom_45_22 = drop_für_Übersicht(df_45_22)
df_strom_45_23 = drop_für_Übersicht(df_45_23)
df_strom_45_24 = drop_für_Übersicht(df_45_24)
df_strom_45_46 = drop_für_Übersicht(df_45_46)
df_strom_45_46_47 = drop_für_Übersicht(df_45_46_47) 

df_strom_22_kn = drop_für_Übersicht(df_22_kn)


print("Ende des last_prognose_strom Skripts")
# %%
