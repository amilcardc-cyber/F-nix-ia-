import time
import requests
import pandas as pd
import numpy as np
import streamlit as st

BASE = "https://fapi.binance.com"
TIMEOUT = 12

st.set_page_config(page_title="FÉNIX AI TRADER", page_icon="🔥", layout="wide")
st.title("🔥 FÉNIX AI TRADER")
st.caption("Módulo 1 · Escáner de oportunidades Binance Futures USDT-M · Solo lectura")

st.warning(
    "Este módulo NO abre operaciones ni necesita claves API. "
    "Es un escáner inicial para observar el mercado. Las señales son indicadores técnicos, "
    "no predicciones ni garantías de rentabilidad."
)

@st.cache_data(ttl=300)
def get_usdt_perpetual_symbols():
    r = requests.get(f"{BASE}/fapi/v1/exchangeInfo", timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    return {
        x["symbol"] for x in data["symbols"]
        if x.get("quoteAsset") == "USDT"
        and x.get("contractType") == "PERPETUAL"
        and x.get("status") == "TRADING"
    }

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def analyze_symbol(symbol, interval):
    r = requests.get(
        f"{BASE}/fapi/v1/klines",
        params={"symbol": symbol, "interval": interval, "limit": 220},
        timeout=TIMEOUT
    )
    r.raise_for_status()
    rows = r.json()
    if len(rows) < 205:
        return None

    df = pd.DataFrame(rows, columns=[
        "open_time","open","high","low","close","volume","close_time",
        "quote_volume","trades","taker_buy_base","taker_buy_quote","ignore"
    ])
    for c in ["open","high","low","close","volume","quote_volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    close = df["close"]
    df["ema9"] = ema(close, 9)
    df["ema21"] = ema(close, 21)
    df["ema200"] = ema(close, 200)
    df["rsi"] = rsi(close)
    df["vol_avg20"] = df["volume"].rolling(20).mean()
    last = df.iloc[-1]
    prev = df.iloc[-2]

    if pd.isna(last["ema200"]) or pd.isna(last["rsi"]) or not last["vol_avg20"]:
        return None

    vol_ratio = float(last["volume"] / last["vol_avg20"]) if last["vol_avg20"] else 0
    change = float((last["close"] / prev["close"] - 1) * 100)
    trend_up = last["close"] > last["ema200"] and last["ema9"] > last["ema21"]
    trend_down = last["close"] < last["ema200"] and last["ema9"] < last["ema21"]

    long_score = 0
    short_score = 0
    long_score += 1 if trend_up else 0
    short_score += 1 if trend_down else 0
    long_score += 1 if 45 <= last["rsi"] <= 68 else 0
    short_score += 1 if 32 <= last["rsi"] <= 55 else 0
    long_score += 1 if vol_ratio >= 1.5 and change > 0 else 0
    short_score += 1 if vol_ratio >= 1.5 and change < 0 else 0
    long_score += 1 if change > 0 else 0
    short_score += 1 if change < 0 else 0

    if long_score >= 3 and long_score > short_score:
        signal = "VIGILAR LONG"
        score = long_score
    elif short_score >= 3 and short_score > long_score:
        signal = "VIGILAR SHORT"
        score = short_score
    else:
        signal = "SIN SEÑAL"
        score = max(long_score, short_score)

    return {
        "Símbolo": symbol,
        "Señal": signal,
        "Puntaje": f"{score}/4",
        "Precio": float(last["close"]),
        "RSI": round(float(last["rsi"]), 1),
        "Volumen x promedio": round(vol_ratio, 2),
        "Cambio última vela %": round(change, 3),
        "Tendencia": "Alcista" if trend_up else ("Bajista" if trend_down else "Mixta"),
    }

def scan(interval, max_symbols, min_quote_volume):
    symbols = get_usdt_perpetual_symbols()
    tick = requests.get(f"{BASE}/fapi/v1/ticker/24hr", timeout=TIMEOUT)
    tick.raise_for_status()
    tickers = tick.json()

    candidates = []
    for t in tickers:
        sym = t.get("symbol")
        if sym in symbols:
            qv = float(t.get("quoteVolume", 0))
            if qv >= min_quote_volume:
                candidates.append((sym, qv))

    candidates.sort(key=lambda x: x[1], reverse=True)
    candidates = candidates[:max_symbols]

    results = []
    progress = st.progress(0)
    status = st.empty()
    for i, (sym, qv) in enumerate(candidates):
        status.write(f"Analizando {sym} ({i+1}/{len(candidates)})…")
        try:
            item = analyze_symbol(sym, interval)
            if item:
                item["Volumen 24h USDT"] = round(qv, 0)
                results.append(item)
        except Exception:
            pass
        progress.progress((i + 1) / max(1, len(candidates)))
        time.sleep(0.08)

    status.empty()
    progress.empty()
    return pd.DataFrame(results)

with st.sidebar:
    st.header("Configuración del escáner")
    interval = st.selectbox("Temporalidad", ["1m", "5m"], index=1)
    max_symbols = st.slider("Cantidad de altcoins a analizar", 10, 60, 25, 5)
    min_quote_volume = st.number_input(
        "Volumen mínimo 24h (USDT)", min_value=0, value=2_000_000, step=500_000
    )
    st.caption("El filtro de volumen reduce, pero no elimina, el riesgo de baja liquidez.")

if st.button("🔎 Escanear mercado ahora", type="primary"):
    try:
        with st.spinner("Consultando Binance Futures…"):
            result = scan(interval, max_symbols, min_quote_volume)
        st.session_state["results"] = result
        st.session_state["scan_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        st.error(f"No se pudo completar el escaneo: {e}")

if "results" in st.session_state:
    st.caption(f"Último escaneo: {st.session_state.get('scan_time', '—')} · Intervalo: {interval}")
    df = st.session_state["results"]
    if df.empty:
        st.info("No se obtuvieron datos. Probá nuevamente en unos minutos.")
    else:
        st.subheader("Oportunidades para investigar")
        filtered = df[df["Señal"] != "SIN SEÑAL"].sort_values(
            by=["Puntaje", "Volumen 24h USDT"], ascending=[False, False]
        )
        if filtered.empty:
            st.info("No hay señales que cumplan los filtros. FÉNIX no fuerza operaciones.")
        else:
            st.dataframe(filtered, use_container_width=True, hide_index=True)
        with st.expander("Ver todos los activos analizados"):
            st.dataframe(df.sort_values("Volumen 24h USDT", ascending=False),
                         use_container_width=True, hide_index=True)
else:
    st.info("Presioná «Escanear mercado ahora» para iniciar el primer análisis.")

st.divider()
st.markdown("**Próximo módulo:** gestión de riesgo y simulación de órdenes. La ejecución real se habilitará únicamente después de validar mínimos, comisiones, precisión de cantidades y protecciones de órdenes.")
st.caption("FÉNIX no es asesoramiento financiero. El mercado de futuros puede provocar la pérdida total del capital.")
