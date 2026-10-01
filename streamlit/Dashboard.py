import json
from datetime import datetime
import altair as alt
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

import components
import config
from db.database import get_data_by_range
from ui.icons import icon

# Config Halaman
st.set_page_config(page_title="CIN Farm", layout="wide")

# Autorefresh setiap 5 detik
count = st_autorefresh(interval=5000, key="slider_refresh")

# config.setup()
components.navbar()

# =========================================================
# CONFIG RENTANG WAKTU & INTERVAL AGREGASI (RESAMPLE)
# =========================================================
TIME_RANGES = {
    "1 Hari Terakhir": {
        "modifier": "-1 day",
        "resample": "5min",
        "fmt": "%H:%M",
    },
    "1 Minggu Terakhir": {
        "modifier": "-7 days",
        "resample": "30min",
        "fmt": "%d %b %H:%M",
    },
    "1 Bulan Terakhir": {
        "modifier": "-1 month",
        "resample": "2h",
        "fmt": "%d %b",
    },
    "2 Bulan Terakhir": {
        "modifier": "-2 months",
        "resample": "6h",
        "fmt": "%d %b",
    },
    "Semua Data": {"modifier": "-10 years", "resample": "1D", "fmt": "%d %b %Y"},
}


# =========================================================
# HELPER: GRAFIK ALTAIR DINAMIS
# =========================================================
def create_clean_chart(data, title="", time_format="%H:%M", height=320):
    """Membuat grafik garis Altair dinamis tanpa merusak susunan layout."""
    value_vars = [col for col in data.columns if col not in ["time", "device"]]

    if not value_vars:
        return alt.Chart(pd.DataFrame()).mark_text().properties(title="Data Kosong")

    df_melted = data.melt(
        id_vars=["time"],
        value_vars=value_vars,
        var_name="Sensor",
        value_name="Nilai",
    )

    sensor_map = {
        "temp": "Suhu (°C)",
        "hum": "Kelembaban (%)",
        "temp1": "Kolam 1 (°C)",
        "temp2": "Kolam 2 (°C)",
        "temp3": "Kolam 3 (°C)",
        "temp4": "Kolam 4 (°C)",
    }

    df_melted["SensorLabel"] = df_melted["Sensor"].map(lambda x: sensor_map.get(x, x))

    color_domain = [sensor_map.get(k, k) for k in value_vars]
    color_palette = ["#FF4B4B", "#1C83E1", "#00C04D", "#FFA500", "#9B59B6", "#E67E22"]
    color_range = color_palette[: len(value_vars)]

    chart = (
        alt.Chart(df_melted)
        .mark_line(interpolate="monotone", strokeWidth=2)
        .encode(
            x=alt.X(
                "time:T",
                title=None,
                axis=alt.Axis(
                    format=time_format,
                    labelAngle=0,
                    grid=True,
                    ticks=True,
                    tickCount=8,
                ),
            ),
            y=alt.Y("Nilai:Q", title=None),
            color=alt.Color(
                "SensorLabel:N",
                scale=alt.Scale(domain=color_domain, range=color_range),
                legend=alt.Legend(
                    orient="bottom",
                    title=None,
                    direction="horizontal",
                ),
            ),
            tooltip=[
                alt.Tooltip("time:T", title="Waktu", format="%d %b %Y - %H:%M:%S"),
                alt.Tooltip("SensorLabel:N", title="Sensor"),
                alt.Tooltip("Nilai:Q", title="Nilai", format=".1f"),
            ],
        )
        .properties(height=height, title=title)
        .interactive()
    )

    return chart


# =========================================================
# LOAD DATA FUNCTION WITH CACHE
# =========================================================
@st.cache_data(ttl=5)
def load_data_by_range(modifier):
    rows = get_data_by_range(modifier=modifier)

    records = []
    for device_id, data, timestamp in rows:
        try:
            parsed = json.loads(data) if isinstance(data, str) else data

            # Parse UTC timestamp dan konversi ke Asia/Jakarta (WIB)
            dt_utc = pd.to_datetime(timestamp, utc=True)
            dt_wib = dt_utc.tz_convert("Asia/Jakarta").tz_localize(None)

            record = {
                "device": device_id,
                "time": dt_wib,
            }

            for key in ["temp", "hum", "temp1", "temp2", "temp3", "temp4"]:
                if key in parsed and parsed[key] is not None:
                    record[key] = float(parsed[key])

            records.append(record)
        except Exception:
            pass

    return pd.DataFrame(records)


# Load default data awal
df_init = load_data_by_range("-1 day")

if df_init.empty:
    st.warning("Belum ada data telemetry masuk...")
    st.stop()

# =========================================================
# LAYOUT UTAMA (UI)
# =========================================================
images = [
    "https://placehold.co/800x450/1E2129/white?text=Slide+1",
    "https://placehold.co/800x450/FF4B4B/white?text=Slide+2",
    "https://placehold.co/800x450/31333F/white?text=Slide+3",
]
current_img = images[count % len(images)]

col_left, col_mid, col_right = st.columns([1.5, 2, 1.5])

# --- KOLOM KIRI (ESP-FARM-1) ---
device_farm = "esp-farm-1"
with col_left:
    with st.container(border=True):
        # Tampilan Hidroponik
        components.cardInfoTanaman(
            device_id="esp-farm-1", pond_id="tanaman", title="Hidroponik"
        )




    df_farm = df_init[df_init["device"] == device_farm]
    
    if not df_farm.empty:
        latest_farm = df_farm.iloc[-1]
        temp_val = latest_farm.get("temp", "-")
        hum_val = latest_farm.get("hum", "-")
    else:
        temp_val, hum_val = "-", "-"

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("### Temperatur")
            st.markdown(f"## {temp_val} °C")

    with col2:
        with st.container(border=True):
            st.markdown("### Humidity")
            st.markdown(f"## {hum_val} %")

    # CONTAINER GRAFIK UTAMA ESP-FARM-1
    with st.container(border=True):
        col_title, col_select = st.columns([1, 0.6])

        with col_title:
            st.markdown(f"##### Device: {device_farm}")

        with col_select:
            selected_range_left = st.selectbox(
                "Rentang Waktu Left",
                options=list(TIME_RANGES.keys()),
                index=0,
                label_visibility="collapsed",
                key="select_range_left",
            )

        range_config_left = TIME_RANGES[selected_range_left]

        filtered_df_left = load_data_by_range(range_config_left["modifier"])
        filtered_farm = filtered_df_left[filtered_df_left["device"] == device_farm].copy()

        if not filtered_farm.empty:
            # Ambil kolom numerik yang valid saja
            valid_cols = [c for c in ["temp", "hum"] if c in filtered_farm.columns]
            
            chart_df_left = (
                filtered_farm.set_index("time")[valid_cols]
                .resample(range_config_left["resample"])
                .mean()
                .ffill()
                .bfill()
                .reset_index()
            )

            chart_left = create_clean_chart(
                chart_df_left,
                time_format=range_config_left["fmt"],
                height=360,
            )
            st.altair_chart(chart_left, use_container_width=True)
        else:
            st.info("Data esp-farm-1 tidak ditemukan")

# --- KOLOM TENGAH ---
with col_mid:
    with st.container(border=True):
        components.cardInfoIkan(
            device_id="esp-ikan-1", pond_id="k1", title="Kolam Ikan 1"
        )

    with st.container(border=True):
        components.cardInfoIkan(
            device_id="esp-ikan-1", pond_id="k2", title="Kolam Ikan 2"
        )

    st.image(current_img)

# --- KOLOM KANAN (ESP-IKAN-1) ---
device_ikan = "esp-ikan-1"
with col_right:
    with st.container(border=True):
        components.cardInfoIkan(
            device_id=device_ikan, pond_id="k3", title="Kolam Ikan 3"
        )

    with st.container(border=True):
        components.cardInfoIkan(
            device_id=device_ikan, pond_id="k4", title="Kolam Ikan 4"
        )

    # GRAFIK ESP-IKAN-1
    with st.container(border=True):
        col_title, col_select = st.columns([1, 0.6])

        with col_title:
            st.markdown(f"##### Device: {device_ikan}")

        with col_select:
            selected_range_right = st.selectbox(
                "Rentang Waktu Right",
                options=list(TIME_RANGES.keys()),
                index=0,
                label_visibility="collapsed",
                key="select_range_right",
            )

        range_config_right = TIME_RANGES[selected_range_right]

        filtered_df_right = load_data_by_range(range_config_right["modifier"])
        filtered_ikan = filtered_df_right[filtered_df_right["device"] == device_ikan].copy()

        if not filtered_ikan.empty:
            # Ambil kolom numerik temp1 - temp4 yang valid
            valid_cols_ikan = [c for c in ["temp1", "temp2", "temp3", "temp4"] if c in filtered_ikan.columns]

            chart_df_right = (
                filtered_ikan.set_index("time")[valid_cols_ikan]
                .resample(range_config_right["resample"])
                .mean()
                .ffill()
                .bfill()
                .reset_index()
            )

            chart_right = create_clean_chart(
                chart_df_right,
                time_format=range_config_right["fmt"],
                height=300,
            )
            st.altair_chart(chart_right, use_container_width=True)
        else:
            st.info("Data esp-ikan-1 tidak ditemukan")
