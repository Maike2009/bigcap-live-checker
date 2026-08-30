
# Big-Cap Live Checker – Version 1

Kostenlose Web-App für den gleichzeitigen Gegencheck von:
AAPL, NVDA, MSFT, AMZN, META und TSLA.

## Funktionen
- Live-Ticks über Finnhub WebSocket
- Umschalter M1 / M5 / M15
- LONG / SHORT / NEUTRAL je Aktie
- Gesamtbild für alle 6 Aktien
- Datenalter pro Aktie

## Kostenlos starten
1. Kostenloses Finnhub-Konto anlegen und API-Key erstellen.
2. Python installieren.
3. Im App-Ordner ausführen:
   pip install -r requirements.txt
4. Danach:
   streamlit run app.py
5. API-Key links in der App eintragen.

## Handy
Wenn Handy und Computer im selben WLAN sind:
   streamlit run app.py --server.address 0.0.0.0
Dann die von Streamlit angezeigte Network-URL im Handy-Browser öffnen.

## Signal-Regel in V1
Die App baut aus den Live-Trades selbst die laufende M1-, M5- oder M15-Kerze.
- LONG = aktueller Kurs über dem Open der laufenden Kerze
- SHORT = aktueller Kurs unter dem Open
- NEUTRAL = innerhalb der einstellbaren Neutral-Zone

## Wichtig
Die V1 sammelt die Kerze erst ab dem Zeitpunkt, an dem die App läuft.
Sie ist ein Markt-Gegencheck und kein Kauf-/Verkaufssignal.
Kostenlose Datenanbieter können ihre Bedingungen ändern.
