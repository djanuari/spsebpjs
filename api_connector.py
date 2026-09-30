import sqlite3
import requests
import streamlit as st

API_TOKEN = "inprc8b6ed516eb3c425c89596b3b42b2d056"
DB_PATH = "database_spse.db"


def sinkronisasi_database_spse():
  """Fungsi untuk melakukan sinkronisasi data via API SPSE.

  Menyertakan mode simulasi untuk data Tender dan Non-Tender ke database SQLite
  lokal.
  """
  total_keseluruhan = 0

  # Kosongkan untuk memicu mode simulasi (isi dengan URL asli jika sudah ada)
  url_tender = ""
  url_nontender = ""

  if not url_tender and not url_nontender:
    # ---------------------------------------------------------
    # MODE SIMULASI: Memasukkan data Tender & Non-Tender ke SQLite
    # ---------------------------------------------------------
    st.info(
        "ℹ️ Mode Simulasi Aktif: Memasukkan data tiruan Tender & Non-Tender ke"
        " database lokal."
    )

    try:
      conn = sqlite3.connect(DB_PATH, check_same_thread=False)
      cursor = conn.cursor()

      # ==========================================
      # 1. DATA DUMMY TENDER
      # ==========================================
      data_dummy_tender = [
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
              "Sudah",
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
              "Sudah",
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
              "Belum",
          ),
      ]

      for item in data_dummy_tender:
        cursor.execute(
            """
                INSERT OR REPLACE INTO tabel_tender 
                (kode_tender, nama_paket, jenis_pengadaan, satuan_kerja, nilai_pagu, nilai_negosiasi, tanggal_penetapan, nama_pemenang, alamat_pemenang, email_pemenang, telp_pemenang, status_bpjs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            item,
        )
        total_keseluruhan += 1

      # ==========================================
      # 2. DATA DUMMY NON-TENDER
      # ==========================================
      data_dummy_nontender = [
          (
              "NTND-2026-001",
              "Pengadaan ATK Kantor Dinas Kesehatan",
              "Pengadaan Barang",
              "Dinas Kesehatan Kota Kendari",
              75000000,
              72000000,
              "2026-06-02",
              "CV Cahaya Abadi",
              "Jl. Abunawas, Kendari",
              "cahaya.abadi@gmail.com",
              "0401-3221122",
              "Sudah",
          ),
          (
              "NTND-2026-002",
              "Pemeliharaan Berkala Kendaraan Dinas Operasional",
              "Jasa Lainnya",
              "Bappeda Kota Kendari",
              100000000,
              95000000,
              "2026-06-06",
              "Bengkel Sejahtera Motor",
              "Jl. Sao-Sao, Kendari",
              "sejahtera.motor@yahoo.com",
              "0401-3255443",
              "Belum",
          ),
      ]

      for item in data_dummy_nontender:
        cursor.execute(
            """
                INSERT OR REPLACE INTO tabel_nontender 
                (kode_nontender, nama_nontender, jenis_pengadaan, satuan_kerja, nilai_hps, nilai_negosiasi, tanggal_kontrak, nama_pemenang, alamat_pemenang, email_pemenang, telp_pemenang, status_bpjs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            item,
        )
        total_keseluruhan += 1

      conn.commit()
      conn.close()
      return total_keseluruhan

    except Exception as db_err:
      st.error(f"Gagal menyimpan data simulasi ke database: {db_err}")
      return 0

  # ---------------------------------------------------------
  # MODE API ASLI (Digunakan jika URL endpoint sudah diisi nanti)
  # ---------------------------------------------------------
  try:
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()

    # Tarik Tender jika URL ada
    if url_tender:
      resp_tender = requests.get(url_tender, headers=headers, timeout=15)
      if resp_tender.status_code == 200:
        for item in resp_tender.json().get("data", []):
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

    # Tarik Non-Tender jika URL ada
    if url_nontender:
      resp_nontender = requests.get(url_nontender, headers=headers, timeout=15)
      if resp_nontender.status_code == 200:
        for item in resp_nontender.json().get("data", []):
          cursor.execute(
              """
                  INSERT OR REPLACE INTO tabel_nontender 
                  (kode_nontender, nama_nontender, jenis_pengadaan, satuan_kerja, nilai_hps, nilai_negosiasi, tanggal_kontrak, nama_pemenang, status_bpjs)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
              """,
              (
                  item.get("kode_nontender"),
                  item.get("nama_nontender"),
                  item.get("jenis_pengadaan"),
                  item.get("satuan_kerja"),
                  item.get("nilai_hps"),
                  item.get("nilai_negosiasi"),
                  item.get("tanggal_kontrak"),
                  item.get("nama_pemenang"),
                  item.get("status_bpjs", "Belum"),
              ),
          )
          total_keseluruhan += 1

    conn.commit()
    conn.close()
    return total_keseluruhan

  except Exception as e:
    st.error(f"Terjadi kesalahan saat sinkronisasi API: {e}")
    return 0
