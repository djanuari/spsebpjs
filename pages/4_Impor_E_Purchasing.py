from api_connector import upsert_spse_data
import pandas as pd
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning("⚠️ Anda belum login. Silakan kembali ke halaman utama.")
  st.stop()

st.set_page_config(
    page_title="Impor Data E-Purchasing", page_icon="📥", layout="wide"
)

st.title("📥 Impor Data Khusus E-Purchasing / Mini Kompetisi")
st.write(
    "Unggah file rekapitulasi data E-Purchasing (format `.xlsx`, `.xls`, atau"
    " `.csv`) agar tersimpan secara aman ke database cloud Supabase."
)
st.markdown("---")

# Widget unggah file khusus E-Purchasing
uploaded_file = st.file_uploader(
    "Pilih file Excel atau CSV E-Purchasing:", type=["xlsx", "xls", "csv"]
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

    st.subheader("👀 Pratinjau Data yang Diunggah:")
    st.dataframe(df_import.head(10), use_container_width=True)
    st.info(f"Total baris data dalam file: **{len(df_import)} baris**")

    st.markdown("---")

    if st.button("🚀 Proses & Simpan ke Cloud Database", type="primary"):
      with st.spinner("Sedang memproses dan mengunggah data ke cloud..."):
        try:
          sukses_count = 0
          for _, row in df_import.iterrows():
            id_val = row.get("kode_paket") or row.get("kode_rup")
            if pd.notna(id_val):
              data_dict = {
                  "id_paket": str(id_val),
                  "nama_paket": str(row.get("nama_paket", "")),
                  "kategori": "E-Purchasing",
                  "pagu": float(
                      row.get("pagu_paket") or row.get("pagu") or 0
                  ),
                  "hps": float(row.get("hps_paket") or row.get("hps") or 0),
                  "pemenang": str(
                      row.get("nama_pemenang") or row.get("nama_penyedia") or ""
                  ),
                  "status_kepatuhan": str(
                      row.get("status_bpjs")
                      or row.get("status_kepatuhan")
                      or "Belum"
                  ),
                  "tanggal_tarik": str(row.get("tanggal_penetapan", "")),
                  "keterangan": str(
                      row.get("jenis_pengadaan")
                      or f"Kontrak: Rp {float(row.get('nilai_kontrak', 0) or 0):,.2f}"
                  ),
              }
              if upsert_spse_data(data_dict):
                sukses_count += 1

          st.success(
              f"🎉 Berhasil! Sebanyak **{sukses_count} data E-Purchasing** telah"
              " disimpan ke database cloud Supabase."
          )
        except Exception as db_err:
          st.error(
              f"Gagal menyimpan ke cloud database. Detail error: {db_err}"
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
        7. **`nama_pemenang`** / **`nama_penyedia`**
        8. **`nilai_kontrak`**
        9. **`alamat_pemenang`**
        10. **`email_pemenang`**
        11. **`telp_pemenang`**
    """)
