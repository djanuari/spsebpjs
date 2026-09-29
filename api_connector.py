import sqlite3
import requests
import streamlit as st

# Konfigurasi Endpoint API SPSE Kota Kendari (Sesuaikan URL resmi LPSE/SPSE instansi Anda)
API_BASE_URL = "https://spse.inaproc.id/kendarikota/api/v1"  # Contoh endpoint umum
API_TOKEN = inprc8b6ed516eb3c425c89596b3b42b2d056 # Ganti dengan token asli Anda


def ambil_data_tender_api():
  headers = {
      "Authorization": f"Bearer {API_TOKEN}",
      "Accept": "application/json",
  }

  try:
    response = requests.get(
        f"{API_BASE_URL}/tender", headers=headers, timeout=15
    )
    if response.status_code == 200:
      data_json = response.json()
      return data_json.get("data", [])
    else:
      st.error(
          f"Gagal mengambil data dari API SPSE. Status Kode: {response.status_code}"
      )
      return []
  except Exception as e:
    st.error(f"Terjadi kesalahan koneksi ke API SPSE: {e}")
    return []


def sinkronisasi_database_spse():
  conn = sqlite3.connect("database_spse.db", check_same_thread=False)
  cursor = conn.cursor()

  # Ambil data dari API
  data_tender = ambil_data_tender_api()

  jumlah_masuk = 0
  for item in data_tender:
    try:
      # Sesuaikan key dictionary JSON dengan struktur balasan API SPSE Kota Kendari
      kode = item.get("kode_tender")
      nama = item.get("nama_paket")
      kategori = item.get("jenis_pengadaan")
      skpd = item.get("satuan_kerja")
      pagu = item.get("nilai_pagu", 0.0)
      nego = item.get("nilai_negosiasi", 0.0)
      tgl = item.get("tanggal_penetapan")
      pemenang = item.get("nama_pemenang")
      alamat = item.get("alamat_pemenang")
      email = item.get("email_pemenang")
      telp = item.get("telp_pemenang")

      # Masukkan atau perbarui data ke database lokal SQLite
      cursor.execute(
          """
                INSERT INTO tabel_tender 
                (kode_tender, nama_paket, jenis_pengadaan, satuan_kerja, nilai_pagu, nilai_negosiasi, 
                 tanggal_penetapan, nama_pemenang, alamat_pemenang, email_pemenang, telp_pemenang, status_bpjs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT status_bpjs FROM tabel_tender WHERE kode_tender = ?), 'Belum'))
                ON CONFLICT(kode_tender) DO UPDATE SET
                nama_paket=excluded.nama_paket,
                nilai_pagu=excluded.nilai_pagu,
                nilai_negosiasi=excluded.nilai_negosiasi,
                tanggal_penetapan=excluded.tanggal_penetapan,
                nama_pemenang=excluded.nama_pemenang
            """,
          (
              kode,
              nama,
              kategori,
              skpd,
              pagu,
              nego,
              tgl,
              pemenang,
              alamat,
              email,
              telp,
              kode,
          ),
      )
      jumlah_masuk += 1
    except Exception as ex:
      print(f"Gagal memproses item: {ex}")

  conn.commit()
  conn.close()
  return jumlah_masuk
