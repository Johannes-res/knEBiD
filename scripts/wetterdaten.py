from meteostat import Stations, Daily
from datetime import datetime

# Zeitraum definieren
start = datetime(2022, 1, 1)
end = datetime(2022, 12, 31)

# Wetterstationen in Deutschland auswählen (z.B. 50 zufällige Stationen)
stations = Stations().region('DE').inventory('daily', (start, end)).fetch(limit=50, sample=True)

# Tageswerte laden und räumlich mitteln
weather = Daily(stations, start, end)
df = weather.aggregate('1D', spatial=True).fetch()

# Die Spalte 'tavg' enthält die gemittelte Tagesdurchschnittstemperatur
print(df[['tavg']])

#ändere das dateformat in datetime auf werte ohne Zeitumstellung
df.index = df.index.tz_localize('UTC')
df.index = df.index.strftime('%Y-%m-%d')

df.to_excel(r'data\Wetterdaten\durchschnitt_täglich_22.xlsx')


print('meteostat skript beendet')