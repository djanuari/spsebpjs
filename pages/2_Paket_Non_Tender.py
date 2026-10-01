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
    page_title="Non-Tender / Pengadaan Langsung", page_icon="📦", layout="wide"
)

conn = sqlite3.connect("database_spse.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tabel_nontender (
    kode_nontender TEXT PRIMARY KEY,
    nama_nontender TEXT,
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
  st.subheader("Formulir Input Non-Tender Baru")
  with st.form("form_tambah_nontender", clear_on_submit=True):
    kode_nontender = st.text_input("1. Kode Non-Tender (Unik)")

    nama_nontender = st.text_input("2. Nama Paket")
    satuan_kerja = st.text_input("3. Satuan Kerja")

    c1, c2 = st.columns(2)
    nilai_pagu = c1.number_input(
        "4. Nilai Pagu (Rp)", min_value=0.0, format="%.2f"
    )
    nilai_hps = c2.number_input("5. Nilai HPS (Rp)", min_value=0.0, format="%.2f")

    jenis_pengadaan = st.selectbox("6. Jenis Pengadaan", jenis_pengadaan_opsi)
    nama_pemenang = st.text_input("7. Nama Pemenang / Penyedia")

    c3, c4 = st.columns(2)
    nilai_kontrak = c3.number_input(
        "8. Nilai Kontrak (Rp)", min_value=0.0, format="%.2f"
    )
    tanggal_penetapan = c4.date_input("9. Tanggal Penetapan Pemenang")

    alamat_pemenang = st.text_area("10. Alamat Pemenang")

    c5, c6 = st.columns(2)
    email_pemenang = c5.text_input("11. Email Pemenang")
    telp_pemenang = c6.text_input("12. Nomor Telepon Pemenang")

    status_bpjs = st.selectbox(
        "13. Sudah Memenuhi Ketentuan BPJS?", ["Belum", "Sudah"]
    )

    submit_nt = st.form_submit_button("Simpan Data Non-Tender", type="primary")

    if submit_nt:
      if kode_nontender.strip() == "":
        st.error("Kode Non-Tender wajib diisi!")
      else:
        try:
          cursor.execute(
              """
                        INSERT INTO tabel_nontender 
                        (kode_nontender, nama_nontender, jenis_pengadaan, satuan_kerja, nilai_pagu, nilai_hps, 
                         nama_pemenang, nilai_kontrak, alamat_pemenang, email_pemenang, telp_pemenang, tanggal_penetapan, status_bpjs)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
              (
                  kode_nontender,
                  nama_nontender,
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
              f"Data Non-Tender dengan kode {kode_nontender} berhasil disimpan!"
          )
        except sqlite3.IntegrityError:
          st.error(f"Kode non-tender '{kode_nontender}' sudah terdaftar!")
        except Exception as e:
          st.error(f"Terjadi kesalahan: {e}")

# TAB 2: EDIT DATA
with tab2:
  st.subheader("Edit Data Berdasarkan Kode Non-Tender")
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
        "Pilih Kode Non-Tender yang ingin diedit:", df_list["label_edit"].tolist()
    )

    if pilihan_edit:
      kode_pilih = pilihan_edit.split(" - ")[0]
      df_row = pd.read_sql_query(
          f"SELECT * FROM tabel_nontender WHERE kode_nontender = '{kode_pilih}'",
          conn,
      )

      if not df_row.empty:
        r = df_row.iloc[0]
        st.info(f"Sedang mengedit Kode Non-Tender: **{kode_pilih}**")

        with st.form(f"form_edit_nontender_{kode_pilih}"):
          u_nama = st.text_input(
              "Nama Paket", value=str(r.get("nama_nontender", "") or "")
          )
          u_satker = st.text_input(
              "Satuan Kerja", value=str(r.get("satuan_kerja", "") or "")
          )

          uc1, uc2 = st.columns(2)
          u_pagu = uc1.number_input(
              "Nilai Pagu (Rp)",
              value=float(r.get("nilai_pagu", 0.0) or 0.0),
              format="%.2f",
          )
          u_hps = uc2.number_input(
              "Nilai HPS (Rp)",
              value=float(r.get("nilai_hps", 0.0) or 0.0),
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

          uc3, uc4 = st.columns(2)
          u_nilai = uc3.number_input(
              "Nilai Kontrak (Rp)",
              value=float(r.get("nilai_kontrak", 0.0) or 0.0),
              format="%.2f",
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
                            SET nama_nontender=?, satuan_kerja=?, nilai_pagu=?, nilai_hps=?, jenis_pengadaan=?, 
                                nama_pemenang=?, nilai_kontrak=?, alamat_pemenang=?, email_pemenang=?, telp_pemenang=?, status_bpjs=?
                            WHERE kode_nontender=?
                        """,
                (
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
                f"Data Non-Tender dengan kode {kode_pilih} berhasil"
                " diperbarui!"
            )
  else:
    st.info("Belum ada data Non-Tender tersimpan untuk diedit.")

# TAB 3: LAPORAN, SMART ALERT, & PUSAT NOTIFIKASI
with tab3:
  st.subheader("Rekapitulasi Paket Non-Tender & Peringatan Otomatis")
  try:
    df_nontender = pd.read_sql_query("SELECT * FROM tabel_nontender", conn)
  except Exception:
    df_nontender = pd.DataFrame()

  if not df_nontender.empty:
    hari_ini = datetime.now().date()


    def cek_status_notif_nt(row):
      try:
        tgl_val = row.get("tanggal_penetapan")
        if not tgl_val:
          return "⏳ Menunggu Jadwal"
        tgl_str = str(tgl_val).split()[0]
        tgl_penetapan = datetime.strptime(tgl_str, "%Y-%m-%d").date()
        status = str(row.get("status_bpjs", "Belum")).capitalize()

        if tgl_penetapan <= hari_ini and status == "Belum":
          return "🚨 Wajib Kirim Notifikasi (Jatuh Tempo)"
        elif status == "Sudah":
          return "✅ Selesai / Patuh"
        else:
          return "⏳ Menunggu Jadwal"
      except:
        return "⏳ Menunggu Jadwal"


    df_nontender["status_peringatan"] = df_nontender.apply(
        cek_status_notif_nt, axis=1
    )

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
        key="btn_download_nontender_csv",
    )

    st.markdown("---")
    st.subheader(
        "📨 Pusat Pengiriman Notifikasi (Email & WhatsApp) - Non-Tender"
    )

    with st.expander(
        "⚙️ Konfigurasi Pengirim & Kirim Pesan Notifikasi", expanded=True
    ):
      col_smtp1, col_smtp2 = st.columns(2)
      smtp_email = col_smtp1.text_input(
          "Email Instansi / Pengirim",
          value="admin.spse@kendarikota.go.id",
          key="nt_smtp_email",
      )
      smtp_pass = col_smtp2.text_input(
          "Password / App Password Email", type="password", key="nt_smtp_pass"
      )

      col_pic1, col_pic2, col_pic3 = st.columns(3)
      nama_pic = col_pic1.text_input(
          "Nama PIC BPJS", value="Tim BPJS Kendari", key="nt_pic_nama"
      )
      email_pic = col_pic2.text_input(
          "Email PIC BPJS", value="pic.bpjs@kendarikota.go.id", key="nt_pic_email"
      )
      hp_pic = col_pic3.text_input(
          "No. WhatsApp PIC (628...)", value="6281111222233", key="nt_pic_hp"
      )

      st.markdown("---")

      try:
        if not df_nontender.empty:
          list_opsi_nt = (
              df_nontender["kode_nontender"].astype(str)
              + " - "
              + df_nontender["nama_nontender"].fillna("")
          ).tolist()
          pilihan_notif_nt = st.selectbox(
              "Pilih Kode & Nama Paket Non-Tender:",
              list_opsi_nt,
              key="nt_sel_notif",
          )
        else:
          pilihan_notif_nt = None
      except Exception:
        pilihan_notif_nt = None

      if pilihan_notif_nt:
        try:
          kode_pilih_nt = pilihan_notif_nt.split(" - ")[0]
          matched_rows_nt = df_nontender[
              df_nontender["kode_nontender"] == kode_pilih_nt
          ]

          if not matched_rows_nt.empty:
            row_n = matched_rows_nt.iloc[0]

            pemenang = row_n.get("nama_pemenang", "Pemenang") or "Pemenang"
            email_pemenang = row_n.get("email_pemenang", "") or ""
            telp_pemenang = row_n.get("telp_pemenang", "") or ""
            status = row_n.get("status_bpjs", "Belum")
            nilai_kontrak_nt = row_n.get("nilai_kontrak", 0.0) or 0.0
            alamat_pemenang_val = row_n.get("alamat_pemenang", "-") or "-"

            if "Wajib Kirim" in str(row_n.get("status_peringatan", "")):
              st.error(
                  "🚨 Status Paket Ini: **Jatuh Tempo (Wajib Kirim Notifikasi"
                  " BPJS)**"
              )

            st.markdown("### 👁️ Pratinjau Pesan")

            body_email_nt = f"""Kepada Yth. Pimpinan {pemenang},

Sehubungan dengan penetapan pemenang untuk paket Non-Tender {row_n.get('nama_nontender', '')} (Kode: {kode_pilih_nt}), sesuai dengan Peraturan Walikota Kendari dan MoU antara Pemerintah Kota Kendari, Kejaksaan Negeri Kendari dan BPJS, diharapkan agar Saudara segera menunaikan kewajiban Saudara terkait BPJS Ketenagakerjaan.

Hormat kami,
Dinas Tenaga Kerja dan Perindustrian Kota Kendari"""

            wa_text_nt = f"Halo {pemenang},\n\nSehubungan dengan penetapan pemenang untuk paket Non-Tender {row_n.get('nama_nontender', '')} (Kode: {kode_pilih_nt}), sesuai dengan Peraturan Walikota Kendari dan MoU antara Pemerintah Kota Kendari, Kejaksaan Negeri Kendari dan BPJS, diharapkan agar Saudara segera menunaikan kewajiban Saudara terkait BPJS Ketenagakerjaan.\n\nHormat kami,\nDinas Tenaga Kerja dan Perindustrian Kota Kendari"

            body_pic_nt = f"""Kepada Yth. {nama_pic},

Berikut laporan pemantauan kepatuhan BPJS untuk paket Non-Tender:
- Kode Paket: {kode_pilih_nt}
- Nama Paket: {row_n.get('nama_nontender', '')}
- Nama Pemenang: {pemenang}
- Nilai Kontrak: Rp {nilai_kontrak_nt:,.2f}
- Alamat Pemenang: {alamat_pemenang_val}
- Email Pemenang: {email_pemenang if email_pemenang else '-'}
- No. Telepon Pemenang: {telp_pemenang if telp_pemenang else '-'}
- Status BPJS: {status}

Mohon untuk dapat dilakukan verifikasi lebih lanjut.

Hormat kami,
Dinas Tenaga Kerja dan Perindustrian Kota Kendari"""

            col_prev1, col_prev2 = st.columns(2)
            with col_prev1:
              with st.expander("📄 Pratinjau Email Pemenang"):
                st.text_area(
                    "Teks Email:",
                    value=body_email_nt,
                    height=140,
                    key="prev_nt_mail",
                )
              with st.expander("📱 Pratinjau WhatsApp Pemenang"):
                st.text_area(
                    "Teks WA:", value=wa_text_nt, height=140, key="prev_nt_wa"
                )
            with col_prev2:
              with st.expander("📄 Pratinjau Laporan Email ke PIC"):
                st.text_area(
                    "Teks Laporan:",
                    value=body_pic_nt,
                    height=160,
                    key="prev_nt_pic",
                )

            st.markdown("---")
            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
              st.markdown("### 🏢 Aksi ke Pemenang")
              if st.button("📧 Kirim Email ke Pemenang", key="btn_nt_mail_pem"):
                if not email_pemenang:
                  st.error("Alamat email pemenang kosong!")
                  catat_log(
                      "Non-Tender",
                      kode_pilih_nt,
                      "Pemenang",
                      "Kosong",
                      "Email",
                      "Gagal",
                      "Alamat email kosong",
                  )
                else:
                  try:
                    msg = MIMEMultipart()
                    msg["From"] = smtp_email
                    msg["To"] = email_pemenang
                    msg["Subject"] = (
                        f"Pemberitahuan Kewajiban BPJS - Non-Tender"
                        f" {kode_pilih_nt}"
                    )
                    msg.attach(MIMEText(body_email_nt, "plain"))

                    server = smtplib.SMTP("smtp.gmail.com", 587)
                    server.starttls()
                    server.login(smtp_email, smtp_pass)
                    server.sendmail(
                        smtp_email, email_pemenang, msg.as_string()
                    )
                    server.quit()
                    st.success("Email ke pemenang berhasil dikirim!")
                    catat_log(
                        "Non-Tender",
                        kode_pilih_nt,
                        "Pemenang",
                        email_pemenang,
                        "Email",
                        "Berhasil",
                        "Terkirim via SMTP",
                    )
                  except Exception as e:
                    st.error(f"Gagal kirim email: {e}")
                    catat_log(
                        "Non-Tender",
                        kode_pilih_nt,
                        "Pemenang",
                        email_pemenang,
                        "Email",
                        "Gagal",
                        str(e),
                    )

              if telp_pemenang:
                url_wa_nt = f"https://wa.me/{telp_pemenang}?text={urllib.parse.quote(wa_text_nt)}"
                if st.button(
                    "📲 Kirim WhatsApp ke Pemenang", key="btn_nt_wa_pem"
                ):
                  catat_log(
                      "Non-Tender",
                      kode_pilih_nt,
                      "Pemenang",
                      telp_pemenang,
                      "WhatsApp",
                      "Berhasil",
                      "Tautan WA Dibuka",
                  )
                  st.success("Log WhatsApp pemenang tercatat!")

                st.markdown(
                    f'<a href="{url_wa_nt}" target="_blank" rel="noopener'
                    ' noreferrer"><button style="background-color:#25D366;'
                    ' color:white; border:none; padding:8px 12px;'
                    ' border-radius:5px; width:100%; cursor:pointer;">🔗 Buka'
                    ' Tautan WhatsApp ke Pemenang</button></a>',
                    unsafe_allow_html=True,
                )
              else:
                st.warning("Nomor telepon pemenang tidak tersedia.")

            with col_btn2:
              st.markdown("### 🏥 Aksi ke PIC BPJS")
              if st.button(
                  "📧 Kirim Laporan Email ke PIC BPJS", key="btn_nt_mail_pic"
              ):
                try:
                  msg = MIMEMultipart()
                  msg["From"] = smtp_email
                  msg["To"] = email_pic
                  msg["Subject"] = (
                      f"Laporan Kepatuhan Non-Tender - {kode_pilih_nt}"
                  )
                  msg.attach(MIMEText(body_pic_nt, "plain"))

                  server = smtplib.SMTP("smtp.gmail.com", 587)
                  server.starttls()
                  server.login(smtp_email, smtp_pass)
                  server.sendmail(smtp_email, email_pic, msg.as_string())
                  server.quit()
                  st.success("Email laporan ke PIC BPJS terkirim!")
                  catat_log(
                      "Non-Tender",
                      kode_pilih_nt,
                      "PIC BPJS",
                      email_pic,
                      "Email",
                      "Berhasil",
                      "Laporan Terkirim",
                  )
                except Exception as e:
                  st.error(f"Gagal kirim: {e}")
                  catat_log(
                      "Non-Tender",
                      kode_pilih_nt,
                      "PIC BPJS",
                      email_pic,
                      "Email",
                      "Gagal",
                      str(e),
                  )

              if hp_pic:
                wa_pic_text_nt = f"Halo {nama_pic},\n\nLaporan Non-Tender *{kode_pilih_nt}* ({row_n.get('nama_nontender', '')}). Pemenang: {pemenang}. Status BPJS: *{status}*.\n\nMohon ditindaklanjuti.\n\nHormat kami,\nDinas Tenaga Kerja dan Perindustrian Kota Kendari"
                url_wa_pic_nt = f"https://wa.me/{hp_pic}?text={urllib.parse.quote(wa_pic_text_nt)}"

                if st.button(
                    "📲 Log WhatsApp ke PIC BPJS", key="btn_nt_wa_pic_log"
                ):
                  catat_log(
                      "Non-Tender",
                      kode_pilih_nt,
                      "PIC BPJS",
                      hp_pic,
                      "WhatsApp",
                      "Berhasil",
                      "Tautan WA PIC Dibuka",
                  )
                  st.success("Log WhatsApp PIC tercatat!")

                st.markdown(
                    f'<a href="{url_wa_pic_nt}" target="_blank" rel="noopener'
                    ' noreferrer"><button style="background-color:#007bff;'
                    ' color:white; border:none; padding:8px 12px;'
                    ' border-radius:5px; width:100%; cursor:pointer;">🔗 Buka'
                    ' Tautan WhatsApp ke PIC BPJS</button></a>',
                    unsafe_allow_html=True,
                )
              else:
                st.warning("Nomor WhatsApp PIC BPJS belum diisi.")
        except Exception:
          st.info("Memuat ulang data notifikasi...")
  else:
    st.info("Belum ada data Non-Tender tersimpan.")
