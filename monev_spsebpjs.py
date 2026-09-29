import sqlite3
import streamlit as st
from api_connector import sinkronisasi_database_spse

# Konfigurasi Halaman Utama
st.set_page_config(
    page_title="Dashboard Kepatuhan BPJS - Pemkot Kendari",
    page_icon="🛡️",
    layout="wide",
)

# Simulasi Status Login
if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = True

if not st.session_state.get("logged_in"):
  st.warning("⚠️ Silakan login terlebih dahulu.")
  st.stop()

st.title("🛡️ Sistem Pemantauan Kepatuhan BPJS Pengadaan Barang/Jasa")
st.markdown("### Pemerintah Kota Kendari")
st.markdown("---")

# Informasi Sambutan
st.info(
    "Selamat datang di Dashboard Utama. Gunakan menu di sebelah kiri (sidebar)"
    " untuk berpindah halaman ke data Tender, Non-Tender, E-Purchasing, Grafik"
    " Statistik, atau Riwayat Notifikasi."
)

st.markdown("---")

# 🔗 BAGIAN TOMBOL SINKRONISASI API SPSE
st.subheader("🔄 Sinkronisasi Otomatis via API SPSE Kota Kendari")
st.markdown(
    "Klik tombol di bawah ini untuk menarik data paket pengadaan terbaru secara"
    " langsung dari server resmi LPSE/SPSE menggunakan token API Anda."
)

if st.button("Tarik Data Terbaru via API SPSE", type="primary"):
  with st.spinner(
      "Sedang terhubung ke server SPSE dan menyinkronkan data..."
  ):
    try:
      total_sinkron = sinkronisasi_database_spse()
      if total_sinkron > 0:
        st.success(
            f"✅ Berhasil! Sinkronisasi selesai. Sebanyak {total_sinkron} data"
            " paket berhasil diperbarui ke database lokal."
        )
      else:
        st.warning(
            "⚠️ Koneksi berhasil, tetapi tidak ada data baru yang masuk atau"
            " periksa kembali format respons API."
        )
    except Exception as e:
      st.error(f"Gagal melakukan sinkronisasi: {e}")

st.markdown("---")
st.markdown(
    "**Catatan:** Pastikan file modul `api_connector.py` dan file konfigurasi"
    " token sudah berada di folder utama yang sama."
)
