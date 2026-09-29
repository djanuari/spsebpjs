import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Impor Data Paket SPSE", page_icon="📥", layout="wide"
)

conn = sqlite3.connect("database_spse.db", check_same_thread=False)
cursor = conn.cursor()

# Pastikan tabel database tersedia
cursor.execute("""
CREATE TABLE IF NOT EXISTS tabel_tender (
    kode_tender TEXT PRIMARY KEY,
    nama_paket TEXT,
    jenis_pengadaan TEXT,
    satuan_kerja TEXT,
    nilai_pagu REAL,
    nilai_negosiasi REAL,
    tanggal_penetapan TEXT,
    nama_pemenang TEXT,
    alamat_pemenang TEXT,
    email_pemenang TEXT,
    telp_pemenang TEXT,
    status_bpjs TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tabel_nontender (
    kode_nontender TEXT PRIMARY KEY,
    nama_nontender TEXT,
    jenis_pengadaan TEXT,
    satuan_kerja TEXT,
    nilai_hps REAL,
    nilai_negosiasi REAL,
    tanggal_kontrak TEXT,
    nama_pemenang TEXT,
    alamat_pemenang TEXT,
    email_pemenang TEXT,
    telp_pemenang TEXT,
    status_bpjs TEXT
)
""")
conn.commit()

st.title("📥 Impor Data Paket SPSE (Excel / CSV)")
st.write(
    "Unggah file rekapitulasi data paket (format `.xlsx`, `.xls`, atau `.csv`)"
    " untuk dimasukkan ke database secara otomatis."
)
st.markdown("---")

# Pilih target tabel impor
kategori_impor = st.selectbox(
    "Pilih Kategori Target Impor:", ["Paket Tender", "Paket Non-Tender"]
)

uploaded_file = st.file_uploader(
    "Pilih file Excel atau CSV:", type=["xlsx", "xls", "csv"]
)

if uploaded_file is not None:
  try:
    if uploaded_file.name.endswith(".csv"):
      df_import = pd.read_csv(uploaded_file)
    else:
      df_import = pd.read_excel(uploaded_file)

    # Normalisasi nama kolom (ubah ke huruf kecil & spasi jadi underscore)
    df_import.columns = [
        str(c).strip().lower().replace(" ", "_") for c in df_import.columns
    ]

    st.subheader("👀 Pratinjau Data yang Diunggah:")
    st.dataframe(df_import.head(10), use_container_width=True)
    st.info(f"Total baris data dalam file: **{len(df_import)} baris**")

    st.markdown("---")

    if st.button("🚀 Proses & Simpan ke Database", type="primary"):
      with st.spinner("Sedang menyimpan data..."):
        try:
          target_tabel = (
              "tabel_tender"
              if kategori_impor == "Paket Tender"
              else "tabel_nontender"
          )
          df_import.to_sql(
              target_tabel, conn, if_exists="append", index=False
          )
          st.success(
              f"🎉 Berhasil! Seluruh data dari file telah diimpor ke"
              f" `{target_tabel}`."
          )
        except Exception as db_err:
          st.error(
              f"Gagal menyimpan ke database. Pastikan kode paket belum pernah"
              f" diimpor sebelumnya atau format kolom sesuai. Detail: {db_err}"
          )

  except Exception as e:
    st.error(f"Terjadi kesalahan saat membaca file. Detail: {e}")

else:
  if kategori_impor == "Paket Tender":
    st.markdown("""
            ### 📋 Panduan Format Kolom File (Paket Tender):
            Pastikan file Excel/CSV Anda memiliki kolom dengan judul berikut:
            1. **`kode_tender`** (Wajib unik)
            2. **`nama_paket`**
            3. **`jenis_pengadaan`** (Contoh: Pekerjaan Konstruksi, Pengadaan Barang, dll)
            4. **`satuan_kerja`**
            5. **`nilai_pagu`** & **`nilai_negosiasi`**
            6. **`tanggal_penetapan`**
            7. **`nama_pemenang`**, **`alamat_pemenang`**, **`email_pemenang`**, **`telp_pemenang`**
            8. **`status_bpjs`** (Sudah / Belum)
        """)
  else:
    st.markdown("""
            ### 📋 Panduan Format Kolom File (Paket Non-Tender):
            Pastikan file Excel/CSV Anda memiliki kolom dengan judul berikut:
            1. **`kode_nontender`** (Wajib unik)
            2. **`nama_nontender`**
            3. **`jenis_pengadaan`** (Contoh: Pekerjaan Konstruksi, Pengadaan Barang, dll)
            4. **`satuan_kerja`**
            5. **`nilai_hps`** & **`nilai_negosiasi`**
            6. **`tanggal_kontrak`**
            7. **`nama_pemenang`**, **`alamat_pemenang`**, **`email_pemenang`**, **`telp_pemenang`**
            8. **`status_bpjs`** (Sudah / Belum)
        """)
