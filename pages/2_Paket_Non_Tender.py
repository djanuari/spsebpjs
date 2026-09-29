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
    page_title="Paket Non-Tender", page_icon="📋", layout="wide"
)

conn = sqlite3.connect("database_spse.db", check_same_thread=False)
cursor = conn.cursor()

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


try:
  cursor.execute(
      "ALTER TABLE tabel_nontender RENAME COLUMN nilai_pagu TO nilai_hps"
  )
  conn.commit()
except sqlite3.OperationalError:
  pass

for col_db, col_type in [
    ("email_pemenang", "TEXT"),
    ("telp_pemenang", "TEXT"),
    ("satuan_kerja", "TEXT"),
    ("nilai_hps", "REAL"),
    ("jenis_pengadaan", "TEXT"),
]:
  try:
    cursor.execute(f"ALTER TABLE tabel_nontender ADD COLUMN {col_db} {col_type}")
    conn.commit()
  except sqlite3.OperationalError:
    pass

st.title("📋 2. Data Paket Non-Tender & Kepatuhan BPJS")
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
  st.subheader("Formulir Input Paket Non-Tender Baru")
  with st.form("form_tambah_nontender", clear_on_submit=True):
    c1, c2 = st.columns(2)
    kode_nontender = c1.text_input("1. Kode Paket Non-Tender")
    nama_nontender = c2.text_input("2. Nama Paket Non-Tender")

    c_jp, c_skpd = st.columns(2)
    jenis_pengadaan = c_jp.selectbox("3. Jenis Pengadaan", jenis_pengadaan_opsi)
    satuan_kerja = c_skpd.text_input(
        "4. Satuan Kerja (SKPD / Bagian)", key="nt_skpd"
    )

    c3, c4 = st.columns(2)
    nilai_hps = c3.number_input(
        "5. Nilai HPS (Rp)", min_value=0.0, format="%.2f", key="nt_hps"
    )
    nilai_negosiasi = c4.number_input(
        "6. Nilai Negosiasi (Rp)", min_value=0.0, format="%.2f", key="nt_nego"
    )

    c5, c6 = st.columns(2)
    tanggal_kontrak = c5.date_input("7. Tanggal Penetapan Pemenang")
    nama_pemenang = c6.text_input(
        "8. Nama Pemenang Non-Tender", key="nt_pemenang"
    )

    alamat_pemenang = st.text_area(
        "9. Alamat Pemenang Non-Tender", key="nt_alamat"
    )

    c7, c8 = st.columns(2)
    email_pemenang = c7.text_input("10. Alamat Email Pemenang", key="nt_email")
    telp_pemenang = c8.text_input("11. Nomor Telepon Pemenang", key="nt_telp")

    status_bpjs = st.selectbox(
        "12. Sudah Memenuhi Ketentuan BPJS?", ["Belum", "Sudah"], key="nt_bpjs"
    )

    submit_nontender = st.form_submit_button(
        "Simpan Data Non-Tender", type="primary"
    )

    if submit_nontender:
      if kode_nontender.strip() == "":
        st.error("Kode paket non-tender wajib diisi!")
      else:
        try:
          cursor.execute(
              """
                        INSERT INTO tabel_nontender 
                        (kode_nontender, nama_nontender, jenis_pengadaan, satuan_kerja, nilai_hps, nilai_negosiasi, tanggal_kontrak, nama_pemenang, alamat_pemenang, email_pemenang, telp_pemenang, status_bpjs)
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
              f"Data paket non-tender dengan kode {kode_nontender} berhasil"
              " disimpan!"
          )
        except sqlite3.IntegrityError:
          st.error(f"Kode non-tender '{kode_nontender}' sudah ada!")
        except Exception as e:
          st.error(f"Terjadi kesalahan: {e}")

# TAB 2: EDIT DATA
with tab2:
  st.subheader("Edit Data Berdasarkan Kode Non-Tender")
  df_list = pd.read_sql_query(
      "SELECT kode_nontender, nama_nontender FROM tabel_nontender", conn
  )

  if not df_list.empty:
    df_list["label_edit"] = (
        df_list["kode_nontender"]
        + " - "
        + df_list["nama_nontender"].fillna("")
    )
    pilihan_edit = st.selectbox(
        "Pilih Kode Non-Tender yang ingin diedit:",
        df_list["label_edit"].tolist(),
        key="sel_edit_nt",
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

        with st.form("form_edit_nontender"):
          u_nama_nontender = st.text_input(
              "Nama Paket Non-Tender", value=str(r["nama_nontender"] or "")
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
          u_hps = uc1.number_input(
              "Nilai HPS (Rp)",
              value=float(r["nilai_hps"] or 0.0),
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
              "Status BPJS", ["Belum", "Sudah"], index=stat_idx, key="u_bpjs_nt"
          )

          submit_update = st.form_submit_button(
              "Simpan Perubahan", type="primary"
          )

          if submit_update:
            cursor.execute(
                """
                            UPDATE tabel_nontender 
                            SET nama_nontender=?, jenis_pengadaan=?, satuan_kerja=?, nilai_hps=?, nilai_negosiasi=?, 
                                nama_pemenang=?, alamat_pemenang=?, email_pemenang=?, telp_pemenang=?, status_bpjs=?
                            WHERE kode_nontender=?
                        """,
                (
                    u_nama_nontender,
                    u_jenis_pengadaan,
                    u_satuan_kerja,
                    u_hps,
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
            st.success(f"Data non-tender {kode_pilih} berhasil diperbarui!")
  else:
    st.info("Belum ada data non-tender tersimpan untuk diedit.")

# TAB 3: LAPORAN & SMART ALERT + LOG PENGIRIMAN
with tab3:
  st.subheader("Rekapitulasi Paket Non-Tender & Peringatan Otomatis")

  query_nontender = """
        SELECT kode_nontender, nama_nontender, jenis_pengadaan, satuan_kerja, nilai_hps, nilai_negosiasi, 
               tanggal_kontrak, nama_pemenang, alamat_pemenang, email_pemenang, 
               telp_pemenang, status_bpjs 
        FROM tabel_nontender
    """
  df_nontender = pd.read_sql_query(query_nontender, conn)

  if not df_nontender.empty:
    hari_ini = datetime.now().date()


    def cek_status_notif_nt(row):
      try:
        tgl_str = str(row["tanggal_kontrak"]).split()[0]
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


    df_nontender["status_peringatan"] = df_nontender.apply(
        cek_status_notif_nt, axis=1
    )

    col_f1, col_f2 = st.columns(2)
    filter_bpjs = col_f1.selectbox(
        "Filter Berdasarkan Status BPJS:",
        ["Semua", "Sudah", "Belum"],
        key="f_nt_bpjs",
    )
    filter_alert = col_f2.selectbox(
        "Filter Status Peringatan:",
        ["Semua", "🚨 Wajib Kirim Notifikasi (Jatuh Tempo)"],
        key="f_nt_alert",
    )

    if filter_bpjs != "Semua":
      df_nontender = df_nontender[df_nontender["status_bpjs"] == filter_bpjs]
    if filter_alert != "Semua":
      df_nontender = df_nontender[
          df_nontender["status_peringatan"].str.contains("Wajib Kirim")
      ]

    jumlah_wajib_kirim = len(
        df_nontender[
            df_nontender["status_peringatan"].str.contains("Wajib Kirim")
        ]
    )
    if jumlah_wajib_kirim > 0:
      st.warning(
          f"⚠️ Perhatian: Ada **{jumlah_wajib_kirim} paket** Non-Tender yang"
          " sudah melewati tanggal penetapan pemenang namun status BPJS-nya"
          " masih 'Belum'!"
      )

    st.dataframe(
        df_nontender,
        column_config={
            "kode_nontender": "Kode Non-Tender",
            "nama_nontender": "Nama Paket Non-Tender",
            "jenis_pengadaan": "Jenis Pengadaan",
            "satuan_kerja": "Satuan Kerja",
            "nilai_hps": st.column_config.NumberColumn(
                "Nilai HPS", format="Rp %,d"
            ),
            "nilai_negosiasi": st.column_config.NumberColumn(
                "Nilai Negosiasi", format="Rp %,d"
            ),
            "tanggal_kontrak": "Tgl Penetapan",
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
          list_opsi = (
              df_nontender["kode_nontender"].astype(str)
              + " - "
              + df_nontender["nama_nontender"].fillna("")
          ).tolist()
          pilihan_notif = st.selectbox(
              "Pilih Kode & Nama Paket Non-Tender:",
              list_opsi,
              key="nt_sel_notif",
          )
        else:
          pilihan_notif = None
      except Exception:
        pilihan_notif = None

      if pilihan_notif:
        try:
          kode_pilih = pilihan_notif.split(" - ")[0]
          matched_rows = df_nontender[
              df_nontender["kode_nontender"] == kode_pilih
          ]

          if not matched_rows.empty:
            row_n = matched_rows.iloc[0]

            pemenang = row_n.get("nama_pemenang", "Pemenang") or "Pemenang"
            email_pemenang = row_n.get("email_pemenang", "") or ""
            telp_pemenang = row_n.get("telp_pemenang", "") or ""
            status = row_n.get("status_bpjs", "Belum")
            nilai_nego_nt = row_n.get("nilai_negosiasi", 0.0) or 0.0
            alamat_pemenang_val = row_n.get("alamat_pemenang", "-") or "-"

            if "Wajib Kirim" in str(row_n.get("status_peringatan", "")):
              st.error(
                  "🚨 Status Paket Ini: **Jatuh Tempo (Wajib Kirim Notifikasi"
                  " BPJS)**"
              )

            # --- PRATINJAU PESAN (LENGKAP DENGAN DETAIL KEUANGAN & KONTAK) ---
            st.markdown("### 👁️ Pratinjau Pesan")

            body_email_nt = f"""Kepada Yth. Pimpinan {pemenang},

Sehubungan dengan penetapan pemenang untuk paket Non-Tender {row_n.get('nama_nontender', '')} (Kode: {kode_pilih}), sesuai dengan Peraturan Walikota Kendari dan MoU antara Pemerintah Kota Kendari, Kejaksaan Negeri Kendari dan BPJS, diharapkan agar Saudara segera menunaikan kewajiban Saudara terkait BPJS Ketenagakerjaan.

Hormat kami,
Dinas Tenaga Kerja dan Perindustrian Kota Kendari"""

            wa_text_nt = f"Halo {pemenang},\n\nSehubungan dengan penetapan pemenang untuk paket Non-Tender {row_n.get('nama_nontender', '')} (Kode: {kode_pilih}), sesuai dengan Peraturan Walikota Kendari dan MoU antara Pemerintah Kota Kendari, Kejaksaan Negeri Kendari dan BPJS, diharapkan agar Saudara segera menunaikan kewajiban Saudara terkait BPJS Ketenagakerjaan.\n\nHormat kami,\nDinas Tenaga Kerja dan Perindustrian Kota Kendari"

            body_pic_nt = f"""Kepada Yth. {nama_pic},

Berikut laporan pemantauan kepatuhan BPJS untuk paket Non-Tender:
- Kode Paket: {kode_pilih}
- Nama Paket: {row_n.get('nama_nontender', '')}
- Nama Pemenang: {pemenang}
- Nilai Negosiasi: Rp {nilai_nego_nt:,.2f}
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
                        f"Pemberitahuan Kewajiban BPJS - Non-Tender {kode_pilih}"
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
                        kode_pilih,
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
                        kode_pilih,
                        "Pemenang",
                        email_pemenang,
                        "Email",
                        "Gagal",
                        str(e),
                    )

              if telp_pemenang:
                url_wa = (
                    f"https://wa.me/{telp_pemenang}?text={urllib.parse.quote(wa_text_nt)}"
                )
                if st.button(
                    "📲 Kirim WhatsApp ke Pemenang", key="btn_nt_wa_pem"
                ):
                  catat_log(
                      "Non-Tender",
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
                  "📧 Kirim Laporan Email ke PIC BPJS", key="btn_nt_mail_pic"
              ):
                try:
                  msg = MIMEMultipart()
                  msg["From"] = smtp_email
                  msg["To"] = email_pic
                  msg["Subject"] = f"Laporan Kepatuhan Non-Tender - {kode_pilih}"
                  msg.attach(MIMEText(body_pic_nt, "plain"))

                  server = smtplib.SMTP("smtp.gmail.com", 587)
                  server.starttls()
                  server.login(smtp_email, smtp_pass)
                  server.sendmail(smtp_email, email_pic, msg.as_string())
                  server.quit()
                  st.success("Email laporan ke PIC BPJS terkirim!")
                  catat_log(
                      "Non-Tender",
                      kode_pilih,
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
                      kode_pilih,
                      "PIC BPJS",
                      email_pic,
                      "Email",
                      "Gagal",
                      str(e),
                  )

              if hp_pic:
                wa_pic_text_nt = f"Halo {nama_pic},\n\nLaporan Non-Tender *{kode_pilih}* ({row_n.get('nama_nontender', '')}). Pemenang: {pemenang}. Status BPJS: *{status}*.\n\nMohon ditindaklanjuti.\n\nHormat kami,\nDinas Tenaga Kerja dan Perindustrian Kota Kendari"
                url_wa_pic = f"https://wa.me/{hp_pic}?text={urllib.parse.quote(wa_pic_text_nt)}"

                if st.button(
                    "📲 Log WhatsApp ke PIC BPJS", key="btn_nt_wa_pic_log"
                ):
                  catat_log(
                      "Non-Tender",
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
    st.info("Belum ada data paket non-tender yang tersimpan.")
