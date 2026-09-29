import sqlite3
import pandas as pd
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning("⚠️ Anda belum login. Silakan kembali ke halaman utama.")
  st.stop()

st.set_page_config(
    page_title="Impor Data E-Purchasing", page_icon="📥", layout="wide"
)

# Koneksi Database SQLite
conn = sqlite3.connect("database_spse.db", check_same_thread=False)
cursor = conn.cursor()

# Pastikan tabel e-purchasing tersedia
cursor.execute("""
CREATE TABLE IF NOT EXISTS tabel_epurchasing (
    kode_paket TEXT PRIMARY KEY,
    kode_rup TEXT,
    nama_paket TEXT,
    pagu_paket REAL,
    hps_paket REAL,
    jenis_pengadaan TEXT,
    nama_pemenang TEXT,
    nilai_kontrak REAL,
    alamat_pemenang TEXT,
    email_pemenang TEXT,
    telp_pemenang TEXT,
    status_bpjs TEXT
)
""")
conn.commit()

st.title("📥 Impor Data Khusus E-Purchasing / Mini Kompetisi")
st.write(
    "Unggah file rekapitulasi data E-Purchasing (format `.xlsx`, `.xls`, atau"
    " `.csv`) sesuai dengan 11 kolom struktur yang ditentukan."
)
st.markdown("---")

# Widget unggah file khusus E-Purchasing
uploaded_file = st.file_uploader(
    "Pilih file Excel atau CSV E-Purchasing:", type=["xlsx", "xls", "csv"]
)

if uploaded_file is not None:
  try:
    # Baca file berdasarkan ekstensinya
    if uploaded_file.name.endswith(".csv"):
      df_import = pd.read_csv(uploaded_file)
    else:
      df_import = pd.read_excel(uploaded_file)

    # Normalisasi nama kolom (ubah ke huruf kecil & spasi jadi underscore agar seragam)
    df_import.columns = [
        str(c).strip().lower().replace(" ", "_") for c in df_import.columns
    ]

    st.subheader("👀 Pratinjau Data yang Diunggah:")
    st.dataframe(df_import.head(10), use_container_width=True)
    st.info(f"Total baris data dalam file: **{len(df_import)} baris**")

    st.markdown("---")

    # Tombol konfirmasi simpan ke database
    if st.button("🚀 Proses & Simpan ke Database E-Purchasing", type="primary"):
      with st.spinner("Sedang menyimpan data..."):
        try:
          df_import.to_sql(
              "tabel_epurchasing", conn, if_exists="append", index=False
          )
          st.success(
              "🎉 Berhasil! Seluruh data E-Purchasing telah diimpor ke"
              " database."
          )
        except Exception as db_err:
          st.error(
              f"Gagal menyimpan ke database. Pastikan 'kode_paket' unik dan belum"
              f" pernah diimpor sebelumnya. Detail error: {db_err}"
          )

  except Exception as e:
    st.error(f"Terjadi kesalahan saat membaca file. Detail: {e}")

else:
  st.markdown("""
        ### 📋 Panduan Format Kolom File E-Purchasing:
        Pastikan file Excel atau CSV Anda memiliki judul kolom dengan penamaan berikut:
        1. **`kode_rup`**
        2. **`kode_paket`** (Wajib unik sebagai Primary Key)
        3. **`nama_paket`**
        4. **`pagu_paket`**
        5. **`hps_paket`**
        6. **`jenis_pengadaan`**
        7. **`nama_pemenang`**
        8. **`nilai_kontrak`**
        9. **`alamat_pemenang`**
        10. **`email_pemenang`**
        11. **`telp_pemenang`**
    """)