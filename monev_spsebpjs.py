from api_connector import get_all_spse_data
import pandas as pd
import streamlit as st

if "logged_in" not in st.session_state:
  st.session_state["logged_in"] = False

st.set_page_config(
    page_title="Monev SPSE & Kepatuhan BPJS", page_icon="🏛️", layout="wide"
)

# --- HALAMAN UTAMA LOGIN & DASHBOARD ---
st.title("🏛️ Sistem Monitoring Kepatuhan BPJS SPSE")
st.markdown("---")

if not st.session_state["logged_in"]:
  st.subheader("Silakan Login Terlebih Dahulu")
  with st.form("form_login"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submit_login = st.form_submit_button("Masuk", type="primary")

    if submit_login:
      if username == "admin" and password == "admin123":
        st.session_state["logged_in"] = True
        st.success("Login berhasil!")
        st.rerun()
      else:
        st.error("Username atau password salah!")
else:
  st.success("Anda berhasil masuk sebagai Administrator (Terhubung ke Cloud).")

  # Ambil data dari Supabase untuk menghitung statistik di beranda
  df_all = get_all_spse_data()

  total_tender = 0
  total_nontender = 0
  total_ep = 0

  if not df_all.empty and "kategori" in df_all.columns:
    total_tender = len(
        df_all[df_all["kategori"].str.lower() == "tender"]
    )
    total_nontender = len(
        df_all[df_all["kategori"].str.lower() == "non-tender"]
    )
    total_ep = len(
        df_all[df_all["kategori"].str.lower() == "e-purchasing"]
    )

  # Tampilan Statistik Ringkasan di Beranda
  col1, col2, col3 = st.columns(3)
  col1.metric("Total Paket Tender", f"{total_tender} Paket")
  col2.metric("Total Paket Non-Tender", f"{total_nontender} Paket")
  col3.metric("Total Paket E-Purchasing", f"{total_ep} Paket")

  st.markdown("---")
  st.subheader("🔄 Sinkronisasi Data Otomatis via API SPSE")
  st.markdown(
      "Gunakan tombol di bawah untuk menarik pembaruan data paket pengadaan"
      " terbaru langsung ke database Supabase Cloud."
  )

  # Tombol Sinkronisasi dengan Indikator Spinner yang Optimal
  if st.button("🔄 Tarik Data Terbaru via API SPSE", type="primary"):
    with st.spinner(
        "Sedang menyinkronkan data dengan server SPSE... Mohon tunggu"
        " sebentar."
    ):
      try:
        # Proses sinkronisasi data ditarik dari fungsi konektor cloud
        _ = get_all_spse_data()
        st.success(
            "✅ Sinkronisasi data SPSE berhasil diperbarui dari database"
            " cloud!"
        )
      except Exception as e:
        st.error(f"⚠️ Gagal melakukan sinkronisasi: {e}")

  # --- FITUR BACKUP DATABASE DI HALAMAN UTAMA ---
  st.markdown("---")
  st.subheader("💾 Backup & Ekspor Seluruh Database Cloud")
  st.markdown(
      "Gunakan tombol di bawah untuk mencadangkan seluruh data pengadaan"
      " (Tender, Non-Tender, dan E-Purchasing) langsung dari database Supabase"
      " ke format CSV."
  )

  if not df_all.empty:
    csv_backup = df_all.to_csv(index=False).encode("utf-8")
    nama_file_backup = (
        f"Backup_Database_SPSE_BPJS_{pd.Timestamp.today().strftime('%Y-%m-%d')}.csv"
    )

    st.download_button(
        label="📥 Unduh / Backup Seluruh Database ke CSV",
        data=csv_backup,
        file_name=nama_file_backup,
        mime="text/csv",
        type="primary",
    )
  else:
    st.info("Belum ada data di dalam database cloud untuk dicadangkan.")

  st.markdown("---")
  st.markdown("""
        ### 📂 Petunjuk Navigasi Menu:
        Silakan pilih menu di **sidebar (sebelah kiri)** untuk mengelola:
        - **Paket Tender**
        - **Paket Non Tender**
        - **E Purchasing**
        - **Import Data SPSE & Laporan**
    """)

  if st.button("🚪 Keluar (Logout)", type="secondary"):
    st.session_state["logged_in"] = False
    st.rerun()
