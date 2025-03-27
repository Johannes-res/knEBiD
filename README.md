# knEBiD
klimaneutrale Energiebereitstellung in Deutschland


Hier wird eine Modellierung einer klimaneutralen Energieversorgung für Deutschland erstellt.
Dazu wird zunächst der Verbrauch bzw. Bedarf anhand vorhandener Prognosen in Zeitreihen modelliert.
Danach kann dieser Bedarf mittels Variation verschiedener regenerativen Umwandlungstechnologien gedeckt werden.


# energy_charts_Zeitreihen.py

Hier werden zunächst die Daten von energy-charts.info geladen sowie die Energiebilanz für Deutschland von der AGEB. (zusätzlich müssen noch die Lastprofile des BDEW eingelesen werden)
Danach werden die Dataframes aufbereitet und die relevanten Daten extrahiert.
Um den Lastverlauf einzelnen Sektoren zuordnen zu können, wird der Energiebedarf jedes Sektors durch den Gesamtendenergiebedarf geteilt. So erhält man die Anteile.
Dies erfolgt zunächst primär für den Stromverbrauch.
Es wird die Aufteilung nach Verbrauchergruppen des BDEW genutzt.
(https://www.bdew.de/service/daten-und-grafiken/strom-verbrauch-nach-verbrauchergruppen/)

Aus dem Lastverlauf des Jahres wird die Summe gebildet und nach Sektoren aufgeteilt.
//Hier muss noch der EEB mitgenommen werden als Kontrollzahl

Als nächstes wird initial mit den Standardlastprofilen versucht den zeitaufgelösten Verbrauch zu modellieren.
Dabei gilt als Vergleich der tatsächliche Lastgang mit der Summe der modellierten Lasten.



Danach soll der Lastgang in Sektoren aufgeteilt werden. Dazu müssen noch sektorspezifische Lastprofile hinterlegt werden, welche die Summe der Last anteilig für den Sektor auf die 15min-Werte aufteilt.
