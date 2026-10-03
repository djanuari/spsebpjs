from api_connector import get_all_spse_data, supabase
import pandas as pd
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning("⚠️ Anda belum login.")
  st.stop()

st.set_page_config(
    page_title="Inspeksi Database Cloud", page_icon="🔍", layout="wide"
)

st.title("🔍 Inspeksi Struktur & Isi Database Supabase")
st.markdown("---")

st.info(
    "Halaman ini menampilkan seluruh kolom dan data mentah yang benar-benar"
    " tersimpan di tabel cloud Supabase Anda."
)

if st.button("🔄 Muat Ulang Data Database", type="primary"):
  st.rerun()

try:
  # Ambil langsung data mentah dari tabel
  response = supabase.table("tabel_spse_bpjs").select("*").execute()
  data = response.data

  if data:
    df_db = pd.DataFrame(data)
    st.success(
        f"Berhasil terhubung ke Supabase! Ditemukan {len(df_db)} baris data di"
        " database."
    )

    st.subheader("📋 Daftar Nama Kolom (Field) yang Ada di Database:")
    st.write(list(df_db.columns))

    st.subheader("📊 Tabel Data Mentah (Raw Data):")
    st.dataframe(df_db, use_container_width=True)
  else:
    st.warning("Tabel `tabel_spse_bpjs` di database saat ini kosong.")
except Exception as e:
  st.error(f"Gagal mengambil data dari Supabase: {e}")
