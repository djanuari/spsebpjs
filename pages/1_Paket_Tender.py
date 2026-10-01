import smtplib
import sqlite3
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import urllib.parse
import pandas as pd
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning("⚠️ Anda belum login. Silakan kembali ke halaman utama.")
  st.stop()

st.set_page_config(
    page_title="Tender / Seleksi", page_icon="🏛️", layout="wide"
)

conn = sqlite3.connect("database_spse.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tabel_tender (
    kode_tender TEXT PRIMARY KEY,
    kode_rup TEXT,
    nama_paket TEXT,
    jenis_pengadaan TEXT,
    satuan_kerja TEXT,
    nilai_pagu REAL,
    nilai_hps REAL,
    nama_pemenang TEXT,
    nilai_kontrak REAL,
    alamat_pemenang TEXT,
    email_pemenang TEXT,
    telp_pemenang TEXT,
    tanggal_penetapan TEXT,
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


st.title("🏛️ 1. Data Tender / Seleksi & Kepatuhan BPJS")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(
    ["➕ Tambah Data", "✏️ Edit / Perbarui Data", "📋 Daftar & Laporan"]
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
  st.subheader("Formulir Input Tender / Seleksi Baru")
  with st.form("form_tambah_tender", clear_on_submit=True):
    c1, c2 = st.columns(2)
    kode_rup = c1.text_input("1. Kode RUP")
    kode_tender = c2.text_input("2. Kode Tender (Unik)")

    nama_paket = st.text_input("3. Nama Paket")
    satuan_kerja = st.text_input("4. Satuan Kerja")

    c3, c4 = st.columns(2)
    nilai_pagu = c3.number_input(
        "5. Nilai Pagu (Rp)", min_value=0.0, format="%.2f"
    )
    nilai_hps = c4.number_input("6. Nilai HPS (Rp)", min_value=0.0, format="%.2f")

    jenis_pengadaan = st.selectbox("7. Jenis Pengadaan", jenis_pengadaan_opsi)
    nama_pemenang = st.text_input("8. Nama Pemenang / Penyedia")

    c5, c6 = st.columns(2)
    nilai_kontrak = c5.number_input(
        "9. Nilai Kontrak (Rp)", min_value=0.0, format="%.2f"
    )
    tanggal_penetapan = c6.date_input("10. Tanggal Penetapan Pemenang")

    alamat_pemenang = st.text_area("11. Alamat Pemenang")

    c7, c8 = st.columns(2)
    email_pemenang = c7.text_input("12. Email Pemenang")
    telp_pemenang = c8.text_input("13. Nomor Telepon Pemenang")

    status_bpjs = st.selectbox(
        "14. Sudah Memenuhi Ketentuan BPJS?", ["Belum", "Sudah"]
    )

    submit_t = st.form_submit_button("Simpan Data Tender", type="primary")

    if submit_t:
      if kode_tender.strip() == "":
        st.error("Kode Tender wajib diisi!")
      else:
        try:
          cursor.execute(
              """
                        INSERT INTO tabel_tender 
                        (kode_tender, kode_rup, nama_paket, jenis_pengadaan, satuan_kerja, nilai_pagu, nilai_hps, 
                         nama_pemenang, nilai_kontrak, alamat_pemenang, email_pemenang, telp_pemenang, tanggal_penetapan, status_bpjs)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
              (
                  kode_tender,
                  kode_rup,
                  nama_paket,
                  jenis_pengadaan,
                  satuan_kerja,
                  nilai_pagu,
                  nilai_hps,
                  nama_pemenang,
                  nilai_kontrak,
                  alamat_pemenang,
                  email_pemenang,
                  telp_pemenang,
                  str(tanggal_penetapan),
                  status_bpjs,
              ),
          )
          conn.commit()
          st.success(
              f"Data Tender dengan kode {kode_tender} berhasil disimpan!"
          )
        except sqlite3.IntegrityError:
          st.error(f"Kode tender '{kode_tender}' sudah terdaftar!")
        except Exception as e:
          st.error(f"Terjadi kesalahan: {e}")

# TAB 2: EDIT DATA
with tab2:
  st.subheader("Edit Data Berdasarkan Kode Tender")
  df_list = pd.read_sql_query(
      "SELECT kode_tender, nama_paket FROM tabel_tender", conn
  )

  if not df_list.empty:
    df_list["label_edit"] = (
        df_list["kode_tender"] + " - " + df_list["nama_paket"].fillna("")
    )
    pilihan_edit = st.selectbox(
        "Pilih Kode Tender yang ingin diedit:", df_list["label_edit"].tolist()
    )

    if pilihan_edit:
      kode_pilih = pilihan_edit.split(" - ")[0]
      df_row = pd.read_sql_query(
          f"SELECT * FROM tabel_tender WHERE kode_tender = '{kode_pilih}'",
          conn,
      )

      if not df_row.empty:
        r = df_row.iloc[0]
        st.info(f"Sedang mengedit Kode Tender: **{kode_pilih}**")

        # Form dibuat dinamis berdasarkan kode_pilih agar isian ter-refresh otomatis
        with st.form(f"form_edit_tender_{kode_pilih}"):
          u_rup = st.text_input(
              "Kode RUP", value=str(r["kode_rup"] or "")
          )
          u_nama = st.text_input(
              "Nama Paket", value=str(r["nama_paket"] or "")
          )
          u_satker = st.text_input(
              "Satuan Kerja", value=str(r["satuan_kerja"] or "")
          )

          uc1, uc2 = st.columns(2)
          u_pagu = uc1.number_input(
              "Nilai Pagu (Rp)",
              value=float(r["nilai_pagu"] or 0.0),
              format="%.2f",
          )
          u_hps = uc2.number_input(
              "Nilai HPS (Rp)",
              value=float(r["nilai_hps"] or 0.0),
              format="%.2f",
          )

          curr_jp = r["jenis_pengadaan"]
          jp_idx = (
              jenis_pengadaan_opsi.index(curr_jp)
              if curr_jp in jenis_pengadaan_opsi
              else 0
          )
          u_jenis = st.selectbox(
              "Jenis Pengadaan", jenis_pengadaan_opsi, index=jp_idx
          )
          u_pemenang = st.text_input(
              "Nama Pemenang", value=str(r["nama_pemenang"] or "")
          )

          uc3, uc4 = st.columns(2)
          u_nilai = uc3.number_input(
              "Nilai Kontrak (Rp)",
              value=float(r["nilai_kontrak"] or 0.0),
              format="%.2f",
          )
          stat_idx = (
              ["Belum", "Sudah"].index(r["status_bpjs"])
              if r["status_bpjs"] in ["Belum", "Sudah"]
              else 0
          )
          u_bpjs = st.selectbox(
              "Status BPJS", ["Belum", "Sudah"], index=stat_idx
          )

          u_alamat = st.text_area(
              "Alamat Pemenang", value=str(r["alamat_pemenang"] or "")
          )

          uc5, uc6 = st.columns(2)
          u_email = uc5.text_input(
              "Email Pemenang", value=str(r["email_pemenang"] or "")
          )
          u_telp = uc6.text_input(
              "Nomor Telepon Pemenang", value=str(r["telp_pemenang"] or "")
          )

          submit_update = st.form_submit_button(
              "Simpan Perubahan", type="primary"
          )

          if submit_update:
            cursor.execute(
                """
                            UPDATE tabel_tender 
                            SET kode_rup=?, nama_paket=?, satuan_kerja=?, nilai_pagu=?, nilai_hps=?, jenis_pengadaan=?, 
                                nama_pemenang=?, nilai_kontrak=?, alamat_pemenang=?, email_pemenang=?, telp_pemenang=?, status_bpjs=?
                            WHERE kode_tender=?
                        """,
                (
                    u_rup,
                    u_nama,
                    u_satker,
                    u_pagu,
                    u_hps,
                    u_jenis,
                    u_pemenang,
                    u_nilai,
                    u_alamat,
                    u_email,
                    u_telp,
                    u_bpjs,
                    kode_pilih,
                ),
            )
            conn.commit()
            st.success(
                f"Data Tender dengan kode {kode_pilih} berhasil diperbarui!"
            )
  else:
    st.info("Belum ada data Tender tersimpan untuk diedit.")

# TAB 3: LAPORAN
with tab3:
  st.subheader("Rekapitulasi Paket Tender & Peringatan Otomatis")
  query_t = "SELECT * FROM tabel_tender"
  df_tender = pd.read_sql_query(query_t, conn)

  if not df_tender.empty:
    st.dataframe(df_tender, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📥 Unduh Laporan Data Tender")
    import io

    output_tender = io.BytesIO()
    with pd.ExcelWriter(output_tender, engine="xlsxwriter") as writer:
      df_tender.to_excel(writer, sheet_name="Laporan Tender", index=False)
    excel_data_tender = output_tender.getvalue()

    st.download_button(
        label="📥 Unduh Laporan Tender ke Excel (.xlsx)",
        data=excel_data_tender,
        file_name="Laporan_Kepatuhan_BPJS_Tender.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        type="primary",
        key="btn_download_tender",
    )
  else:
    st.info("Belum ada data Tender tersimpan.")
