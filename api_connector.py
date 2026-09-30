import sqlite3
import requests
import streamlit as st

API_TOKEN = "inprc8b6ed516eb3c425c89596b3b42b2d056"
DB_PATH = "database_spse.db"


def sinkronisasi_database_spse():
  """Fungsi untuk melakukan sinkronisasi data via API SPSE.

  Jika URL endpoint belum diisi, fungsi ini mengaktifkan Mode Simulasi
  dan memasukkan data tiruan (dummy) langsung ke database SQLite lokal.
  """
  total_keseluruhan = 0
  
  # Masukkan URL endpoint API asli Anda di sini jika nanti sudah memilikinya
  # Contoh: url_tender = "https://lpse.kendarikota.go.id/api/v1/tender"
  url_tender = "" 

  if not url_tender:
    # ---------------------------------------------------------
    # MODE SIMULASI: Memasukkan data dummy langsung ke SQLite
    # ---------------------------------------------------------
    st.info("ℹ️ Mode Simulasi Aktif: Memasukkan data tiruan ke database lokal.")
    
    try:
      conn = sqlite3.connect(DB_PATH, check_same_thread=False)
      cursor = conn.cursor()

      # Data contoh (dummy) untuk tabel_tender
      data_dummy = [
          (
              "TND-2026-001",
              "Pembangunan Gedung Kantor Walikota Tahap II",
              "Pekerjaan Konstruksi",
              "Setda Kota Kendari",
              2500000000,
              2400000000,
              "2026-06-01",
              "PT Sultra Konstruksi Utama",
              "Jalan Malik Raya No. 10, Kendari",
              "sultra.konstruksi@gmail.com",
              "0401-3123456",
              "Sudah"
          ),
          (
              "TND-2026-002",
              "Pengadaan Alat Kesehatan RSUD Kota Kendari",
              "Pengadaan Barang",
              "RSUD Kota Kendari",
              1200000000,
              1150000000,
              "2026-06-05",
              "PT Medika Sejahtera Mandiri",
              "Jl. Brigjen M. Yoenoes, Kendari",
              "medika.sejahtera@yahoo.com",
              "0401-3198765",
              "Sudah"
          ),
          (
              "TND-2026-003",
              "Belanja Jasa Konsultansi Perencanaan Jalan",
              "Jasa Konsultansi",
              "Dinas Pekerjaan Umum",
              350000000,
              340000000,
              "2026-06-10",
              "CV Konsultan Madani",
              "Kadia, Kendari",
              "konsultan.madani@gmail.com",
              "08114112233",
              "Belum"
          )
      ]

      # Masukkan data dummy ke dalam tabel_tender
      for item in data_dummy:
        cursor.execute(
            """
                INSERT OR REPLACE INTO tabel_tender 
                (kode_tender, nama_paket, jenis_pengadaan, satuan_kerja, nilai_pagu, nilai_negosiasi, tanggal_penetapan, nama_pemenang, alamat_pemenang, email_pemenang, telp_pemenang, status_bpjs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            item
        )
        total_keseluruhan += 1

      conn.commit()
      conn.close()
      return total_keseluruhan

    except Exception as db_err:
      st.error(f"Gagal menyimpan data simulasi ke database: {db_err}")
      return 0

  # ---------------------------------------------------------
  # MODE API ASLI (Digunakan jika url_tender sudah diisi nanti)
  # ---------------------------------------------------------
  try:
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    response = requests.get(url_tender, headers=headers, timeout=15)

    if response.status_code == 200:
      conn = sqlite3.connect(DB_PATH, check_same_thread=False)
      cursor = conn.cursor()
      
      data_tender = response.json()
      list_tender = data_tender.get("data", []) if isinstance(data_tender, dict) else data_tender

      for item in list_tender:
        cursor.execute(
            """
                INSERT OR REPLACE INTO tabel_tender 
                (kode_tender, nama_paket, jenis_pengadaan, satuan_kerja, nilai_pagu, nilai_negosiasi, tanggal_penetapan, nama_pemenang, status_bpjs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.get("kode_tender"),
                item.get("nama_paket"),
                item.get("jenis_pengadaan"),
                item.get("satuan_kerja"),
                item.get("nilai_pagu"),
                item.get("nilai_negosiasi"),
                item.get("tanggal_penetapan"),
                item.get("nama_pemenang"),
                item.get("status_bpjs", "Belum"),
            ),
        )
        total_keseluruhan += 1

      conn.commit()
      conn.close()
      return total_keseluruhan
    else:
      st.error(f"Gagal dari server, Status Code: {response.status_code}")
      return 0

  except requests.exceptions.RequestException as req_err:
    st.error(f"Gagal terhubung ke server API: {req_err}")
    return 0
  except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")
    return 0
