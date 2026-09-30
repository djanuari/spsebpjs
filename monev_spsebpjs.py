import io
import sqlite3
import pandas as pd
import streamlit as st

# Import fungsi sinkronisasi dari modul eksternal api_connector.py
from api_connector import sinkronisasi_database_spse

# Konfigurasi Halaman Utama
st.set_page_config(
    page_title="Monev SPSE & Kepatuhan BPJS", page_icon="📊", layout="wide"
)

# ---------------------------------------------------------
# SISTEM LOGIN SEDERHANA (Opsional, sesuaikan jika sudah ada)
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
      # Ubah password atau kredensial sesuai kebutuhan Anda
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

# Koneksi ke database lokal
DB_PATH = "database_spse.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)

# Informasi Ringkas / Statistik Singkat
col_s1, col_s2, col_s3 = st.columns(3)
try:
  df_t_count = pd.read_sql_query("SELECT COUNT(*) as total FROM tabel_tender", conn).iloc[0]["total"]
except:
  df_t_count = 0

try:
  df_nt_count = pd.read_sql_query("SELECT COUNT(*) as total FROM tabel_nontender", conn).iloc[0]["total"]
except:
  df_nt_count = 0

try:
  df_ep_count = pd.read_sql_query("SELECT COUNT(*) as total FROM tabel_epurchasing", conn).iloc[0]["total"]
except:
  df_ep_count = 0

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
    " terbaru langsung dari server SPSE / API Eksternal."
)

if st.button("🔄 Tarik Data Terbaru via API SPSE", type="primary", key="btn_tarik_api"):
  with st.spinner("Sedang menghubungkan ke server API SPSE dan memproses data..."):
    # Memanggil fungsi dari api_connector.py
    jumlah_data = sinkronisasi_database_spse()

    if jumlah_data > 0:
      st.success(
          f"✅ Berhasil! Sinkronisasi selesai. Sebanyak **{jumlah_data} data paket**"
          " berhasil diperbarui ke database lokal."
      )
      
      # Simpan status sukses di session_state agar tombol unduh tetap tampil setelah sinkronisasi
      st.session_state["sync_success"] = True
    else:
      st.warning("⚠️ Sinkronisasi selesai, namun tidak ada data baru yang diproses.")
      st.session_state["sync_success"] = False

# =========================================================
# KONTROL TOMBOL UNDUH INSTAN (MUNCUL SETELAH TARIK DATA BERHASIL)
# =========================================================
if st.session_state.get("sync_success", False):
  st.markdown("---")
  st.info("📥 Arsip data hasil tarikan API terbaru siap diunduh.")

  try:
    # Mengambil gabungan atau data terbaru dari database untuk di-export ke Excel
    query_gabungan = """
        SELECT 'Tender' as kategori, kode_tender as kode_paket, nama_paket, jenis_pengadaan, satuan_kerja, nilai_pagu as nilai, status_bpjs FROM tabel_tender
        UNION ALL
        SELECT 'Non-Tender' as kategori, kode_nontender as kode_paket, nama_nontender as nama_paket, jenis_pengadaan, satuan_kerja, nilai_hps as nilai, status_bpjs FROM tabel_nontender
    """
    df_hasil_tarikan = pd.read_sql_query(query_gabungan, conn)

    if not df_hasil_tarikan.empty:
      # Buat file excel virtual di memori menggunakan io.BytesIO
      output_excel = io.BytesIO()
      with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
        df_hasil_tarikan.to_excel(
            writer, sheet_name="Hasil Sinkronisasi API", index=False
        )
      excel_bytes = output_excel.getvalue()

      # Tombol unduh instan
      st.download_button(
          label="📥 Unduh Hasil Tarikan API ke Format Excel (.xlsx)",
          data=excel_bytes,
          file_name="Hasil_Tarikan_Data_SPSE.xlsx",
          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
          type="secondary",
          key="btn_download_excel_api",
      )
  except Exception as e:
    st.error(f"Gagal menyiapkan file unduhan: {e}")

st.markdown("---")
st.markdown(
    "💡 *Silakan navigasikan ke menu halaman di sidebar (Tender, Non-Tender, atau"
    " E-Purchasing) untuk melihat detail lengkap, melakukan verifikasi"
    " kepatuhan BPJS, dan mengirimkan notifikasi.*"
)
