import pandas as pd
import numpy as np


def ergänze_Zeitreihen(df, df_profil, name, EEB, saisonalerfaktor):

    """
    Ergänzt den DataFrame df_last mit der Spalte 'Name', basierend auf den Werten
    aus df_profil entsprechend der Spalte Monats_Tageskennung und den Uhrzeiten.
    

    :param df_last: Der DataFrame, der ergänzt werden soll (z. B. df_Last_22).
    :param df_profil: Der DataFrame mit den Lastprofilwerten.
    
    :return: Der ergänzte DataFrame.
    """
    t= df.index.dayofyear
    def saisonschwankungen_modellieren(t):
        """
        Simuliert saisonale Schwankungen im Stromverbrauch (x = Tag 1-365)
        Gibt relativen Verbrauchsfaktor zurück (1.0 = Durchschnitt)
        """
        # Jahreszeitliche Grundschwingung (Hauptmaximum im Winter)
        saison = 0.15 * np.cos(2*np.pi*(t - 15)/365)
        
        # Weihnachtseffekt (Spitze im Dezember)
        weihnachten = 0.1 * np.exp(-((t - 355)/10)**2)
        
        # Sommerdip mit leichtem Anstieg durch Kühlung
        sommer = -0.015 * np.exp(-((t - 200)/60)**2)
        
        # Zufällige tägliche Schwankungen (Rauschen)
        # rauschen = 0.05 * np.random.normal()
        
        return 1.0 + saison #+ weihnachten + sommer + rauschen

    # Stelle sicher, dass die Indizes von df_Lastprofildatetime.time-Objekte sind
    df_profil.index = pd.to_datetime(df_profil.index, format='%H:%M:%S').time

    # Initialisiere die neue Spalte
    df[name] = df.apply(
        lambda row: df_profil.loc[row.name.time(), row['Monats_Tageskennung']], axis=1
        )
    
    # Wende den saisonalen Faktor an
    df[name] = (df[name]/df[name].sum()) * EEB *((1-saisonalerfaktor)+(saisonalerfaktor*saisonschwankungen_modellieren(t)))  # Normalisiere die Werte auf die Jahresenergiemenge

    return df



# Hier werden die Lastprofile für die weiteren Verbraucher erzeugt
#dazu werden die Funktionen aus de, sltript lastprofile_modellieren verwendet

from lastprofile_modellieren import generiere_stufenfunktion
from lastprofile_modellieren import auf_monate_erweitern

from klimaneutral_heute import übersicht_gesamt

df_wasserstoffprofil = generiere_stufenfunktion( {'WT': ([5,8, 12, 19], [1, 1, 1, 1]), 'SA': ([7, 14, 20], [1, 1, 1]), 'FT': ([1, 12, 18], [1, 1, 1])}, decay_rate = 0.0)
df_wasserstoffprofil = auf_monate_erweitern(df_wasserstoffprofil,)

df_biomasse = generiere_stufenfunktion( {'WT': ([5,8, 12, 19], [1, 1, 1, 1]), 'SA': ([7, 14, 20], [1, 1, 1]), 'FT': ([1, 12, 18], [1, 1, 1])}, decay_rate = 0.0)
df_biomasse = auf_monate_erweitern(df_biomasse,)

df_fernwärme = generiere_stufenfunktion( {'WT': ([5,8, 12, 19], [1, 1, 1, 1]), 'SA': ([7, 14, 20], [1, 1, 1]), 'FT': ([1, 12, 18], [1, 1, 1])}, decay_rate = 0.0)
df_fernwärme = auf_monate_erweitern(df_fernwärme,)

df_sonstige = generiere_stufenfunktion( {'WT': ([5,8, 12, 19], [1, 1, 1, 1]), 'SA': ([7, 14, 20], [1, 1, 1]), 'FT': ([1, 12, 18], [1, 1, 1])}, decay_rate = 0.0)
df_sonstige = auf_monate_erweitern(df_sonstige,)



#Dann werden diese der Zeitreihe hinzugefügt und mit den Jahresenergiemengen verrechnet
from last_prog_strom import df_strom_22_kn


df_22_kn = ergänze_Zeitreihen(df_strom_22_kn, df_wasserstoffprofil, 'Wasserstoff', übersicht_gesamt.loc['Summe_Energieträger', 'Wasserstoff']*1e6, 0.5)
df_22_kn = ergänze_Zeitreihen(df_strom_22_kn, df_biomasse, 'Biomasse', übersicht_gesamt.loc['Summe_Energieträger', 'Biomasse']*1e6, 0)
df_22_kn = ergänze_Zeitreihen(df_strom_22_kn, df_wasserstoffprofil, 'Thermie', übersicht_gesamt.loc['Summe_Energieträger', 'Thermie']*1e6, 1)
df_22_kn = ergänze_Zeitreihen(df_strom_22_kn, df_wasserstoffprofil, 'E-Fuels', übersicht_gesamt.loc['Summe_Energieträger', 'E-Fuels']*1e6, 0)

df_22_kn.rename(columns={'Last_prognose [MWh]': 'Strom [MWh]'}, inplace=True)
df_22_kn.rename(columns={'Energie [MWh]': 'Energie_22_org [MWh]'}, inplace=True)
#df_22_kn = ergänze_Zeitreihen(df_strom_22_kn, df_fernwärme, 'Fernwärme', übersicht_gesamt.loc['Summe_Energieträger', 'Fernwärme'], 1)
# df_22_kn = ergänze_Zeitreihen(df_strom_22_kn, df_sonstige, 'Sonstige', 172500000, 0)


print(f"Strom: {df_22_kn['Strom [MWh]'].sum()}")
print(f"Wasserstoff:{df_22_kn['Wasserstoff'].sum()}")
print(f"Biomasse: {df_22_kn['Biomasse'].sum()}")
print(f"E-Fuels: {df_22_kn['E-Fuels'].sum()}")
print(f"Thermie: {df_22_kn['Thermie'].sum()}")

print(df_22_kn['Strom [MWh]'].sum()+df_22_kn['Wasserstoff'].sum() + df_22_kn['Biomasse'].sum() + df_22_kn['E-Fuels'].sum() + df_22_kn['Thermie'].sum())
print('Ende des Lastprognose allgemein Skriptes')


