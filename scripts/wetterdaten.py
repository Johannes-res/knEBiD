from datetime import datetime
import pandas as pd
from meteostat import Hourly

start = datetime(2022, 1, 1)
end = datetime(2022, 12, 31, 23, 59)

data= Hourly(10637, start, end, timezone='Europe/Berlin')
data = data.fetch()

#ändere das dateformat in datetime auf werte ohne Zeitumstellung
data.index = data.index.tz_convert('UTC')
#data.index = pd.to_datetime(data.index, format='%H:%M:%S').time



print('meteostat skript beendet')