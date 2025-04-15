from daten_einlesen import df_Nettostromerzeugung_22
from daten_einlesen import df_Nettostromerzeugung_23

#das Maximum der einzelenen Erzeugertechnologien wird als installierte Leistung gesehen und darauf nomiert. Danach wird mit der Prognose der installierten Leistung multipliziert

def erzeuger_prognose(df, Technologiename, Leistungsprognose):
    df_prog=df.copy()

    df_prog[Technologiename]=df[Technologiename]/df[Technologiename].max() * Leistungsprognose
    return df_prog

df_prognose_22 = erzeuger_prognose(df_Nettostromerzeugung_22, 'Wind Onshore', 100)

print('Ende des Erzeuger Skripts')