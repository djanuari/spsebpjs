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
    page_title="E-Purchasing / Mini Kompetisi", page_icon="🛒", layout="wide"
)

conn = sqlite3.connect("database_spse.db", check_same_thread=False)
cursor = conn.cursor()

# 1. Pastikan tabel utama tercipta lengkap
cursor.execute("""
CREATE TABLE IF NOT EXISTS tabel_epurchasing (
    kode_paket TEXT PRIMARY KEY,
    kode_rup TEXT,
    nama_paket TEXT,
    pagu_paket REAL,
    hps_paket REAL,
    jenis_pengadaan TEXT,
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

# 2. Pengaman otomatis (Auto-add kolom jika tabel sudah terlanjur ada tapi kurang lengkap)
kolom_yang_dibutuhkan = [
    ("kode_rup", "TEXT"),
    ("pagu_paket", "REAL"),
    ("hps_paket", "REAL"),
    ("jenis_pengadaan", "TEXT"),
    ("nilai_kontrak", "REAL"),
    ("alamat_pemenang", "TEXT"),
    ("email_pemenang", "TEXT"),
    ("telp_pemenang", "TEXT"),
    ("tanggal_penetapan", "TEXT"),
    ("status_bpjs", "TEXT")
]

for col_name, col_type in kolom_yang_dibutuhkan:
  try:
    cursor.execute(f"ALTER TABLE tabel_epurchasing ADD COLUMN {col_name} {col_type}")
    conn.commit()
  except sqlite3.OperationalError:
    pass # Kolom sudah ada, abaikan error


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


st.title("🛒 3. Data E-Purchasing / Mini Kompetisi & Kepatuhan BPJS")
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
  st.subheader("Formulir Input E-Purchasing / Mini Kompetisi Baru")
  with st.form("form_tambah_epurchasing", clear_on_submit=True):
    c1, c2 = st.columns(2)
    kode_rup = c1.text_input("1. Kode RUP")
    kode_paket = c2.text_input("2. Kode Paket (Unik)")

    nama_paket = st.text_input("3. Nama Paket")

    c3, c4 = st.columns(2)
    pagu_paket = c3.number_input(
        "4. Pagu Paket (Rp)", min_value=0.0, format="%.2f"
    )
    hps_paket = c4.number_input(
        "5. HPS Paket (Rp)", min_value=0.0, format="%.2f"
    )

    jenis_pengadaan = st.selectbox("6. Jenis Pengadaan", jenis_pengadaan_opsi)
    nama_pemenang = st.text_input("7. Nama Pemenang / Penyedia")

    c5, c6 = st.columns(2)
    nilai_kontrak = c5.number_input(
        "8. Nilai Kontrak (Rp)", min_value=0.0, format="%.2f"
    )
    tanggal_penetapan = c6.date_input("9. Tanggal Penetapan Pemenang")

    alamat_pemenang = st.text_area("10. Alamat Pemenang")

    c7, c8 = st.columns(2)
    email_pemenang = c7.text_input("11. Email Pemenang")
    telp_pemenang = c8.text_input("12. Nomor Telepon Pemenang")

    status_bpjs = st.selectbox(
        "13. Sudah Memenuhi Ketentuan BPJS?", ["Belum", "Sudah"]
    )

    submit_ep = st.form_submit_button(
        "Simpan Data E-Purchasing", type="primary"
    )

    if submit_ep:
      if kode_paket.strip() == "":
        st.error("Kode Paket wajib diisi!")
      else:
        try:
          cursor.execute(
              """
                        INSERT INTO tabel_epurchasing 
                        (kode_paket, kode_rup, nama_paket, pagu_paket, hps_paket, jenis_pengadaan, 
                         nama_pemenang, nilai_kontrak, alamat_pemenang, email_pemenang, telp_pemenang, tanggal_penetapan, status_bpjs)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
              (
                  kode_paket,
                  kode_rup,
                  nama_paket,
                  pagu_paket,
                  hps_paket,
                  jenis_pengadaan,
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
              f"Data E-Purchasing dengan kode paket {kode_paket} berhasil"
              " disimpan!"
          )
        except sqlite3.IntegrityError:
          st.error(f"Kode paket '{kode_paket}' sudah terdaftar!")
        except Exception as e:
          st.error(f"Terjadi kesalahan: {e}")

# TAB 2: EDIT DATA
with tab2:
  st.subheader("Edit Data Berdasarkan Kode Paket")
  df_list = pd.read_sql_query(
      "SELECT kode_paket, nama_paket FROM tabel_epurchasing", conn
  )

  if not df_list.empty:
    df_list["label_edit"] = (
        df_list["kode_paket"] + " - " + df_list["nama_paket"].fillna("")
    )
    pilihan_edit = st.selectbox(
        "Pilih Kode Paket yang ingin diedit:", df_list["label_edit"].tolist()
    )

    if pilihan_edit:
      kode_pilih = pilihan_edit.split(" - ")[0]
      df_row = pd.read_sql_query(
          f"SELECT * FROM tabel_epurchasing WHERE kode_paket = '{kode_pilih}'",
          conn,
      )

      if not df_row.empty:
        r = df_row.iloc[0]
        st.info(f"Sedang mengedit Kode Paket: **{kode_pilih}**")

        with st.form("form_edit_epurchasing"):
          u_rup = st.text_input(
              "Kode RUP", value=str(r["kode_rup"] or "")
          )
          u_nama = st.text_input(
              "Nama Paket", value=str(r["nama_paket"] or "")
          )

          uc1, uc2 = st.columns(2)
          u_pagu = uc1.number_input(
              "Pagu Paket (Rp)",
              value=float(r["pagu_paket"] or 0.0),
              format="%.2f",
          )
          u_hps = uc2.number_input(
              "HPS Paket (Rp)",
              value=float(r["hps_paket"] or 0.0),
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
                            UPDATE tabel_epurchasing 
                            SET kode_rup=?, nama_paket=?, pagu_paket=?, hps_paket=?, jenis_pengadaan=?, 
                                nama_pemenang=?, nilai_kontrak=?, alamat_pemenang=?, email_pemenang=?, telp_pemenang=?, status_bpjs=?
                            WHERE kode_paket=?
                        """,
                (
                    u_rup,
                    u_nama,
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
                f"Data E-Purchasing dengan kode {kode_pilih} berhasil"
                " diperbarui!"
            )
  else:
    st.info("Belum ada data E-Purchasing tersimpan untuk diedit.")

# TAB 3: LAPORAN & SMART ALERT + LOG PENGIRIMAN
with tab3:
  st.subheader("Rekapitulasi Paket E-Purchasing & Peringatan Otomatis")

  query_ep = """
        SELECT kode_rup, kode_paket, nama_paket, pagu_paket, hps_paket, jenis_pengadaan, 
               nama_pemenang, nilai_kontrak, tanggal_penetapan, alamat_pemenang, email_pemenang, 
               telp_pemenang, status_bpjs 
        FROM tabel_epurchasing
    """
  df_ep = pd.read_sql_query(query_ep, conn)

  if not df_ep.empty:
    hari_ini = datetime.now().date()


    def cek_status_notif_ep(row):
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


    df_ep["status_peringatan"] = df_ep.apply(cek_status_notif_ep, axis=1)

    col_f1, col_f2 = st.columns(2)
    filter_bpjs = col_f1.selectbox(
        "Filter Berdasarkan Status BPJS:",
        ["Semua", "Sudah", "Belum"],
        key="f_ep_bpjs",
    )
    filter_alert = col_f2.selectbox(
        "Filter Status Peringatan:",
        ["Semua", "🚨 Wajib Kirim Notifikasi (Jatuh Tempo)"],
        key="f_ep_alert",
    )

    if filter_bpjs != "Semua":
      df_ep = df_ep[df_ep["status_bpjs"] == filter_bpjs]
    if filter_alert != "Semua":
      df_ep = df_ep[df_ep["status_peringatan"].str.contains("Wajib Kirim")]

    jumlah_wajib_kirim = len(
        df_ep[df_ep["status_peringatan"].str.contains("Wajib Kirim")]
    )
    if jumlah_wajib_kirim > 0:
      st.warning(
          f"⚠️ Perhatian: Ada **{jumlah_wajib_kirim} paket** E-Purchasing yang"
          " sudah melewati tanggal penetapan pemenang namun status BPJS-nya"
          " masih 'Belum'!"
      )

    st.dataframe(
        df_ep,
        column_config={
            "kode_rup": "Kode RUP",
            "kode_paket": "Kode Paket",
            "nama_paket": "Nama Paket",
            "pagu_paket": st.column_config.NumberColumn(
                "Pagu Paket", format="Rp %,d"
            ),
            "hps_paket": st.column_config.NumberColumn(
                "HPS Paket", format="Rp %,d"
            ),
            "jenis_pengadaan": "Jenis Pengadaan",
            "nama_pemenang": "Nama Pemenang",
            "nilai_kontrak": st.column_config.NumberColumn(
                "Nilai Kontrak", format="Rp %,d"
            ),
            "tanggal_penetapan": "Tgl Penetapan",
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
        "📨 Pusat Pengiriman Notifikasi (Email & WhatsApp) - E-Purchasing"
    )

    with st.expander(
        "⚙️️ Konfigurasi Pengirim & Kirim Pesan Notifikasi", expanded=True
    ):
      col_smtp1, col_smtp2 = st.columns(2)
      smtp_email = col_smtp1.text_input(
          "Email Instansi / Pengirim",
          value="admin.spse@kendarikota.go.id",
          key="ep_smtp_email",
      )
      smtp_pass = col_smtp2.text_input(
          "Password / App Password Email", type="password", key="ep_smtp_pass"
      )

      col_pic1, col_pic2, col_pic3 = st.columns(3)
      nama_pic = col_pic1.text_input(
          "Nama PIC BPJS", value="Tim BPJS Kendari", key="ep_pic_nama"
      )
      email_pic = col_pic2.text_input(
          "Email PIC BPJS", value="pic.bpjs@kendarikota.go.id", key="ep_pic_email"
      )
      hp_pic = col_pic3.text_input(
          "No. WhatsApp PIC (628...)", value="6281111222233", key="ep_pic_hp"
      )

      st.markdown("---")

      try:
        if not df_ep.empty:
          list_opsi = (
              df_ep["kode_paket"].astype(str)
              + " - "
              + df_ep["nama_paket"].fillna("")
          ).tolist()
          pilihan_notif = st.selectbox(
              "Pilih Kode & Nama Paket E-Purchasing:",
              list_opsi,
              key="ep_sel_notif",
          )
        else:
          pilihan_notif = None
      except Exception:
        pilihan_notif = None

      if pilihan_notif:
        try:
          kode_pilih = pilihan_notif.split(" - ")[0]
          matched_rows = df_ep[df_ep["kode_paket"] == kode_pilih]

          if not matched_rows.empty:
            row_n = matched_rows.iloc[0]

            pemenang = row_n.get("nama_pemenang", "Pemenang") or "Pemenang"
            email_pemenang = row_n.get("email_pemenang", "") or ""
            telp_pemenang = row_n.get("telp_pemenang", "") or ""
            status = row_n.get("status_bpjs", "Belum")
            nilai_kontrak_ep = row_n.get("nilai_kontrak", 0.0) or 0.0
            alamat_pemenang_val = row_n.get("alamat_pemenang", "-") or "-"

            if "Wajib Kirim" in str(row_n.get("status_peringatan", "")):
              st.error(
                  "🚨 Status Paket Ini: **Jatuh Tempo (Wajib Kirim Notifikasi"
                  " BPJS)**"
              )

            st.markdown("### 👁️️ Pratinjau Pesan")

            body_email_ep = f"""Kepada Yth. Pimpinan {pemenang},

Sehubungan dengan penetapan pemenang untuk paket E-Purchasing {row_n.get('nama_paket', '')} (Kode: {kode_pilih}), sesuai dengan Peraturan Walikota Kendari dan MoU antara Pemerintah Kota Kendari, Kejaksaan Negeri Kendari dan BPJS, diharapkan agar Saudara segera menunaikan kewajiban Saudara terkait BPJS Ketenagakerjaan.

Hormat kami,
Dinas Tenaga Kerja dan Perindustrian Kota Kendari"""

            wa_text_ep = f"Halo {pemenang},\n\nSehubungan dengan penetapan pemenang untuk paket E-Purchasing {row_n.get('nama_paket', '')} (Kode: {kode_pilih}), sesuai dengan Peraturan Walikota Kendari dan MoU antara Pemerintah Kota Kendari, Kejaksaan Negeri Kendari dan BPJS, diharapkan agar Saudara segera menunaikan kewajiban Saudara terkait BPJS Ketenagakerjaan.\n\nHormat kami,\nDinas Tenaga Kerja dan Perindustrian Kota Kendari"

            body_pic_ep = f"""Kepada Yth. {nama_pic},

Berikut laporan pemantauan kepatuhan BPJS untuk paket E-Purchasing:
- Kode Paket: {kode_pilih}
- Nama Paket: {row_n.get('nama_paket', '')}
- Nama Pemenang: {pemenang}
- Nilai Kontrak: Rp {nilai_kontrak_ep:,.2f}
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
                    value=body_email_ep,
                    height=140,
                    key="prev_ep_mail",
                )
              with st.expander("📱 Pratinjau WhatsApp Pemenang"):
                st.text_area(
                    "Teks WA:", value=wa_text_ep, height=140, key="prev_ep_wa"
                )
            with col_prev2:
              with st.expander("📄 Pratinjau Laporan Email ke PIC"):
                st.text_area(
                    "Teks Laporan:",
                    value=body_pic_ep,
                    height=160,
                    key="prev_ep_pic",
                )

            st.markdown("---")

            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
              st.markdown("### 🏢 Aksi ke Pemenang")
              if st.button("📧 Kirim Email ke Pemenang", key="btn_ep_mail_pem"):
                if not email_pemenang:
                  st.error("Alamat email pemenang kosong!")
                  catat_log(
                      "E-Purchasing",
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
                        f"Pemberitahuan Kewajiban BPJS - E-Purchasing {kode_pilih}"
                    )
                    msg.attach(MIMEText(body_email_ep, "plain"))

                    server = smtplib.SMTP("smtp.gmail.com", 587)
                    server.starttls()
                    server.login(smtp_email, smtp_pass)
                    server.sendmail(
                        smtp_email, email_pemenang, msg.as_string()
                    )
                    server.quit()
                    st.success("Email ke pemenang berhasil dikirim!")
                    catat_log(
                        "E-Purchasing",
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
                        "E-Purchasing",
                        kode_pilih,
                        "Pemenang",
                        email_pemenang,
                        "Email",
                        "Gagal",
                        str(e),
                    )

              if telp_pemenang:
                url_wa = (
                    f"https://wa.me/{telp_pemenang}?text={urllib.parse.quote(wa_text_ep)}"
                )
                if st.button(
                    "📲 Kirim WhatsApp ke Pemenang", key="btn_ep_wa_pem"
                ):
                  catat_log(
                      "E-Purchasing",
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
                  "📧 Kirim Laporan Email ke PIC BPJS", key="btn_ep_mail_pic"
              ):
                try:
                  msg = MIMEMultipart()
                  msg["From"] = smtp_email
                  msg["To"] = email_pic
                  msg["Subject"] = (
                      f"Laporan Kepatuhan E-Purchasing - {kode_pilih}"
                  )
                  msg.attach(MIMEText(body_pic_ep, "plain"))

                  server = smtplib.SMTP("smtp.gmail.com", 587)
                  server.starttls()
                  server.login(smtp_email, smtp_pass)
                  server.sendmail(smtp_email, email_pic, msg.as_string())
                  server.quit()
                  st.success("Email laporan ke PIC BPJS terkirim!")
                  catat_log(
                      "E-Purchasing",
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
                      "E-Purchasing",
                      kode_pilih,
                      "PIC BPJS",
                      email_pic,
                      "Email",
                      "Gagal",
                      str(e),
                  )

              if hp_pic:
                wa_pic_text_ep = f"Halo {nama_pic},\n\nLaporan E-Purchasing *{kode_pilih}* ({row_n.get('nama_paket', '')}). Pemenang: {pemenang}. Status BPJS: *{status}*.\n\nMohon ditindaklanjuti.\n\nHormat kami,\nDinas Tenaga Kerja dan Perindustrian Kota Kendari"
                url_wa_pic = f"https://wa.me/{hp_pic}?text={urllib.parse.quote(wa_pic_text_ep)}"

                if st.button(
                    "📲 Log WhatsApp ke PIC BPJS", key="btn_ep_wa_pic_log"
                ):
                  catat_log(
                      "E-Purchasing",
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
    st.info("Belum ada data E-Purchasing yang tersimpan.")
