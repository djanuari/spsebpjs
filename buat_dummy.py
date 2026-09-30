import sqlite3

DB_PATH = "database_spse.db"


def inisialisasi_dan_isi_dummy():
  print("⏳ Menghubungkan ke database lokal:", DB_PATH)
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()

  # 1. Pastikan tabel-tabel utama sudah ada (jaga-jaga jika belum dibuat)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS tabel_tender (
            kode_tender TEXT PRIMARY KEY,
            nama_paket TEXT,
            jenis_pengadaan TEXT,
            satuan_kerja TEXT,
            nilai_pagu REAL,
            nilai_negosiasi REAL,
            tanggal_penetapan TEXT,
            nama_pemenang TEXT,
            alamat_pemenang TEXT,
            email_pemenang TEXT,
            telp_pemenang TEXT,
            status_bpjs TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS tabel_nontender (
            kode_nontender TEXT PRIMARY KEY,
            nama_nontender TEXT,
            jenis_pengadaan TEXT,
            satuan_kerja TEXT,
            nilai_hps REAL,
            nilai_negosiasi REAL,
            tanggal_kontrak TEXT,
            nama_pemenang TEXT,
            alamat_pemenang TEXT,
            email_pemenang TEXT,
            telp_pemenang TEXT,
            status_bpjs TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS tabel_epurchasing (
            kode_paket TEXT PRIMARY KEY,
            nama_paket TEXT,
            penyedia TEXT,
            satuan_kerja TEXT,
            pagu REAL,
            nilai_transaksi REAL,
            tanggal_transaksi TEXT,
            status_bpjs TEXT
        )
    """)

  # 2. Data Dummy Tender (5 Paket)
  data_tender = [
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
      (
          "TND-2026-004",
          "Peningkatan Jalan Poros Nanga-Nanga",
          "Pekerjaan Konstruksi",
          "Dinas Pekerjaan Umum dan Penataan Ruang",
          4500000000,
          4400000000,
          "2026-06-12",
          "PT Bumi Kendari Perkasa",
          "Jl. HEA Mokodompit, Kendari",
          "bumi.perkasa@gmail.com",
          "0401-3155678",
          "Sudah",
      ),
      (
          "TND-2026-005",
          "Pengadaan Meubelair Sekolah Dasar Negeri Se-Kota Kendari",
          "Pengadaan Barang",
          "Dinas Pendidikan dan Kebudayaan",
          850000000,
          820000000,
          "2026-06-15",
          "CV Sultra Sejahtera Furnitur",
          "Mandonga, Kendari",
          "sultra.furnitur@yahoo.com",
          "0401-3224455",
          "Belum",
      ),
  ]

  # 3. Data Dummy Non-Tender (4 Paket)
  data_nontender = [
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
      (
          "NTND-2026-003",
          "Penyusunan Dokumen Kajian Lingkungan Hidup Strategis (KLHS)",
          "Jasa Konsultansi",
          "Dinas Lingkungan Hidup",
          150000000,
          145000000,
          "2026-06-08",
          "CV Enviro Consult",
          "Wua-Wua, Kendari",
          "enviro.consult@gmail.com",
          "08124567890",
          "Sudah",
      ),
      (
          "NTND-2026-004",
          "Belanja Cetak dan Pengadaan Publikasi Kegiatan Pemkot",
          "Pengadaan Barang",
          "Diskominfo Kota Kendari",
          50000000,
          48000000,
          "2026-06-11",
          "CV Media Utama Kendari",
          "Mandonga, Kendari",
          "media.utama@gmail.com",
          "0401-3118899",
          "Belum",
      ),
  ]

  # 4. Data Dummy E-Purchasing (3 Paket)
  data_epurchasing = [
      (
          "EP-2026-001",
          "Pembelian Laptop Operasional Kantor (Katalog Elektronik)",
          "PT Elektrindo Jaya",
          "Badan Kepegawaian dan Pengembangan SDM",
          150000000,
          145000000,
          "2026-06-03",
          "Sudah",
      ),
      (
          "EP-2026-002",
          "Pengadaan Seragam Dinas Pegawai (Katalog Lokal)",
          "CV Konveksi Kendari Mandiri",
          "Dinas Perhubungan",
          80000000,
          78000000,
          "2026-06-07",
          "Sudah",
      ),
      (
          "EP-2026-003",
          "Belanja Langganan Server dan Cloud Hosting Pemkot",
          "PT Cloud Solusi Indonesia",
          "Dinas Komunikasi dan Informatika",
          120000000,
          120000000,
          "2026-06-09",
          "Belum",
      ),
  ]

  # Eksekusi Memasukkan Data ke Database
  cursor.executemany(
      """
        INSERT OR REPLACE INTO tabel_tender 
        (kode_tender, nama_paket, jenis_pengadaan, satuan_kerja, nilai_pagu, nilai_negosiasi, tanggal_penetapan, nama_pemenang, alamat_pemenang, email_pemenang, telp_pemenang, status_bpjs)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
      data_tender,
  )

  cursor.executemany(
      """
        INSERT OR REPLACE INTO tabel_nontender 
        (kode_nontender, nama_nontender, jenis_pengadaan, satuan_kerja, nilai_hps, nilai_negosiasi, tanggal_kontrak, nama_pemenang, alamat_pemenang, email_pemenang, telp_pemenang, status_bpjs)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
      data_nontender,
  )

  cursor.executemany(
      """
        INSERT OR REPLACE INTO tabel_epurchasing 
        (kode_paket, nama_paket, penyedia, satuan_kerja, pagu, nilai_transaksi, tanggal_transaksi, status_bpjs)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
      data_epurchasing,
  )

  conn.commit()
  conn.close()
  print("✅ Sukses! Data dummy Tender, Non-Tender, dan E-Purchasing berhasil dimasukkan ke database.")


if __name__ == "__main__":
  inisialisasi_dan_isi_dummy()
