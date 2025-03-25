import requests
import pandas as pd

# URL der XML-Datei
#bei 'Start' kann das Startdatum angegeben werden, bei 'End' das Enddatum
#hier wird das Startdatum auf den 01.10.2022 und das Enddatum auf den 31.10.2022 gesetzt
url = "https://datenservice.tradinghub.eu/XmlInterface/getXML.ashx?ReportId=AggregatedConsumptionData&Start=01-10-2022&End=31-10-2022"

"""https://www.tradinghub.eu/Portals/0/The_XML_Interface_V2.0_de.pdf?ver=A5R82BaYi7YlQDZEGs3inQ%3d%3d beinhaltet die Anleitung zur Nutzung der XML-Schnittstelle

Hier können die Daten der Veröffentlichung der aggregierten Verbrauchsmengen
im Marktgebiet je Gastag abgerufen werden.
Hinweis: Sollte das Startdatum nicht mit angegeben werden, wird das Startdatum
auf das Datum des ältesten Datensatzes gesetzt. Sollte das Enddatum nicht mit
angegeben werden, werden alle vorhandenen Daten, abhängig vom Startdatum
ausgegeben. Sollte kein Datum angegeben werden, werden alle Daten abgerufen.
"""



# XML-Daten abrufen
response = requests.get(url)

# XML in DataFrame umwandeln
df = pd.read_xml(response.content, xpath="//ns:AggregatedConsumptionData", namespaces={"ns": "urn:schemas-microsoft-com:sql:SqlRowSet1"})

# DataFrame anzeigen
# print(df)