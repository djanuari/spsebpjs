import math
import requests
from supabase import create_client, Client
import streamlit as st

API_TOKEN = "inprc8b6ed516eb3c425c89596b3b42b2d056"

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]


@st.cache_resource
def init_supabase() -> Client:
  return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()


def clean_value(val):
  """Membersihkan nilai NaN atau float di luar batas JSON"""
  if val is None:
    return None
  if isinstance(val, float):
    if math.isnan(val) or math.isinf(val):
      return 0.0  # Ubah NaN/inf menjadi 0 atau string kosong
  return val


def get_all_spse_data():
  """Mengambil seluruh data dari tabel_spse_bpjs di cloud Supabase"""
  try:
    res = supabase.table("tabel_spse_bpjs").select("*").execute()
    return pd.DataFrame(res.data)
  except Exception as e:
    st.error(f"Gagal mengambil data dari Supabase: {e}")
    return pd.DataFrame()


def upsert_spse_data(data_dict):
  """Menyimpan atau memperbarui data ke cloud dengan membersihkan nilai NaN"""
  try:
    # Bersihkan setiap nilai dari potensi NaN / float ilegal
    cleaned_dict = {
        k: (
            clean_value(v)
            if not isinstance(v, str)
            else (v if v.strip() != "" else None)
        )
        for k, v in data_dict.items()
    }

    supabase.table("tabel_spse_bpjs").upsert(
        cleaned_dict, on_conflict="id_paket"
    ).execute()
    return True
  except Exception as e:
    st.error(f"Gagal menyimpan data ke cloud: {e}")
    return False
