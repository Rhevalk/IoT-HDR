from datetime import datetime
import streamlit as st
import pandas as pd
import json

from db.database import get_all_data
from ui.icons import icon

from streamlit_autorefresh import st_autorefresh

import components
import config

st.set_page_config(page_title="CIN Farm", layout="wide")

#config.setup()

components.navbar()


# =========================
# LOAD DATA (NO SQL HERE)
# =========================
def load_data():
    rows = get_all_data(200)

    records = []

    for device_id, data, timestamp in rows:
        try:
            parsed = json.loads(data)

            records.append({
                "device": device_id,
                "temp": parsed.get("temp"),
                "hum": parsed.get("hum"),
                "time": timestamp
            })
        except:
            pass

    return pd.DataFrame(records)


# Setup
df = load_data()

if df.empty:
    st.warning("Belum ada data masuk...")
    st.stop()

devices = sorted(df["device"].unique())

st.title("⚙ Edit Info Dashboard")

with st.container(border=True):
    components.cardInfoTanaman_edit(
        device_id="esp-farm-1", pond_id="tanaman", title="Hidroponik"
    )

with st.container(border=True):
    components.cardInfoIkan_edit(
        device_id="esp-ikan-1", pond_id="k1", title="Kolam Ikan 1"
    )

with st.container(border=True):
    components.cardInfoIkan_edit(
        device_id="esp-ikan-1", pond_id="k2", title="Kolam Ikan 2"
    )

with st.container(border=True):
    components.cardInfoIkan_edit(
        device_id="esp-ikan-1", pond_id="k3", title="Kolam Ikan 3"
    )

with st.container(border=True):
    components.cardInfoIkan_edit(
        device_id="esp-ikan-1", pond_id="k4", title="Kolam Ikan 4"
    )
