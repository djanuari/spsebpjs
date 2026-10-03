import streamlit as st
from api_connector import upsert_spse_data


def inisialisasi_dan_isi_dummy():
  print("⏳ Memulai pengisian data dummy ke Supabase Cloud...")

  # 1. Data Dummy Tender (5 Paket)
  data_tender = [
      {
          "id_paket": "TND-2026-001",
          "nama_paket": "Pembangunan Gedung Kantor Walikota Tahap II",
          "kategori": "Tender",
          "pagu": 2500000000,
          "hps": 2400000000,
          "pemenang": "PT Sultra Konstruksi Utama",
          "status_kepatuhan": "Sudah",
          "tanggal_tarik": "2026-06-01",
          "keterangan": "Setda Kota Kendari | Konstruksi",
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
          "keterangan": "RSUD Kota Kendari | Barang",
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
          "keterangan": "Dinas Pekerjaan Umum | Konsultansi",
      },
      {
          "id_paket": "TND-2026-004",
          "nama_paket": "Peningkatan Jalan Poros Nanga-Nanga",
          "kategori": "Tender",
          "pagu": 4500000000,
          "hps": 4400000000,
          "pemenang": "PT Bumi Kendari Perkasa",
          "status_kepatuhan": "Sudah",
          "tanggal_tarik": "2026-06-12",
          "keterangan": "DPUPR | Konstruksi",
      },
      {
          "id_paket": "TND-2026-005",
          "nama_paket": "Pengadaan Meubelair Sekolah Dasar Negeri Se-Kota Kendari",
          "kategori": "Tender",
          "pagu": 850000000,
          "hps": 820000000,
          "pemenang": "CV Sultra Sejahtera Furnitur",
          "status_kepatuhan": "Belum",
          "tanggal_tarik": "2026-06-15",
          "keterangan": "Dinas Pendidikan dan Kebudayaan | Barang",
      },
  ]

  # 2. Data Dummy Non-Tender (4 Paket)
  data_nontender = [
      {
          "id_paket": "NTND-2026-001",
          "nama_paket": "Pengadaan ATK Kantor Dinas Kesehatan",
          "kategori": "Non-Tender",
          "pagu": 75000000,
          "hps": 72000000,
          "pemenang": "CV Cahaya Abadi",
          "status_kepatuhan": "Sudah",
          "tanggal_tarik": "2026-06-02",
          "keterangan": "Dinas Kesehatan Kota Kendari | Barang",
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
          "keterangan": "Bappeda Kota Kendari | Jasa Lainnya",
      },
      {
          "id_paket": "NTND-2026-003",
          "nama_paket": "Penyusunan Dokumen Kajian Lingkungan Hidup Strategis (KLHS)",
          "kategori": "Non-Tender",
          "pagu": 150000000,
          "hps": 145000000,
          "pemenang": "CV Enviro Consult",
          "status_kepatuhan": "Sudah",
          "tanggal_tarik": "2026-06-08",
          "keterangan": "Dinas Lingkungan Hidup | Jasa Konsultansi",
      },
      {
          "id_paket": "NTND-2026-004",
          "nama_paket": "Belanja Cetak dan Pengadaan Publikasi Kegiatan Pemkot",
          "kategori": "Non-Tender",
          "pagu": 50000000,
          "hps": 48000000,
          "pemenang": "CV Media Utama Kendari",
          "status_kepatuhan": "Belum",
          "tanggal_tarik": "2026-06-11",
          "keterangan": "Diskominfo Kota Kendari | Barang",
      },
  ]

  # 3. Data Dummy E-Purchasing (3 Paket)
  data_epurchasing = [
      {
          "id_paket": "EP-2026-001",
          "nama_paket": "Pembelian Laptop Operasional Kantor (Katalog Elektronik)",
          "kategori": "E-Purchasing",
          "pagu": 150000000,
          "hps": 145000000,
          "pemenang": "PT Elektrindo Jaya",
          "status_kepatuhan": "Sudah",
          "tanggal_tarik": "2026-06-03",
          "keterangan": "BKPSDM | E-Purchasing",
      },
      {
          "id_paket": "EP-2026-002",
          "nama_paket": "Pengadaan Seragam Dinas Pegawai (Katalog Lokal)",
          "kategori": "E-Purchasing",
          "pagu": 80000000,
          "hps": 78000000,
          "pemenang": "CV Konveksi Kendari Mandiri",
          "status_kepatuhan": "Sudah",
          "tanggal_tarik": "2026-06-07",
          "keterangan": "Dinas Perhubungan | E-Purchasing",
      },
      {
          "id_paket": "EP-2026-003",
          "nama_paket": "Belanja Langganan Server dan Cloud Hosting Pemkot",
          "kategori": "E-Purchasing",
          "pagu": 120000000,
          "hps": 120000000,
          "pemenang": "PT Cloud Solusi Indonesia",
          "status_kepatuhan": "Belum",
          "tanggal_tarik": "2026-06-09",
          "keterangan": "Diskominfo Kota Kendari | E-Purchasing",
      },
  ]

  total_sukses = 0
  semua_data = data_tender + data_nontender + data_epurchasing

  for item in semua_data:
    if upsert_spse_data(item):
      total_sukses += 1

  print(
      f"✅ Sukses! Sebanyak {total_sukses} data dummy berhasil dimasukkan ke"
      " tabel cloud Supabase."
  )


if __name__ == "__main__":
  inisialisasi_dan_isi_dummy()
