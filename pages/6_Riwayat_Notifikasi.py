import sqlite3
import pandas as pd
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning("⚠️ Anda belum login. Silakan kembali ke halaman utama.")
  st.stop()

st.set_page_config(
    page_title="Riwayat Pengiriman Notifikasi", page_icon="📜", layout="wide"
)

conn = sqlite3.connect("database_spse.db", check_same_thread=False)
cursor = conn.cursor()

# Pastikan tabel log tersedia
cursor.execute("""
CREATE TABLE IF NOT EXISTS tabel_log_notifikasi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    waktu TEXT,
    kategori_paket TEXT,
    kode_paket TEXT,
    penerima TEXT,
    tujuan TEXT,
    media TEXT,
    status TEXT,
    keterangan TEXT
)
""")
conn.commit()

st.title("📜 Riwayat & Log Pengiriman Notifikasi (Email & WhatsApp)")
st.markdown("---")

query_log = "SELECT * FROM tabel_log_notifikasi ORDER BY id DESC"
df_log = pd.read_sql_query(query_log, conn)

if not df_log.empty:
  c1, c2 = st.columns(2)
  filter_media = c1.selectbox(
      "Filter Berdasarkan Media:", ["Semua", "Email", "WhatsApp"]
  )
  filter_status = c2.selectbox(
      "Filter Berdasarkan Status:", ["Semua", "Berhasil", "Gagal"]
  )

  if filter_media != "Semua":
    df_log = df_log[df_log["media"] == filter_media]
  if filter_status != "Semua":
    df_log = df_log[df_log["status"] == filter_status]

  st.subheader("📋 Tabel Riwayat Log Pengiriman")
  st.dataframe(
      df_log,
      column_config={
          "id": "ID",
          "waktu": "Waktu Pengiriman",
          "kategori_paket": "Kategori",
          "kode_paket": "Kode Paket",
          "penerima": "Target Penerima",
          "tujuan": "Alamat / No. HP Tujuan",
          "media": "Media",
          "status": "Status",
          "keterangan": "Keterangan / Detail",
      },
      use_container_width=True,
      hide_index=True,
  )

  st.markdown("---")
  col_b1, col_b2 = st.columns(2)
  if col_b1.button("🗑️ Bersihkan Seluruh Riwayat Log", type="secondary"):
    cursor.execute("DELETE FROM tabel_log_notifikasi")
    conn.commit()
    st.success("Riwayat log berhasil dibersihkan!")
    st.rerun()

else:
  st.info(
      "Belum ada riwayat pengiriman notifikasi yang tercatat. Silakan"
      " lakukan pengiriman pesan melalui halaman Tender, Non-Tender, atau"
      " E-Purchasing terlebih dahulu."
  )
