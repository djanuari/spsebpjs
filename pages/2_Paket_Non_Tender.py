from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sqlite3
import urllib.parse
import pandas as pd
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning("⚠️ Anda belum login. Silakan kembali ke halaman utama.")
  st.stop()

st.set_page_config(
    page_title="Non-Tender / Pengadaan Langsung", page_icon="📦", layout="wide"
)

# Koneksi Database SQLite Lokal Asli
conn = sqlite3.connect("database_spse.db", check_same_thread=False)
cursor = conn.cursor()

# Mempertahankan struktur tabel asli persis seperti semula
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
CREATE TABLE IF NOT EXISTS tabel_log_notifikasi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    waktu TEXT,
    kategori_paket TEXT,
    kode_paket TEXT,
    penerima TEXT,
    tujuan TEXT,
    media TEXT,
    status TEXT,
    keterangan TEXT
)
""")
conn.commit()


def catat_log(
    kategori, kode_paket, penerima, tujuan, media, status, keterangan
):
  waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  try:
    cursor.execute(
        """
            INSERT INTO tabel_log_notifikasi (waktu, kategori_paket, kode_paket, penerima, tujuan, media, status, keterangan)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            waktu_sekarang,
            kategori,
            kode_paket,
            penerima,
            tujuan,
            media,
            status,
            keterangan,
        ),
    )
    conn.commit()
  except Exception:
    pass


st.title("📦 2. Data Non-Tender / Pengadaan Langsung & Kepatuhan BPJS")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(
    ["➕ Tambah Data", "✏️ Edit / Hapus Data", "📋 Daftar & Laporan"]
)

jenis_pengadaan_opsi = [
    "Pekerjaan Konstruksi",
    "Jasa Konsultansi Konstruksi",
    "Jasa Konsultansi Non Konstruksi",
    "Jasa Lainnya",
    "Pengadaan Barang",
]

# TAB 1: TAMBAH DATA
with tab1:
  st.subheader("Formulir Input Non-Tender Baru")
  with st.form("form_tambah_nontender", clear_on_submit=True):
    kode_nontender = st.text_input("1. Kode Non-Tender (Unik)")
    nama_nontender = st.text_input("2. Nama Paket")
    satuan_kerja = st.text_input("3. Satuan Kerja")

    c1, c2 = st.columns(2)
    nilai_hps = c1.number_input("4. Nilai HPS (Rp)", min_value=0.0, format="%.2f")
    nilai_negosiasi = c2.number_input(
        "5. Nilai Negosiasi (Rp)", min_value=0.0, format="%.2f"
    )

    jenis_pengadaan = st.selectbox("6. Jenis Pengadaan", jenis_pengadaan_opsi)
    nama_pemenang = st.text_input("7. Nama Pemenang / Penyedia")

    c3, c4 = st.columns(2)
    tanggal_kontrak = c3.date_input("8. Tanggal Kontrak")
    status_bpjs = c4.selectbox(
        "9. Sudah Memenuhi Ketentuan BPJS?", ["Belum", "Sudah"]
    )

    alamat_pemenang = st.text_area("10. Alamat Pemenang")

    c5, c6 = st.columns(2)
    email_pemenang = c5.text_input("11. Email Pemenang")
    telp_pemenang = c6.text_input("12. Nomor Telepon Pemenang")

    submit_nt = st.form_submit_button("Simpan Data Non-Tender", type="primary")

    if submit_nt:
      if kode_nontender.strip() == "":
        st.error("Kode Non-Tender wajib diisi!")
      else:
        try:
          cursor.execute(
              """
                        INSERT INTO tabel_nontender 
                        (kode_nontender, nama_nontender, jenis_pengadaan, satuan_kerja, nilai_hps, nilai_negosiasi, 
                         tanggal_kontrak, nama_pemenang, alamat_pemenang, email_pemenang, telp_pemenang, status_bpjs)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
              (
                  kode_nontender,
                  nama_nontender,
                  jenis_pengadaan,
                  satuan_kerja,
                  nilai_hps,
                  nilai_negosiasi,
                  str(tanggal_kontrak),
                  nama_pemenang,
                  alamat_pemenang,
                  email_pemenang,
                  telp_pemenang,
                  status_bpjs,
              ),
          )
          conn.commit()
          st.success(
              f"Data Non-Tender dengan kode {kode_nontender} berhasil disimpan!"
          )
        except sqlite3.IntegrityError:
          st.error(f"Kode non-tender '{kode_nontender}' sudah terdaftar!")
        except Exception as e:
          st.error(f"Terjadi kesalahan: {e}")

# TAB 2: EDIT & HAPUS DATA
with tab2:
  st.subheader("Edit atau Hapus Data Berdasarkan Kode Non-Tender")
  try:
    df_list = pd.read_sql_query(
        "SELECT kode_nontender, nama_nontender FROM tabel_nontender", conn
    )
  except Exception:
    df_list = pd.DataFrame()

  if not df_list.empty:
    df_list["label_edit"] = (
        df_list["kode_nontender"].astype(str)
        + " - "
        + df_list["nama_nontender"].fillna("")
    )
    pilihan_edit = st.selectbox(
        "Pilih Kode Non-Tender yang ingin dikelola:",
        df_list["label_edit"].tolist(),
    )

    if pilihan_edit:
      kode_pilih = pilihan_edit.split(" - ")[0]
      df_row = pd.read_sql_query(
          f"SELECT * FROM tabel_nontender WHERE kode_nontender = '{kode_pilih}'",
          conn,
      )

      if not df_row.empty:
        r = df_row.iloc[0]
        st.info(f"Sedang mengelola Kode Non-Tender: **{kode_pilih}**")

        with st.form(f"form_edit_nontender_{kode_pilih}"):
          u_nama = st.text_input(
              "Nama Paket", value=str(r.get("nama_nontender", "") or "")
          )
          u_satker = st.text_input(
              "Satuan Kerja", value=str(r.get("satuan_kerja", "") or "")
          )

          uc1, uc2 = st.columns(2)
          u_hps = uc1.number_input(
              "Nilai HPS (Rp)",
              value=float(r.get("nilai_hps", 0.0) or 0.0),
              format="%.2f",
          )
          u_nego = uc2.number_input(
              "Nilai Negosiasi (Rp)",
              value=float(r.get("nilai_negosiasi", 0.0) or 0.0),
              format="%.2f",
          )

          curr_jp = r.get("jenis_pengadaan", "Pengadaan Barang")
          jp_idx = (
              jenis_pengadaan_opsi.index(curr_jp)
              if curr_jp in jenis_pengadaan_opsi
              else 0
          )
          u_jenis = st.selectbox(
              "Jenis Pengadaan", jenis_pengadaan_opsi, index=jp_idx
          )
          u_pemenang = st.text_input(
              "Nama Pemenang", value=str(r.get("nama_pemenang", "") or "")
          )

          stat_idx = (
              ["Belum", "Sudah"].index(r.get("status_bpjs", "Belum"))
              if r.get("status_bpjs") in ["Belum", "Sudah"]
              else 0
          )
          u_bpjs = st.selectbox(
              "Status BPJS", ["Belum", "Sudah"], index=stat_idx
          )

          u_alamat = st.text_area(
              "Alamat Pemenang", value=str(r.get("alamat_pemenang", "") or "")
          )

          uc5, uc6 = st.columns(2)
          u_email = uc5.text_input(
              "Email Pemenang", value=str(r.get("email_pemenang", "") or "")
          )
          u_telp = uc6.text_input(
              "Nomor Telepon Pemenang",
              value=str(r.get("telp_pemenang", "") or ""),
          )

          submit_update = st.form_submit_button(
              "Simpan Perubahan", type="primary"
          )

          if submit_update:
            cursor.execute(
                """
                            UPDATE tabel_nontender 
                            SET nama_nontender=?, satuan_kerja=?, nilai_hps=?, nilai_negosiasi=?, jenis_pengadaan=?, 
                                nama_pemenang=?, alamat_pemenang=?, email_pemenang=?, telp_pemenang=?, status_bpjs=?
                            WHERE kode_nontender=?
                        """,
                (
                    u_nama,
                    u_satker,
                    u_hps,
                    u_nego,
                    u_jenis,
                    u_pemenang,
                    u_alamat,
                    u_email,
                    u_telp,
                    u_bpjs,
                    kode_pilih,
                ),
            )
            conn.commit()
            st.success(
                f"Data Non-Tender dengan kode {kode_pilih} berhasil"
                " diperbarui!"
            )
            st.rerun()

        # Tombol Hapus Data Satuan
        st.markdown("---")
        if st.button(
            f"🗑️ Hapus Paket Non-Tender ({kode_pilih})",
            type="secondary",
            key=f"del_nt_{kode_pilih}",
        ):
          try:
            cursor.execute(
                "DELETE FROM tabel_nontender WHERE kode_nontender = ?",
                (kode_pilih,),
            )
            conn.commit()
            st.success(
                f"Data Non-Tender dengan kode {kode_pilih} berhasil dihapus!"
            )
            st.rerun()
          except Exception as e:
            st.error(f"Gagal menghapus data: {e}")
  else:
    st.info("Belum ada data Non-Tender tersimpan untuk dikelola.")

# TAB 3: LAPORAN & NOTIFIKASI
with tab3:
  st.subheader("Rekapitulasi Paket Non-Tender & Peringatan Otomatis")
  try:
    df_nontender = pd.read_sql_query("SELECT * FROM tabel_nontender", conn)
  except Exception:
    df_nontender = pd.DataFrame()

  if not df_nontender.empty:
    st.dataframe(df_nontender, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📥 Unduh Laporan Data Non-Tender")
    csv_data = df_nontender.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Unduh Laporan Non-Tender ke Format CSV (.csv)",
        data=csv_data,
        file_name="Laporan_Kepatuhan_BPJS_NonTender.csv",
        mime="text/csv",
        type="primary",
    )
  else:
    st.info("Belum ada data Non-Tender tersimpan.")
