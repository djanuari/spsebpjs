import requests
import pandas as pd
from supabase import create_client, Client
import streamlit as st

API_TOKEN = "inprc8b6ed516eb3c425c89596b3b42b2d056"

# Inisialisasi Koneksi Supabase dari st.secrets (menggunakan kredensial project Supabase Anda)
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

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
        supabase.table("tabel_spse_bpjs").upsert(
            data_dict, on_conflict="id_paket"
        ).execute()
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan data ke cloud: {e}")
        return False

def sinkronisasi_database_spse():
    """
    Fungsi untuk melakukan sinkronisasi data via API SPSE atau Mode Simulasi,
    langsung disimpan secara permanen ke Supabase Cloud.
    """
    total_keseluruhan = 0

    url_tender = ""
    url_nontender = ""

    if not url_tender and not url_nontender:
        # ---------------------------------------------------------
        # MODE SIMULASI: Memasukkan data tiruan Tender & Non-Tender ke Supabase
        # ---------------------------------------------------------
        st.info("ℹ️ Mode Simulasi Aktif: Memasukkan data tiruan Tender & Non-Tender ke cloud database.")

        try:
            # Data Dummy Tender
            data_dummy_tender = [
                {
                    "id_paket": "TND-2026-001",
                    "nama_paket": "Pembangunan Gedung Kantor Walikota Tahap II",
                    "kategori": "Tender",
                    "pagu": 2500000000,
                    "hps": 2400000000,
                    "pemenang": "PT Sultra Konstruksi Utama",
                    "status_kepatuhan": "Sudah",
                    "tanggal_tarik": "2026-06-01",
                    "keterangan": "Satuan Kerja: Setda Kota Kendari"
                },
                {
                    "id_paket": "TND-2026-002",
                    "nama_paket": "Pengadaan Alat Kesehatan RSUD Kota Kendari",
                    "kategori": "Tender",
                    "pagu": 1200000000,
                    "hps": 1150000000,
                    "pemenang": "PT Medika Sejahtera Mandiri",
                    "status_kepatuhan": "Sudah",
                    "tanggal_tarik": "2026-06-05",
                    "keterangan": "Satuan Kerja: RSUD Kota Kendari"
                },
                {
                    "id_paket": "TND-2026-003",
                    "nama_paket": "Belanja Jasa Konsultansi Perencanaan Jalan",
                    "kategori": "Tender",
                    "pagu": 350000000,
                    "hps": 340000000,
                    "pemenang": "CV Konsultan Madani",
                    "status_kepatuhan": "Belum",
                    "tanggal_tarik": "2026-06-10",
                    "keterangan": "Satuan Kerja: Dinas Pekerjaan Umum"
                }
            ]

            for item in data_dummy_tender:
                if upsert_spse_data(item):
                    total_keseluruhan += 1

            # Data Dummy Non-Tender
            data_dummy_nontender = [
                {
                    "id_paket": "NTND-2026-001",
                    "nama_paket": "Pengadaan ATK Kantor Dinas Kesehatan",
                    "kategori": "Non-Tender",
                    "pagu": 75000000,
                    "hps": 72000000,
                    "pemenang": "CV Cahaya Abadi",
                    "status_kepatuhan": "Sudah",
                    "tanggal_tarik": "2026-06-02",
                    "keterangan": "Satuan Kerja: Dinas Kesehatan Kota Kendari"
                },
                {
                    "id_paket": "NTND-2026-002",
                    "nama_paket": "Pemeliharaan Berkala Kendaraan Dinas Operasional",
                    "kategori": "Non-Tender",
                    "pagu": 100000000,
                    "hps": 95000000,
                    "pemenang": "Bengkel Sejahtera Motor",
                    "status_kepatuhan": "Belum",
                    "tanggal_tarik": "2026-06-06",
                    "keterangan": "Satuan Kerja: Bappeda Kota Kendari"
                }
            ]

            for item in data_dummy_nontender:
                if upsert_spse_data(item):
                    total_keseluruhan += 1

            return total_keseluruhan

        except Exception as db_err:
            st.error(f"Gagal menyimpan data simulasi ke cloud: {db_err}")
            return 0

    # ---------------------------------------------------------
    # MODE API ASLI (Digunakan jika URL endpoint sudah diisi nanti)
    # ---------------------------------------------------------
    try:
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        if url_tender:
            resp_tender = requests.get(url_tender, headers=headers, timeout=15)
            if resp_tender.status_code == 200:
                for item in resp_tender.json().get("data", []):
                    data_item = {
                        "id_paket": item.get("kode_tender"),
                        "nama_paket": item.get("nama_paket"),
                        "kategori": "Tender",
                        "pagu": item.get("nilai_pagu"),
                        "hps": item.get("nilai_hps", 0),
                        "pemenang": item.get("nama_pemenang"),
                        "status_kepatuhan": item.get("status_bpjs", "Belum"),
                        "tanggal_tarik": item.get("tanggal_penetapan"),
                        "keterangan": item.get("satuan_kerja")
                    }
                    if upsert_spse_data(data_item):
                        total_keseluruhan += 1

        if url_nontender:
            resp_nontender = requests.get(url_nontender, headers=headers, timeout=15)
            if resp_nontender.status_code == 200:
                for item in resp_nontender.json().get("data", []):
                    data_item = {
                        "id_paket": item.get("kode_nontender"),
                        "nama_paket": item.get("nama_nontender"),
                        "kategori": "Non-Tender",
                        "pagu": item.get("nilai_pagu", 0),
                        "hps": item.get("nilai_hps"),
                        "pemenang": item.get("nama_pemenang"),
                        "status_kepatuhan": item.get("status_bpjs", "Belum"),
                        "tanggal_tarik": item.get("tanggal_kontrak"),
                        "keterangan": item.get("satuan_kerja")
                    }
                    if upsert_spse_data(data_item):
                        total_keseluruhan += 1

        return total_keseluruhan

    except Exception as e:
        st.error(f"Terjadi kesalahan saat sinkronisasi API: {e}")
        return 0
