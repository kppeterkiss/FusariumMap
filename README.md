# FusariumMap - workplan

## Interaktív fuzárium térkép (Python web + ArcGIS / QGIS)
- ODP 1 órás gyakoriságú adatsor letöltése (folyamatos adatbázisba importálás)
    - folyamatos adatok: https://odp.met.hu/climate/observations_hungary/hourly/
    - napi adatok: https://odp.met.hu/weather/weather_reports/synoptic/hungary/hourly/
- MATE mérőállomások folyamatos betöltése (ehhez még kell hozzáférés)
- P% valószínűség számítás az egyes mérőállomásokra:
    - 7 napos mozgó átlag
    - p% = –3.3756 + 6.8128*TRH9010         (1)          ahol: p a fertőzés valószínűsége %-ban, TRH9010 a feltételeknek megfelelő (RH>90% és 15 °C<=Ta<=30 °C) egybefüggő óraszám (óra).
    - A virágzást megelőző és azt követő időszakban használható legjobb úgynevezett interakciós modell (2)
    - p% = –3.7251 + 10.5097*INT3 (2)          ahol: p a fertőzés valószínűsége %-ban,
    - INT3 a feltételeknek megfelelő virágzást megelőző 15 °C<=Ta<=30 °C és a virágzást követő RH>90% egybefüggő óraszám (óra). Az interakció a hőmérséklet súlyozott figyelembevételére vonatkozik.
- Interaktív (időszerűséget is mutató) térkép – az egyes pontok között interpolálva
 
## V1 verzió: Python / QGIS  és ArcGIS:
  1. ODP adatok letöltése, transzformálása megfelelő
  2. Térkép (Python / QGIS) lokális adatokból
  3. ArcGIS térkép lokális adatokból
## V2. Azure-ban lévő DB-be tölteni az adatokat folyamatosan
## V3. fájlszerverre menjen az OMSZ csv (adattranszformáció)
  - SQL szerver betölti CSV-t
  - ArcGIS VPN-en / remote desktop-n keresztül elérje a DB-t (MATE feladat)
  - ArcGIS Fuzárium térkép a MATE DB-ből

# Implementation 
## V1 verzió: Python / QGIS  és ArcGIS:
Loading the data:
### start database


```docker compose up```
-  postgres + pgadmin
- ```.env``` file
```
POSTGRES_PASSWORD=secret
PGADMIN_DEFAULT_EMAIL=admin@example.com
PGADMIN_DEFAULT_PASSWORD=secret
```

We can check (or delete) the tables using pgAdmin, that is also started by   ```localhost:15080``` using ```PGADMIN_DEFAULT_EMAIL``` and  ```PGADMIN_DEFAULT_PASSWORD```.

### Generating datatable with python:

Run the ```research.ipynb``` , that will pull last 7 days data from the database, and calculate ```p```


 - Start ArcGIS
 - Add Data  from top menu - chose output csv
 - Display XY data after right click - detects automatically coordinates -OK
 - Properties - Time - each feature has a single time filed - leave at "Time"
 - Symbology :
![Setting symbology](img/symbology.png "Setting symbology")

First result:
![Time + Heatmap](img/arcgisv1.gif "Time + Heatmap")

