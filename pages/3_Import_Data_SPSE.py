import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Kelola Data SPSE & E-Purchasing", page_icon="⚙️", layout="wide"
)

conn = sqlite3.connect("database_spse.db", check_same_thread=False)
cursor = conn.cursor()

# Pastikan tabel database untuk Tender, Non-Tender, dan E-Purchasing tersedia
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS tabel_epurchasing (
    kode_paket TEXT PRIMARY KEY,
    nama_paket TEXT,
    komoditas TEXT,
    satuan_kerja TEXT,
    nilai_transaksi REAL,
    tanggal_transaksi TEXT,
    nama_penyedia TEXT,
    alamat_penyedia TEXT,
    status_bpjs TEXT
)
""")
conn.commit()

st.title("⚙️ Manajemen Data: Tender, Non-Tender, & E-Purchasing")
st.write(
    "Gunakan halaman ini untuk mengunggah data baru atau menghapus data tersimpan"
    " berdasarkan kategori pengadaan."
)
st.markdown("---")

# Pilih Kategori Target (3 Kategori)
kategori_pilihan = st.selectbox(
    "Pilih Kategori Data:",
    ["Paket Tender", "Paket Non-Tender", "Paket E-Purchasing"],
)

# Pemetaan tabel dan kolom kode berdasarkan pilihan
if kategori_pilihan == "Paket Tender":
  target_tabel = "tabel_tender"
  kolom_kode = "kode_tender"
elif kategori_pilihan == "Paket Non-Tender":
  target_tabel = "tabel_nontender"
  kolom_kode = "kode_nontender"
else:
  target_tabel = "tabel_epurchasing"
  kolom_kode = "kode_paket"

# Tab Menu untuk memisahkan Aksi Impor dan Aksi Hapus
tab_impor, tab_hapus = st.tabs(["📥 Impor Data Baru", "🗑️ Hapus Data"])

# ================= TAB 1: IMPOR DATA =================
with tab_impor:
  st.subheader(f"Unggah Data {kategori_pilihan}")
  uploaded_file = st.file_uploader(
      "Pilih file Excel atau CSV:", type=["xlsx", "xls", "csv"], key="upload_file"
  )

  if uploaded_file is not None:
    try:
      if uploaded_file.name.endswith(".csv"):
        df_import = pd.read_csv(uploaded_file)
      else:
        df_import = pd.read_excel(uploaded_file)

      # Normalisasi nama kolom
      df_import.columns = [
          str(c).strip().lower().replace(" ", "_") for c in df_import.columns
      ]

      st.markdown("### 👀 Pratinjau Data yang Diunggah:")
      df_preview = df_import.copy()
      df_preview.insert(0, "No", range(1, len(df_preview) + 1))
      st.dataframe(df_preview.head(10), use_container_width=True)
      st.info(f"Total baris data dalam file: **{len(df_import)} baris**")

      st.markdown("---")

      if st.button("🚀 Proses & Simpan ke Database", type="primary"):
        with st.spinner("Sedang menyimpan data..."):
          try:
            kolom_db = [
                col[1]
                for col in cursor.execute(
                    f"PRAGMA table_info({target_tabel})"
                ).fetchall()
            ]
            kolom_tersedia = [c for c in df_import.columns if c in kolom_db]

            if not kolom_tersedia:
              st.error(
                  "Nama kolom pada file Excel Anda tidak cocok dengan struktur"
                  " database."
              )
            else:
              sukses_count = 0
              for _, row in df_import.iterrows():
                data_row = {
                    col: row[col]
                    for col in kolom_tersedia
                    if pd.notna(row[col])
                }
                if data_row:
                  keys = ", ".join(data_row.keys())
                  placeholders = ", ".join([":" + k for k in data_row.keys()])
                  sql = (
                      f"INSERT OR REPLACE INTO {target_tabel} ({keys}) VALUES"
                      f" ({placeholders})"
                  )
                  cursor.execute(sql, data_row)
                  sukses_count += 1

              conn.commit()
              st.success(
                  f"🎉 Berhasil! Sebanyak **{sukses_count} baris data** telah"
                  f" disimpan ke `{target_tabel}`."
              )
          except Exception as db_err:
            st.error(f"Gagal menyimpan ke database. Detail: {db_err}")
    except Exception as e:
      st.error(f"Terjadi kesalahan saat membaca file: {e}")

# ================= TAB 2: HAPUS DATA =================
with tab_hapus:
  st.subheader(f"🗑️ Kelola Penghapusan Data ({kategori_pilihan})")

  # Tampilkan jumlah data saat ini di database
  df_existing = pd.read_sql_query(f"SELECT * FROM {target_tabel}", conn)
  st.info(
      f"Saat ini terdapat **{len(df_existing)} baris data** di dalam"
      f" `{target_tabel}`."
  )

  if len(df_existing) > 0:
    st.markdown("---")

    # Opsi 1: Hapus berdasarkan Kode Tertentu
    st.markdown("### 1. Hapus Berdasarkan Kode Paket")
    kode_terpilih = st.selectbox(
        "Pilih Kode Paket yang ingin dihapus:",
        options=["-- Pilih Kode --"] + df_existing[kolom_kode].tolist(),
    )

    if kode_terpilih != "-- Pilih Kode --":
      if st.button("🗑️ Hapus Paket Ini", type="secondary"):
        try:
          cursor.execute(
              f"DELETE FROM {target_tabel} WHERE {kolom_kode} = ?",
              (kode_terpilih,),
          )
          conn.commit()
          st.success(
              f"Data dengan {kolom_kode} **{kode_terpilih}** berhasil"
              " dihapus!"
          )
          st.rerun()
        except Exception as e:
          st.error(f"Gagal menghapus data: {e}")

    st.markdown("---")

    # Opsi 2: Reset / Kosongkan Seluruh Tabel
    st.markdown("### 2. Zona Bahaya: Kosongkan Seluruh Tabel")
    st.warning(
        "Tindakan ini akan menghapus **seluruh** data paket pada tabel"
        f" `{target_tabel}` secara permanen!"
    )

    konfirmasi_reset = st.checkbox(
        "Saya yakin ingin menghapus seluruh data pada tabel ini"
    )
    if konfirmasi_reset:
      if st.button(
          "⚠️ Kosongkan Seluruh Tabel Sekarang", type="primary"
      ):
        try:
          cursor.execute(f"DELETE FROM {target_tabel}")
          conn.commit()
          st.success(
              f"Seluruh data pada tabel `{target_tabel}` berhasil dikosongkan!"
          )
          st.rerun()
        except Exception as e:
          st.error(f"Gagal mengosongkan tabel: {e}")
  else:
    st.write("Belum ada data yang tersimpan di dalam tabel ini.")
