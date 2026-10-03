import math
from supabase import Client, create_client
import pandas as pd
import requests
import streamlit as st

API_TOKEN = "inprc8b6ed516eb3c425c89596b3b42b2d056"

# Inisialisasi Koneksi Supabase dari st.secrets
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
      return 0.0
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
  """Menyimpan atau memperbarui data berdasarkan id_paket ke cloud"""
  try:
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


def sinkronisasi_database_spse():
  """Fungsi sinkronisasi data (Mode Simulasi / API Asli) ke Supabase Cloud"""
  total_keseluruhan = 0

  url_tender = ""
  url_nontender = ""

  if not url_tender and not url_nontender:
    st.info(
        "ℹ️ Mode Simulasi Aktif: Memasukkan data tiruan ke Supabase Cloud."
    )

    try:
      data_dummy = [
          {
              "id_paket": "TND-2026-001",
              "nama_paket": "Pembangunan Gedung Kantor Walikota Tahap II",
              "kategori": "Tender",
              "pagu": 2500000000,
              "hps": 2400000000,
              "pemenang": "PT Sultra Konstruksi Utama",
              "status_kepatuhan": "Sudah",
              "tanggal_tarik": "2026-06-01",
              "keterangan": "Satuan Kerja: Setda Kota Kendari",
          },
          {
              "id_paket": "NTND-2026-001",
              "nama_paket": "Pengadaan ATK Kantor Dinas Kesehatan",
              "kategori": "Non-Tender",
              "pagu": 75000000,
              "hps": 72000000,
              "pemenang": "CV Cahaya Abadi",
              "status_kepatuhan": "Sudah",
              "tanggal_tarik": "2026-06-02",
              "keterangan": "Satuan Kerja: Dinas Kesehatan Kota Kendari",
          },
      ]

      for item in data_dummy:
        if upsert_spse_data(item):
          total_keseluruhan += 1

      return total_keseluruhan
    except Exception as db_err:
      st.error(f"Gagal menyimpan data simulasi: {db_err}")
      return 0

  return total_keseluruhan
