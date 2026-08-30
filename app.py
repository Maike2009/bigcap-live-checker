
import json
import threading
import time
from collections import defaultdict, deque

import pandas as pd
import streamlit as st
import websocket

st.set_page_config(page_title="Big-Cap Live Checker", page_icon="📈", layout="wide")

SYMBOLS = ["AAPL", "NVDA", "MSFT", "AMZN", "META", "TSLA"]
TF_SECONDS = {"M1": 60, "M5": 300, "M15": 900}

class FinnhubStream:
    def __init__(self, token):
        self.token = token
        self.lock = threading.Lock()
        self.trades = {s: deque(maxlen=20000) for s in SYMBOLS}
        self.running = False
        self.error = None

    def on_open(self, ws):
        for symbol in SYMBOLS:
            ws.send(json.dumps({"type": "subscribe", "symbol": symbol}))

    def on_message(self, ws, message):
        try:
            payload = json.loads(message)
            if payload.get("type") != "trade":
                return
            with self.lock:
                for item in payload.get("data", []):
                    s = item.get("s")
                    p = item.get("p")
                    t = item.get("t")
                    v = item.get("v", 0)
                    if s in self.trades and p is not None and t is not None:
                        self.trades[s].append((t/1000.0, float(p), float(v or 0)))
        except Exception as e:
            self.error = str(e)

    def on_error(self, ws, error):
        self.error = str(error)

    def on_close(self, ws, code, msg):
        self.running = False

    def start(self):
        if self.running:
            return
        self.running = True
        url = f"wss://ws.finnhub.io?token={self.token}"
        self.ws = websocket.WebSocketApp(
            url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        threading.Thread(
            target=lambda: self.ws.run_forever(ping_interval=20, ping_timeout=10),
            daemon=True,
        ).start()

    def snapshot(self):
        with self.lock:
            return {s: list(v) for s, v in self.trades.items()}

@st.cache_resource(show_spinner=False)
def get_stream(token):
    s = FinnhubStream(token)
    s.start()
    return s

def stats(trades, seconds, neutral_pct):
    if not trades:
        return None
    buckets = defaultdict(list)
    for ts, price, volume in trades:
        k = int(ts // seconds) * seconds
        buckets[k].append((ts, price, volume))
    k = sorted(buckets)[-1]
    arr = buckets[k]
    open_p = arr[0][1]
    last_p = arr[-1][1]
    move = (last_p / open_p - 1) * 100 if open_p else 0
    if move > neutral_pct:
        signal = "LONG"
    elif move < -neutral_pct:
        signal = "SHORT"
    else:
        signal = "NEUTRAL"
    age = max(0, time.time() - arr[-1][0])
    return last_p, move, signal, age

st.title("Big-Cap Live Checker")
st.caption("Kostenlose V1 · Live-Ticks · M1 / M5 / M15")

with st.sidebar:
    token = st.text_input("Finnhub API-Key", type="password")
    timeframe = st.radio("Zeiteinheit", ["M1", "M5", "M15"], horizontal=True)
    neutral_pct = st.slider("Neutral-Zone (%)", 0.00, 0.30, 0.03, 0.01)
    refresh = st.select_slider("Aktualisierung (Sek.)", [1,2,3,5,10], value=2)

if not token:
    st.info("Links den kostenlosen Finnhub-API-Key eintragen.")
    st.stop()

stream = get_stream(token)
time.sleep(0.2)
snap = stream.snapshot()
seconds = TF_SECONDS[timeframe]

rows = []
for s in SYMBOLS:
    x = stats(snap.get(s, []), seconds, neutral_pct)
    if x is None:
        rows.append([s, "⚪ WARTEN", "—", "—", "noch kein Tick"])
    else:
        last_p, move, signal, age = x
        icon = {"LONG":"🟢", "SHORT":"🔴", "NEUTRAL":"🟡"}[signal]
        rows.append([s, f"{icon} {signal}", f"{last_p:,.2f}", f"{move:+.3f}%", f"{age:.0f} s"])

df = pd.DataFrame(rows, columns=["Symbol", "Signal", "Kurs", f"{timeframe} %", "Datenalter"])

long_n = sum("LONG" in s for s in df["Signal"])
short_n = sum("SHORT" in s for s in df["Signal"])
neutral_n = sum("NEUTRAL" in s for s in df["Signal"])

if long_n >= 5:
    overall = f"🟢 DEUTLICH LONG · {long_n}/6"
elif short_n >= 5:
    overall = f"🔴 DEUTLICH SHORT · {short_n}/6"
elif long_n >= 4:
    overall = f"🟢 EHER LONG · {long_n}/6"
elif short_n >= 4:
    overall = f"🔴 EHER SHORT · {short_n}/6"
else:
    overall = f"🟡 GEMISCHT · L {long_n} / S {short_n} / N {neutral_n}"

st.metric("Gesamtbild", overall)
st.dataframe(df, use_container_width=True, hide_index=True)

st.warning(
    "V1 bewertet nur die Richtung der aktuell laufenden M1/M5/M15-Kerze. "
    "Prüfe immer das Datenalter. Außerhalb aktiver US-Handelszeiten können keine neuen Aktien-Ticks eintreffen."
)

st.markdown(
    f"""<script>
    setTimeout(function(){{window.parent.location.reload();}}, {int(refresh*1000)});
    </script>""",
    unsafe_allow_html=True
)
