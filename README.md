# knEBiD
klimaneutrale Energiebereitstellung in Deutschland


Hier wird eine Modellierung einer klimaneutralen Energieversorgung für Deutschland erstellt.
Dazu wird zunächst der Verbrauch bzw. Bedarf anhand vorhandener Prognosen in Zeitreihen modelliert.
Danach kann dieser Bedarf mittels Variation verschiedener regenerativen Umwandlungstechnologien gedeckt werden.


# energy_charts_Zeitreihen.py

Hier werden zunächst die Daten von energy-charts.info geladen sowie die Energiebilanz für Deutschland von der AGEB. (zusätzlich müssen noch die Lastprofile des BDEW eingelesen werden)
Danach werden die Dataframes aufbereitet und die relevanten Daten extrahiert.
Um den Lastverlauf einzelnen Sektoren zuordnen zu können, wird der Energiebedarf jedes Sektors pro Endenergiebedarf aufgeteilt.
Dies erfolgt zunächst für den Stromverbrauch.

Danach soll der Lastgang in Sektoren aufgeteilt werden. Dazu müssen noch sektorspezifische Lastprofile hinterlegt werden, welche die Summe der Last anteilig für den Sektor auf die 15min-Werte aufteilt.
