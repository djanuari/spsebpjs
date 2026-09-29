import sqlite3
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning("⚠️ Anda belum login. Silakan kembali ke halaman utama.")
  st.stop()

st.set_page_config(
    page_title="Grafik & Statistik Kepatuhan BPJS", page_icon="📊", layout="wide"
)

# Koneksi Database SQLite
conn = sqlite3.connect("database_spse.db", check_same_thread=False)

st.title("📊 Dashboard Grafik & Statistik Kepatuhan BPJS")
st.markdown("---")

# Memuat data dari masing-masing tabel dengan penanganan aman
try:
  df_tender = pd.read_sql_query("SELECT * FROM tabel_tender", conn)
except Exception:
  df_tender = pd.DataFrame()

try:
  df_nontender = pd.read_sql_query("SELECT * FROM tabel_nontender", conn)
except Exception:
  df_nontender = pd.DataFrame()

try:
  df_ep = pd.read_sql_query("SELECT * FROM tabel_epurchasing", conn)
except Exception:
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

# Bagian Grafik Menggunakan Plotly dengan Key Unik & Aman dari Glitch
c_g1, c_g2 = st.columns(2)

with c_g1:
  st.subheader("📈 Status Kepatuhan BPJS (Tender)")
  if not df_tender.empty and "status_bpjs" in df_tender.columns:
    count_tender = df_tender["status_bpjs"].value_counts().reset_index()
    count_tender.columns = ["Status", "Jumlah"]
    fig_tender = px.pie(
        count_tender,
        names="Status",
        values="Jumlah",
        title="Distribusi BPJS Tender",
        hole=0.4,
        color_discrete_sequence=["#FF4B4B", "#00CC96"],
    )
    # Argumen use_container_width dan key unik mencegah error transisi
    st.plotly_chart(fig_tender, use_container_width=True, key="grafik_pie_tender")
  else:
    st.info("Belum ada data status BPJS untuk Tender.")

with c_g2:
  st.subheader("📈 Status Kepatuhan BPJS (Non-Tender)")
  if not df_nontender.empty and "status_bpjs" in df_nontender.columns:
    count_nt = df_nontender["status_bpjs"].value_counts().reset_index()
    count_nt.columns = ["Status", "Jumlah"]
    fig_nt = px.pie(
        count_nt,
        names="Status",
        values="Jumlah",
        title="Distribusi BPJS Non-Tender",
        hole=0.4,
        color_discrete_sequence=["#FF4B4B", "#00CC96"],
    )
    st.plotly_chart(fig_nt, use_container_width=True, key="grafik_pie_nontender")
  else:
    st.info("Belum ada data status BPJS untuk Non-Tender.")

st.markdown("---")

# Grafik Batang Berdasarkan Jenis Pengadaan
st.subheader("📊 Perbandingan Volume Berdasarkan Jenis Pengadaan")

try:
  # Gabungkan data untuk analisis jenis pengadaan jika kolomnya tersedia
  list_gabungan = []
  if not df_tender.empty and "jenis_pengadaan" in df_tender.columns:
    t_sub = df_tender[["jenis_pengadaan"]].copy()
    t_sub["Kategori"] = "Tender"
    list_gabungan.append(t_sub)

  if not df_nontender.empty and "jenis_pengadaan" in df_nontender.columns:
    nt_sub = df_nontender[["jenis_pengadaan"]].copy()
    nt_sub["Kategori"] = "Non-Tender"
    list_gabungan.append(nt_sub)

  if not df_ep.empty and "jenis_pengadaan" in df_ep.columns:
    ep_sub = df_ep[["jenis_pengadaan"]].copy()
    ep_sub["Kategori"] = "E-Purchasing"
    list_gabungan.append(ep_sub)

  if len(list_gabungan) > 0:
    df_all = pd.concat(list_gabungan, ignore_index=True)
    fig_bar = px.histogram(
        df_all,
        x="jenis_pengadaan",
        color="Kategori",
        barmode="group",
        title="Jumlah Paket per Jenis Pengadaan",
        labels={
            "jenis_pengadaan": "Jenis Pengadaan",
            "count": "Jumlah Paket",
        },
    )
    fig_bar.update_layout(xaxis_tickangle=-15)
    st.plotly_chart(
        fig_bar, use_container_width=True, key="grafik_histogram_pengadaan"
    )
  else:
    st.info("Data jenis pengadaan belum mencukupi untuk ditampilkan dalam grafik.")
except Exception as e:
  st.warning(f"Gagal memuat grafik statistik gabungan: {e}")
