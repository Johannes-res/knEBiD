# knEBiD
klimaneutrale Energiebereitstellung in Deutschland


Hier wird eine Modellierung einer klimaneutralen Energieversorgung für Deutschland erstellt.
Dazu wird zunächst der Verbrauch bzw. Bedarf anhand vorhandener Prognosen in Zeitreihen modelliert.
Danach kann dieser Bedarf mittels Variation verschiedener regenerativen Umwandlungstechnologien gedeckt werden.


# Datenstruktur
Perspektivisch soll möglichst Benutzer*innenfreundlich über main.py alles gesteuert werden können.
Für mehr Übersichtlichkeit wurden einzelne .py-Dateien erstellt, welche abtrennbare Funktionen ausführen.
So gibt es momentan:

daten_einlesen.py                 Einlesen von Tabellen etc.
graphisch_darstellen.py           Plotten von Zeitreihen zur graphischen Überprüfung
last_aufteilen.py                 Aufteilen der allgemeinen Last in Verbrauchssektoren
last_prognose.py                  Erweiterung des last_aufteilen.py mit der Möglichkeit neue Verbraucherprofile und Energiebedarfe zu ergänzen
lastprofile_modellieren.py        eigenhändiges Erstellen von Lastprofilen um neue Verbraucher dynamisch mit in die Zeitreihen einfließen zu lassen



# daten_einlesen.py
Hier werden zunächst die Daten von energy-charts.info geladen sowie die Energiebilanz für Deutschland von der AGEB. Zudem werden die neuen Standardlastprofile des BDEW geladen.
Danach werden die Dataframes aufbereitet und die relevanten Daten extrahiert.

# graphisch_darstellen.py
Hier können beliebige Jahreszeitreihen importiert werden und der Jahresgang, ein einzelner Tag oder eine Woche dargestellt werden.

# last_aufteilen.py
Hier wird die Lastzeitreihe anhand der Endstromverbräuche der Sektoren sowie den Lastprofilen aufgeteilt.

# last_prognose.py
Macht das selbe wie last_aufteilen.py. Zusätzlich können neue Verbrauchergruppen wie zb. die Emobilität mit einem Lastprofil eingelesen und der anteil an der Last pro 15min-Wert ermittelt werden

# lastprofile_modellieren.py
Schafft die Möglichkeit eigene Lastprofile in Anlehnung der Standardlastprofile des BDEW zu erstellen.
Momentan ist ein EMob_Lastprofil sowie ein Wärmpepumpen Lastprofil initialisiert.
