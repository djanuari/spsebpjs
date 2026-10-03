from api_connector import get_all_spse_data
import pandas as pd
import plotly.express as px
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning("⚠️ Anda belum login. Silakan kembali ke halaman utama.")
  st.stop()

st.set_page_config(
    page_title="Grafik & Statistik Kepatuhan BPJS", page_icon="📊", layout="wide"
)

st.title("📊 Dashboard Grafik & Statistik Kepatuhan BPJS")
st.markdown("---")

# Memuat seluruh data dari Supabase Cloud
df_all = get_all_spse_data()

# Memisahkan data berdasarkan kategori
if not df_all.empty and "kategori" in df_all.columns:
  df_tender = df_all[df_all["kategori"].str.lower() == "tender"]
  df_nontender = df_all[df_all["kategori"].str.lower() == "non-tender"]
  df_ep = df_all[df_all["kategori"].str.lower() == "e-purchasing"]
else:
  df_tender = pd.DataFrame()
  df_nontender = pd.DataFrame()
  df_ep = pd.DataFrame()

# Layout Statistik Ringkas (Metrics)
col1, col2, col3 = st.columns(3)

total_tender = len(df_tender)
total_nontender = len(df_nontender)
total_ep = len(df_ep)

col1.metric("🏗️ Total Paket Tender", f"{total_tender} Paket")
col2.metric("📋 Total Paket Non-Tender", f"{total_nontender} Paket")
col3.metric("🛒 Total Paket E-Purchasing", f"{total_ep} Paket")

st.markdown("---")

# BAGIAN 1: GRAFIK PIE STATUS KEPATUHAN BPJS
st.subheader("📈 Distribusi Status Kepatuhan BPJS per Kategori Paket")
c_g1, c_g2, c_g3 = st.columns(3)


def render_pie_chart(df_sub, title_text, key_name):
  st.markdown(f"**{title_text}**")
  if not df_sub.empty and "status_kepatuhan" in df_sub.columns:
    count_data = df_sub["status_kepatuhan"].value_counts().reset_index()
    count_data.columns = ["Status", "Jumlah"]
    fig = px.pie(
        count_data,
        names="Status",
        values="Jumlah",
        hole=0.4,
        color_discrete_sequence=["#FF4B4B", "#00CC96"],
    )
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=True)
    st.plotly_chart(fig, use_container_width=True, key=key_name)
  else:
    st.info("Belum ada data.")


with c_g1:
  render_pie_chart(df_tender, "Tender / Seleksi", "grafik_pie_tender")

with c_g2:
  render_pie_chart(df_nontender, "Non-Tender", "grafik_pie_nontender")

with c_g3:
  render_pie_chart(df_ep, "E-Purchasing / Mini Kompetisi", "grafik_pie_epurchasing")

st.markdown("---")

# BAGIAN 2: GRAFIK BATANG BERDASARKAN KETERANGAN / JENIS
st.subheader("📊 Perbandingan Volume Paket Berdasarkan Kategori & Keterangan")

try:
  if not df_all.empty:
    fig_bar = px.histogram(
        df_all,
        x="kategori",
        color="status_kepatuhan",
        barmode="group",
        title="Distribusi Status Kepatuhan Berdasarkan Kategori Paket",
        labels={"kategori": "Kategori Paket", "count": "Jumlah Paket"},
        color_discrete_sequence=["#FF4B4B", "#00CC96"],
    )
    fig_bar.update_layout(xaxis_tickangle=0)
    st.plotly_chart(
        fig_bar, use_container_width=True, key="grafik_histogram_kepatuhan"
    )
  else:
    st.info("Data belum mencukupi untuk ditampilkan dalam grafik.")
except Exception as e:
  st.warning(f"Gagal memuat grafik statistik gabungan: {e}")
