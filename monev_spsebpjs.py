import pandas as pd
import streamlit as st

# Import fungsi dari api_connector.py
from api_connector import get_all_spse_data, sinkronisasi_database_spse

# Konfigurasi Halaman Utama
st.set_page_config(
    page_title="Monev SPSE & Kepatuhan BPJS", page_icon="📊", layout="wide"
)

# ---------------------------------------------------------
# SISTEM LOGIN SEDERHANA
# ---------------------------------------------------------
if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
  st.title("🔐 Login Sistem Monitoring SPSE & BPJS")
  st.markdown("---")
  with st.form("form_login"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submit_login = st.form_submit_button("Masuk", type="primary")

    if submit_login:
      if username == "admin" and password == "admin123":
        st.session_state["logged_in"] = True
        st.success("Login berhasil! Memuat aplikasi...")
        st.rerun()
      else:
        st.error("Username atau Password salah!")
  st.stop()

# ---------------------------------------------------------
# HALAMAN UTAMA SETELAH LOGIN
# ---------------------------------------------------------
st.title("📊 Beranda Utama - Monitoring SPSE & Kepatuhan BPJS")
st.markdown(
    "Selamat datang di Panel Pengendalian Pengadaan Barang dan Jasa Pemerintah"
    " Kota Kendari."
)
st.markdown("---")

# Ambil seluruh data dari Supabase Cloud melalui api_connector
df_all = get_all_spse_data()

# Hitung jumlah data berdasarkan kategori
if not df_all.empty and "kategori" in df_all.columns:
  df_t_count = len(df_all[df_all["kategori"].str.lower() == "tender"])
  df_nt_count = len(df_all[df_all["kategori"].str.lower() == "non-tender"])
  df_ep_count = len(df_all[df_all["kategori"].str.lower() == "e-purchasing"])
else:
  df_t_count = 0
  df_nt_count = 0
  df_ep_count = 0

# Informasi Ringkas / Statistik Singkat
col_s1, col_s2, col_s3 = st.columns(3)
col_s1.metric("Total Paket Tender", f"{df_t_count} Paket")
col_s2.metric("Total Paket Non-Tender", f"{df_nt_count} Paket")
col_s3.metric("Total Paket E-Purchasing", f"{df_ep_count} Paket")

st.markdown("---")

# ---------------------------------------------------------
# MENU SINKRONISASI API SPSE & TOMBOL UNDUH HASIL TARIKAN
# ---------------------------------------------------------
st.subheader("🔄 Sinkronisasi Data Otomatis via API SPSE")
st.markdown(
    "Gunakan tombol di bawah untuk menarik pembaruan data paket pengadaan"
    " terbaru langsung dari server SPSE / API Eksternal ke Supabase Cloud."
)

if st.button(
    "🔄 Tarik Data Terbaru via API SPSE", type="primary", key="btn_tarik_api"
):
  with st.spinner(
      "Sedang menghubungkan ke server API SPSE dan memproses data..."
  ):
    # Memanggil fungsi dari api_connector.py
    jumlah_data = sinkronisasi_database_spse()

    if jumlah_data > 0:
      st.success(
          f"✅ Berhasil! Sinkronisasi selesai. Sebanyak **{jumlah_data} data paket**"
          " berhasil diperbarui ke database cloud."
      )
      st.session_state["sync_success"] = True
    else:
      st.warning(
          "⚠️ Sinkronisasi selesai, namun tidak ada data baru yang diproses."
      )
      st.session_state["sync_success"] = False

# =========================================================
# KONTROL TOMBOL UNDUH INSTAN (FORMAT CSV)
# =========================================================
if st.session_state.get("sync_success", False):
  st.markdown("---")
  st.info("📥 Arsip data hasil tarikan API terbaru siap diunduh.")

  try:
    df_fresh = get_all_spse_data()
    if not df_fresh.empty:
      csv_data = df_fresh.to_csv(index=False).encode("utf-8")

      st.download_button(
          label="📥 Unduh Hasil Tarikan API ke Format CSV (.csv)",
          data=csv_data,
          file_name="Hasil_Tarikan_Data_SPSE.csv",
          mime="text/csv",
          type="secondary",
          key="btn_download_csv_api",
      )
    else:
      st.info("Tidak ada data yang tersedia untuk diunduh.")
  except Exception as e:
    st.error(f"Gagal menyiapkan file unduhan: {e}")

st.markdown("---")
st.markdown(
    "💡 *Silakan navigasikan ke menu halaman di sidebar (Tender, Non-Tender, atau"
    " E-Purchasing) untuk melihat detail lengkap, melakukan verifikasi"
    " kepatuhan BPJS, dan mengirimkan notifikasi.*"
)
