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
    page_title="Paket Tender / Seleksi", page_icon="🏗️", layout="wide"
)

conn = sqlite3.connect("database_spse.db", check_same_thread=False)
cursor = conn.cursor()

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


for col_db, col_type in [
    ("jenis_pengadaan", "TEXT"),
    ("satuan_kerja", "TEXT"),
    ("alamat_pemenang", "TEXT"),
    ("email_pemenang", "TEXT"),
    ("telp_pemenang", "TEXT"),
]:
  try:
    cursor.execute(f"ALTER TABLE tabel_tender ADD COLUMN {col_db} {col_type}")
    conn.commit()
  except sqlite3.OperationalError:
    pass

st.title("🏗️ 1. Data Paket Tender / Seleksi & Kepatuhan BPJS")
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
  st.subheader("Formulir Input Paket Tender & Seleksi Baru")
  with st.form("form_tambah_tender", clear_on_submit=True):
    c1, c2 = st.columns(2)
    kode_tender = c1.text_input("1. Kode Paket Tender / Seleksi")
    nama_paket = c2.text_input("2. Nama Paket Tender / Seleksi")

    c_jp, c_skpd = st.columns(2)
    jenis_pengadaan = c_jp.selectbox("3. Jenis Pengadaan", jenis_pengadaan_opsi)
    satuan_kerja = c_skpd.text_input("4. Satuan Kerja (SKPD / Bagian)")

    c3, c4 = st.columns(2)
    nilai_pagu = c3.number_input(
        "5. Nilai Pagu (Rp)", min_value=0.0, format="%.2f"
    )
    nilai_negosiasi = c4.number_input(
        "6. Nilai Negosiasi (Rp)", min_value=0.0, format="%.2f"
    )

    c5, c6 = st.columns(2)
    tanggal_penetapan = c5.date_input("7. Tanggal Penetapan Pemenang")
    nama_pemenang = c6.text_input("8. Nama Pemenang Tender / Seleksi")

    alamat_pemenang = st.text_area("9. Alamat Pemenang Tender / Seleksi")

    c7, c8 = st.columns(2)
    email_pemenang = c7.text_input("10. Alamat Email Pemenang")
    telp_pemenang = c8.text_input("11. Nomor Telepon Pemenang")

    status_bpjs = st.selectbox(
        "12. Sudah Memenuhi Ketentuan BPJS?", ["Belum", "Sudah"]
    )

    submit_tender = st.form_submit_button("Simpan Data Tender", type="primary")

    if submit_tender:
      if kode_tender.strip() == "":
        st.error("Kode paket tender/seleksi wajib diisi!")
      else:
        try:
          cursor.execute(
              """
                        INSERT INTO tabel_tender 
                        (kode_tender, nama_paket, jenis_pengadaan, satuan_kerja, nilai_pagu, nilai_negosiasi, tanggal_penetapan, nama_pemenang, alamat_pemenang, email_pemenang, telp_pemenang, status_bpjs)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
              (
                  kode_tender,
                  nama_paket,
                  jenis_pengadaan,
                  satuan_kerja,
                  nilai_pagu,
                  nilai_negosiasi,
                  str(tanggal_penetapan),
                  nama_pemenang,
                  alamat_pemenang,
                  email_pemenang,
                  telp_pemenang,
                  status_bpjs,
              ),
          )
          conn.commit()
          st.success(
              f"Data paket tender dengan kode {kode_tender} berhasil"
              " disimpan!"
          )
        except sqlite3.IntegrityError:
          st.error(f"Kode tender '{kode_tender}' sudah ada!")
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
          f"SELECT * FROM tabel_tender WHERE kode_tender = '{kode_pilih}'", conn
      )

      if not df_row.empty:
        r = df_row.iloc[0]
        st.info(f"Sedang mengedit Kode Tender: **{kode_pilih}**")

        with st.form("form_edit_tender"):
          u_nama_paket = st.text_input(
              "Nama Paket", value=str(r["nama_paket"] or "")
          )
          curr_jp = r["jenis_pengadaan"]
          jp_idx = (
              jenis_pengadaan_opsi.index(curr_jp)
              if curr_jp in jenis_pengadaan_opsi
              else 0
          )
          u_jenis_pengadaan = st.selectbox(
              "Jenis Pengadaan", jenis_pengadaan_opsi, index=jp_idx
          )
          u_satuan_kerja = st.text_input(
              "Satuan Kerja", value=str(r["satuan_kerja"] or "")
          )

          uc1, uc2 = st.columns(2)
          u_pagu = uc1.number_input(
              "Nilai Pagu (Rp)",
              value=float(r["nilai_pagu"] or 0.0),
              format="%.2f",
          )
          u_nego = uc2.number_input(
              "Nilai Negosiasi (Rp)",
              value=float(r["nilai_negosiasi"] or 0.0),
              format="%.2f",
          )

          uc3, uc4 = st.columns(2)
          u_nama_pemenang = uc3.text_input(
              "Nama Pemenang", value=str(r["nama_pemenang"] or "")
          )
          u_alamat_pemenang = uc4.text_area(
              "Alamat Pemenang", value=str(r["alamat_pemenang"] or "")
          )

          uc5, uc6 = st.columns(2)
          u_email = uc5.text_input(
              "Alamat Email Pemenang", value=str(r["email_pemenang"] or "")
          )
          u_telp = uc6.text_input(
              "Nomor Telepon Pemenang", value=str(r["telp_pemenang"] or "")
          )

          stat_idx = (
              ["Belum", "Sudah"].index(r["status_bpjs"])
              if r["status_bpjs"] in ["Belum", "Sudah"]
              else 0
          )
          u_bpjs = st.selectbox(
              "Status BPJS", ["Belum", "Sudah"], index=stat_idx
          )

          submit_update = st.form_submit_button(
              "Simpan Perubahan", type="primary"
          )

          if submit_update:
            cursor.execute(
                """
                            UPDATE tabel_tender 
                            SET nama_paket=?, jenis_pengadaan=?, satuan_kerja=?, nilai_pagu=?, nilai_negosiasi=?, 
                                nama_pemenang=?, alamat_pemenang=?, email_pemenang=?, telp_pemenang=?, status_bpjs=?
                            WHERE kode_tender=?
                        """,
                (
                    u_nama_paket,
                    u_jenis_pengadaan,
                    u_satuan_kerja,
                    u_pagu,
                    u_nego,
                    u_nama_pemenang,
                    u_alamat_pemenang,
                    u_email,
                    u_telp,
                    u_bpjs,
                    kode_pilih,
                ),
            )
            conn.commit()
            st.success(f"Data tender {kode_pilih} berhasil diperbarui!")
  else:
    st.info("Belum ada data tender tersimpan untuk diedit.")

# TAB 3: LAPORAN & SMART ALERT + LOG PENGIRIMAN
with tab3:
  st.subheader("Rekapitulasi Paket Tender / Seleksi & Peringatan Otomatis")

  query_tender = """
        SELECT kode_tender, nama_paket, jenis_pengadaan, satuan_kerja, nilai_pagu, nilai_negosiasi, 
               tanggal_penetapan, nama_pemenang, alamat_pemenang, email_pemenang, 
               telp_pemenang, status_bpjs 
        FROM tabel_tender
    """
  df_tender = pd.read_sql_query(query_tender, conn)

  if not df_tender.empty:
    hari_ini = datetime.now().date()


    def cek_status_notif(row):
      try:
        tgl_str = str(row["tanggal_penetapan"]).split()[0]
        tgl_penetapan = datetime.strptime(tgl_str, "%Y-%m-%d").date()
        status = str(row["status_bpjs"]).capitalize()

        if tgl_penetapan <= hari_ini and status == "Belum":
          return "🚨 Wajib Kirim Notifikasi (Jatuh Tempo)"
        elif status == "Sudah":
          return "✅ Selesai / Patuh"
        else:
          return "⏳ Menunggu Jadwal"
      except:
        return "⏳ Menunggu Jadwal"


    df_tender["status_peringatan"] = df_tender.apply(
        cek_status_notif, axis=1
    )

    col_f1, col_f2 = st.columns(2)
    filter_bpjs = col_f1.selectbox(
        "Filter Berdasarkan Status BPJS:",
        ["Semua", "Sudah", "Belum"],
        key="f_tender_bpjs",
    )
    filter_alert = col_f2.selectbox(
        "Filter Status Peringatan:",
        ["Semua", "🚨 Wajib Kirim Notifikasi (Jatuh Tempo)"],
        key="f_tender_alert",
    )

    if filter_bpjs != "Semua":
      df_tender = df_tender[df_tender["status_bpjs"] == filter_bpjs]
    if filter_alert != "Semua":
      df_tender = df_tender[
          df_tender["status_peringatan"].str.contains("Wajib Kirim")
      ]

    jumlah_wajib_kirim = len(
        df_tender[df_tender["status_peringatan"].str.contains("Wajib Kirim")]
    )
    if jumlah_wajib_kirim > 0:
      st.warning(
          f"⚠️ Perhatian: Ada **{jumlah_wajib_kirim} paket** yang sudah melewati"
          " tanggal penetapan pemenang namun status BPJS-nya masih 'Belum'!"
      )

    st.dataframe(
        df_tender,
        column_config={
            "kode_tender": "Kode Tender",
            "nama_paket": "Nama Paket",
            "jenis_pengadaan": "Jenis Pengadaan",
            "satuan_kerja": "Satuan Kerja",
            "nilai_pagu": st.column_config.NumberColumn(
                "Nilai Pagu", format="Rp %,d"
            ),
            "nilai_negosiasi": st.column_config.NumberColumn(
                "Nilai Negosiasi", format="Rp %,d"
            ),
            "tanggal_penetapan": "Tgl Penetapan",
            "nama_pemenang": "Nama Pemenang",
            "alamat_pemenang": "Alamat Pemenang",
            "email_pemenang": "Email Pemenang",
            "telp_pemenang": "No. Telepon",
            "status_bpjs": "Status BPJS",
            "status_peringatan": "Status Peringatan Sistem",
        },
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.subheader(
        "📨 Pusat Pengiriman Notifikasi (Email & WhatsApp) - Paket Tender"
    )

    with st.expander(
        "⚙️ Konfigurasi Pengirim & Kirim Pesan Notifikasi", expanded=True
    ):
      col_smtp1, col_smtp2 = st.columns(2)
      smtp_email = col_smtp1.text_input(
          "Email Instansi / Pengirim",
          value="admin.spse@kendarikota.go.id",
          key="t_smtp_email",
      )
      smtp_pass = col_smtp2.text_input(
          "Password / App Password Email", type="password", key="t_smtp_pass"
      )

      col_pic1, col_pic2, col_pic3 = st.columns(3)
      nama_pic = col_pic1.text_input(
          "Nama PIC BPJS", value="Tim BPJS Kendari", key="t_pic_nama"
      )
      email_pic = col_pic2.text_input(
          "Email PIC BPJS", value="pic.bpjs@kendarikota.go.id", key="t_pic_email"
      )
      hp_pic = col_pic3.text_input(
          "No. WhatsApp PIC (628...)", value="6281111222233", key="t_pic_hp"
      )

      st.markdown("---")

      try:
        if not df_tender.empty:
          list_opsi = (
              df_tender["kode_tender"].astype(str)
              + " - "
              + df_tender["nama_paket"].fillna("")
          ).tolist()
          pilihan_notif = st.selectbox(
              "Pilih Kode & Nama Paket untuk Dikirim Notifikasi:",
              list_opsi,
              key="t_sel_notif",
          )
        else:
          pilihan_notif = None
      except Exception:
        pilihan_notif = None

      if pilihan_notif:
        try:
          kode_pilih = pilihan_notif.split(" - ")[0]
          matched_rows = df_tender[df_tender["kode_tender"] == kode_pilih]

          if not matched_rows.empty:
            row_n = matched_rows.iloc[0]

            pemenang = row_n.get("nama_pemenang", "Pemenang") or "Pemenang"
            email_pemenang = row_n.get("email_pemenang", "") or ""
            telp_pemenang = row_n.get("telp_pemenang", "") or ""
            status = row_n.get("status_bpjs", "Belum")

            if "Wajib Kirim" in str(row_n.get("status_peringatan", "")):
              st.error(
                  "🚨 Status Paket Ini: **Jatuh Tempo (Wajib Kirim Notifikasi"
                  " BPJS)**"
              )

            # --- FITUR PRATINJAU PESAN (PREVIEW) ---
            st.markdown("### 👁️ Pratinjau Pesan")

            body_email = f"""Kepada Yth. Pimpinan {pemenang},

Sehubungan dengan penetapan pemenang pada SPSE Kota Kendari untuk paket {row_n.get('nama_paket', '')} (Kode: {kode_pilih}), sesuai dengan Surat Edaran Nomor 100.3.4.3/3290/Tahun 2025 Tentang Perlindungan Jaminan Sosial Berupa Jaminan Kecelakaan Kerja (JKK) dan Jaminan Kematian (JKM) Bagi Pekerja Sektor Jasa Konstruksi Di Lingkungan Pemerintah Kota Kendari, disampaikan agar Saudara segera menunaikan kewajiban Saudara terkait BPJS Ketenagakerjaan.

Hormat kami,
Dinas Tenaga Kerja dan Perindustrian Kota Kendari"""

            wa_text = f"Halo {pemenang},\n\nSehubungan dengan penetapan pemenang untuk paket {row_n.get('nama_paket', '')} (Kode: {kode_pilih}), sesuai dengan Surat Edaran Nomor 100.3.4.3/3290/Tahun 2025 Tentang Perlindungan Jaminan Sosial Berupa Jaminan Kecelakaan Kerja (JKK) dan Jaminan Kematian (JKM) Bagi Pekerja Sektor Jasa Konstruksi Di Lingkungan Pemerintah Kota Kendari, disampaikan agar Saudara segera menunaikan kewajiban Saudara terkait BPJS Ketenagakerjaan..\n\nHormat kami,\nDinas Tenaga Kerja dan Perindustrian Kota Kendari"

            body_pic = f"""Kepada Yth. {nama_pic},

Berikut laporan pemantauan kepatuhan BPJS untuk paket Tender:
- Kode Paket: {kode_pilih}
- Nama Paket: {row_n.get('nama_paket', '')}
- Nama Pemenang: {pemenang}
- Status BPJS: {status}

Mohon untuk dapat dilakukan verifikasi lebih lanjut.

Hormat kami,
Dinas Tenaga Kerja dan Perindustrian Kota Kendari"""

            col_prev1, col_prev2 = st.columns(2)
            with col_prev1:
              with st.expander("📄 Pratinjau Email Pemenang"):
                st.text_area(
                    "Teks Email:",
                    value=body_email,
                    height=140,
                    key="prev_t_mail",
                )
              with st.expander("📱 Pratinjau WhatsApp Pemenang"):
                st.text_area(
                    "Teks WA:", value=wa_text, height=140, key="prev_t_wa"
                )
            with col_prev2:
              with st.expander("📄 Pratinjau Laporan Email ke PIC"):
                st.text_area(
                    "Teks Laporan:",
                    value=body_pic,
                    height=140,
                    key="prev_t_pic",
                )

            st.markdown("---")

            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
              st.markdown("### 🏢 Aksi ke Pemenang")
              if st.button("📧 Kirim Email ke Pemenang", key="btn_t_mail_pem"):
                if not email_pemenang:
                  st.error("Alamat email pemenang kosong!")
                  catat_log(
                      "Tender",
                      kode_pilih,
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
                        f"Pemberitahuan Kewajiban BPJS - Tender {kode_pilih}"
                    )
                    msg.attach(MIMEText(body_email, "plain"))

                    server = smtplib.SMTP("smtp.gmail.com", 587)
                    server.starttls()
                    server.login(smtp_email, smtp_pass)
                    server.sendmail(
                        smtp_email, email_pemenang, msg.as_string()
                    )
                    server.quit()
                    st.success(f"Email berhasil dikirim ke {email_pemenang}!")
                    catat_log(
                        "Tender",
                        kode_pilih,
                        "Pemenang",
                        email_pemenang,
                        "Email",
                        "Berhasil",
                        "Terkirim via SMTP",
                    )
                  except Exception as e:
                    st.error(f"Gagal mengirim email: {e}")
                    catat_log(
                        "Tender",
                        kode_pilih,
                        "Pemenang",
                        email_pemenang,
                        "Email",
                        "Gagal",
                        str(e),
                    )

              if telp_pemenang:
                url_wa = (
                    f"https://wa.me/{telp_pemenang}?text={urllib.parse.quote(wa_text)}"
                )
                if st.button("📲 Kirim WhatsApp ke Pemenang", key="btn_t_wa_pem"):
                  catat_log(
                      "Tender",
                      kode_pilih,
                      "Pemenang",
                      telp_pemenang,
                      "WhatsApp",
                      "Berhasil",
                      "Tautan WA Dibuka",
                  )
                  st.success("Log WhatsApp pemenang tercatat!")

                st.markdown(
                    f'<a href="{url_wa}" target="_blank" rel="noopener'
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
                  "📧 Kirim Laporan Email ke PIC BPJS", key="btn_t_mail_pic"
              ):
                if not email_pic or not smtp_pass:
                  st.error("Email PIC atau Password SMTP belum lengkap!")
                else:
                  try:
                    msg = MIMEMultipart()
                    msg["From"] = smtp_email
                    msg["To"] = email_pic
                    msg["Subject"] = (
                        f"Laporan Kepatuhan BPJS Tender - {kode_pilih}"
                    )
                    msg.attach(MIMEText(body_pic, "plain"))

                    server = smtplib.SMTP("smtp.gmail.com", 587)
                    server.starttls()
                    server.login(smtp_email, smtp_pass)
                    server.sendmail(smtp_email, email_pic, msg.as_string())
                    server.quit()
                    st.success(
                        f"Laporan email berhasil dikirim ke {email_pic}!"
                    )
                    catat_log(
                        "Tender",
                        kode_pilih,
                        "PIC BPJS",
                        email_pic,
                        "Email",
                        "Berhasil",
                        "Laporan Terkirim",
                    )
                  except Exception as e:
                    st.error(f"Gagal mengirim email ke PIC: {e}")
                    catat_log(
                        "Tender",
                        kode_pilih,
                        "PIC BPJS",
                        email_pic,
                        "Email",
                        "Gagal",
                        str(e),
                    )

              if hp_pic:
                wa_pic_text = f"Halo {nama_pic},\n\nLaporan paket Tender *{kode_pilih}* ({row_n.get('nama_paket', '')}). Pemenang: {pemenang}. Status BPJS: *{status}*.\n\nMohon ditindaklanjuti.\n\nHormat kami,\nDinas Tenaga Kerja dan Perindustrian Kota Kendari"
                url_wa_pic = f"https://wa.me/{hp_pic}?text={urllib.parse.quote(wa_pic_text)}"

                if st.button(
                    "📲 Log WhatsApp ke PIC BPJS", key="btn_t_wa_pic_log"
                ):
                  catat_log(
                      "Tender",
                      kode_pilih,
                      "PIC BPJS",
                      hp_pic,
                      "WhatsApp",
                      "Berhasil",
                      "Tautan WA PIC Dibuka",
                  )
                  st.success("Log WhatsApp PIC tercatat!")

                st.markdown(
                    f'<a href="{url_wa_pic}" target="_blank" rel="noopener'
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
    st.info("Belum ada data paket tender yang tersimpan.")
