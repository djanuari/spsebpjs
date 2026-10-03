from api_connector import get_all_spse_data, upsert_spse_data
from supabase import create_client
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Kelola Data SPSE & E-Purchasing", page_icon="⚙️", layout="wide"
)

# Inisialisasi koneksi Supabase untuk eksekusi hapus langsung jika diperlukan
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("⚙️ Manajemen Data: Tender, Non-Tender, & E-Purchasing")
st.write(
    "Gunakan halaman ini untuk mengunggah data baru atau menghapus data tersimpan"
    " di cloud berdasarkan kategori pengadaan."
)
st.markdown("---")

# Pilih Kategori Target (3 Kategori)
kategori_pilihan = st.selectbox(
    "Pilih Kategori Data:",
    ["Paket Tender", "Paket Non-Tender", "Paket E-Purchasing"],
)

# Pemetaan kategori untuk disimpan ke kolom 'kategori' di tabel cloud
if kategori_pilihan == "Paket Tender":
  kategori_db = "Tender"
elif kategori_pilihan == "Paket Non-Tender":
  kategori_db = "Non-Tender"
else:
  kategori_db = "E-Purchasing"

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

      if st.button("🚀 Proses & Simpan ke Cloud Database", type="primary"):
        with st.spinner("Sedang menyimpan data ke cloud..."):
          try:
            sukses_count = 0
            for _, row in df_import.iterrows():
              # Ambil id_paket dari berbagai variasi penamaan kolom file pengguna
              id_val = (
                  row.get("id_paket")
                  or row.get("kode_tender")
                  or row.get("kode_nontender")
                  or row.get("kode_paket")
              )

              if pd.notna(id_val):
                data_dict = {
                    "id_paket": str(id_val),
                    "nama_paket": str(
                        row.get("nama_paket")
                        or row.get("nama_nontender")
                        or ""
                    ),
                    "kategori": kategori_db,
                    "pagu": float(
                        row.get("pagu")
                        or row.get("nilai_pagu")
                        or row.get("pagu_paket")
                        or 0
                    ),
                    "hps": float(
                        row.get("hps") or row.get("nilai_hps") or 0
                    ),
                    "pemenang": str(
                        row.get("pemenang")
                        or row.get("nama_pemenang")
                        or row.get("nama_penyedia")
                        or ""
                    ),
                    "status_kepatuhan": str(
                        row.get("status_kepatuhan")
                        or row.get("status_bpjs")
                        or "Belum"
                    ),
                    "tanggal_tarik": str(
                        row.get("tanggal_tarik")
                        or row.get("tanggal_penetapan")
                        or row.get("tanggal_kontrak")
                        or ""
                    ),
                    "keterangan": str(
                        row.get("keterangan")
                        or row.get("satuan_kerja")
                        or f"Kategori: {kategori_pilihan}"
                    ),
                }

                if upsert_spse_data(data_dict):
                  sukses_count += 1

            st.success(
                f"🎉 Berhasil! Sebanyak **{sukses_count} baris data** telah"
                f" disimpan ke tabel cloud untuk {kategori_pilihan}."
            )
          except Exception as db_err:
            st.error(f"Gagal menyimpan ke database cloud. Detail: {db_err}")
    except Exception as e:
      st.error(f"Terjadi kesalahan saat membaca file: {e}")

# ================= TAB 2: HAPUS DATA =================
with tab_hapus:
  st.subheader(f"🗑️ Kelola Penghapusan Data ({kategori_pilihan})")

  # Ambil data dari cloud dan filter berdasarkan kategori yang dipilih
  df_all = get_all_spse_data()
  if not df_all.empty and "kategori" in df_all.columns:
    df_existing = df_all[
        df_all["kategori"].str.lower() == kategori_db.lower()
    ]
  else:
    df_existing = pd.DataFrame()

  st.info(
      f"Saat ini terdapat **{len(df_existing)} baris data** tersimpan untuk"
      f" kategori {kategori_pilihan} di cloud."
  )

  if len(df_existing) > 0:
    st.markdown("---")

    # Opsi 1: Hapus berdasarkan ID/Kode Tertentu
    st.markdown("### 1. Hapus Berdasarkan Kode Paket")
    list_kode = df_existing["id_paket"].astype(str).tolist()
    kode_terpilih = st.selectbox(
        "Pilih Kode Paket yang ingin dihapus:",
        options=["-- Pilih Kode --"] + list_kode,
    )

    if kode_terpilih != "-- Pilih Kode --":
      if st.button("🗑️ Hapus Paket Ini", type="secondary"):
        try:
          supabase.table("tabel_spse_bpjs").delete().eq(
              "id_paket", kode_terpilih
          ).execute()
          st.success(
              f"Data dengan kode **{kode_terpilih}** berhasil dihapus dari"
              " cloud!"
          )
          st.rerun()
        except Exception as e:
          st.error(f"Gagal menghapus data: {e}")

    st.markdown("---")

    # Opsi 2: Kosongkan Kategori Ini
    st.markdown("### 2. Zona Bahaya: Kosongkan Kategori Ini")
    st.warning(
        "Tindakan ini akan menghapus **seluruh** data paket untuk kategori"
        f" `{kategori_pilihan}` secara permanen dari cloud!"
    )

    konfirmasi_reset = st.checkbox(
        "Saya yakin ingin menghapus seluruh data kategori ini"
    )
    if konfirmasi_reset:
      if st.button("⚠️ Kosongkan Kategori Ini Sekarang", type="primary"):
        try:
          supabase.table("tabel_spse_bpjs").delete().eq(
              "kategori", kategori_db
          ).execute()
          st.success(
              f"Seluruh data untuk kategori `{kategori_pilihan}` berhasil"
              " dikosongkan!"
          )
          st.rerun()
        except Exception as e:
          st.error(f"Gagal mengosongkan data: {e}")
  else:
    st.write("Belum ada data yang tersimpan di dalam kategori ini.")
