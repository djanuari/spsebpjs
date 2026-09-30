import sqlite3
import requests
import streamlit as st

# Token API resmi Anda
API_TOKEN = "inprc8b6ed516eb3c425c89596b3b42b2d056"

# Koneksi ke database lokal
DB_PATH = "database_spse.db"


def sinkronisasi_database_spse():
  """Fungsi untuk menarik data dari endpoint API spesifik,

  memprosesnya, menyimpannya ke database SQLite, dan mengembalikan
  total data yang berhasil diperbarui.
  """
  total_keseluruhan = 0
  conn = sqlite3.connect(DB_PATH, check_same_thread=False)
  cursor = conn.cursor()

  headers = {
      "Authorization": f"Bearer {API_TOKEN}",
      "Content-Type": "application/json",
      "Accept": "application/json",
  }

  try:
    # ==========================================
    # 1. TARIK DATA TENDER (Ganti URL dengan endpoint asli)
    # ==========================================
    url_tender = "https://api.lkpp.go.id/v1/eproc/tender"  # Contoh Endpoint Tender
    response_tender = requests.get(url_tender, headers=headers, timeout=15)

    if response_tender.status_code == 200:
      data_tender = response_tender.json()
      # Sesuaikan struktur kunci JSON dari API (misalnya: data_tender.get('data', []))
      list_tender = data_tender.get("data", []) if isinstance(data_tender, dict) else data_tender

      for item in list_tender:
        # Contoh pemetaan data ke tabel_tender (sesuaikan key API dengan kolom database Anda)
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

    # ==========================================
    # 2. TARIK DATA NON-TENDER (Opsional)
    # ==========================================
    # Lakukan pola serupa jika ada endpoint terpisah untuk non-tender
    # url_nontender = "https://api.lkpp.go.id/v1/eproc/nontender"
    # ... (proses fetch & insert ke tabel_nontender)

    conn.commit()
    conn.close()

    # Mengembalikan total data yang berhasil masuk (agar tidak bernilai 0 atau None)
    return total_keseluruhan

  except requests.exceptions.RequestException as req_err:
    st.error(f"Gagal terhubung ke server API: {req_err}")
    if conn:
      conn.close()
    return 0
  except Exception as e:
    st.error(f"Terjadi kesalahan saat memproses data API: {e}")
    if conn:
      conn.close()
    return 0
