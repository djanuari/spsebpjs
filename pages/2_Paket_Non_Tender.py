from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import urllib.parse
from api_connector import get_all_spse_data, supabase, upsert_spse_data
import pandas as pd
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning("⚠️ Anda belum login. Silakan kembali ke halaman utama.")
  st.stop()

st.set_page_config(
    page_title="Non-Tender / Pengadaan Langsung", page_icon="📦", layout="wide"
)

st.title("📦 2. Data Non-Tender / Pengadaan Langsung & Kepatuhan BPJS")
st.markdown("---")

tab_import, tab1, tab2, tab3 = st.tabs(
    [
        "📤 Impor Excel",
        "➕ Tambah Data",
        "✏️ Edit / Hapus Data",
        "📋 Daftar & Laporan",
    ]
)

jenis_pengadaan_opsi = [
    "Pekerjaan Konstruksi",
    "Jasa Konsultansi Badan Usaha Konstruksi",
    "Jasa Konsultansi Non Badan Usaha Konstruksi",
    "Jasa Lainnya",
    "Pengadaan Barang",
]

tahapan_opsi = ["Pemilihan Berlangsung", "Pemilihan Selesai"]

# TAB IMPORT EXCEL: Sinkronisasi langsung persis seperti file rujukan Anda
with tab_import:
  st.subheader("📤 Unggah File Excel Rujukan Non-Tender")
  st.info(
      "Unggah file Excel Anda di sini. Sistem akan otomatis membaca seluruh"
      " kolom (`jenis_pengadaan`, `satuan_kerja`, `tahapan_pengadaan`,"
      " `nilai_kontrak`, dll) dan menyimpannya ke database agar sama persis"
      " tanpa ada yang kosong (-)."
  )

  uploaded_excel = st.file_uploader(
      "Pilih file Excel (.xlsx)", type=["xlsx", "xls"]
  )
  if uploaded_excel is not None:
    try:
      df_import = pd.read_excel(uploaded_excel)
      st.write(
          f"Berhasil membaca file dengan {len(df_import)} baris data. Contoh"
          " data teratas:"
      )
      st.dataframe(df_import.head(3), use_container_width=True)

      if st.button("🚀 Proses & Simpan Data Excel ke Database", type="primary"):
        success_count = 0
        with st.spinner("Sedang menyinkronkan data ke Supabase..."):
          for _, row in df_import.iterrows():
            kode = str(row.get("kode_nontender", ""))
            if not kode or kode.lower() == "nan":
              continue

            # Petakan persis ke kolom database
            data_row = {
                "id_paket": kode.strip(),
                "nama_paket": str(row.get("nama_nontender", "") or ""),
                "kategori": "Non-Tender",
                "pagu": float(row.get("nilai_kontrak", 0.0) or 0.0),
                "hps": 0.0,
                "pemenang": str(row.get("nama_pemenang", "") or ""),
                "status_kepatuhan": str(
                    row.get("status_kepatuhan", "Belum") or "Belum"
                ),
                "tanggal_tarik": str(
                    row.get("tanggal selesai pemilihan", "") or ""
                ),
                "email_pemenang": str(row.get("email", "") or ""),
                "telp_pemenang": str(row.get("telepon", "") or ""),
                "satuan_kerja": str(row.get("satuan_kerja", "") or ""),
                "jenis_pengadaan": str(row.get("jenis_pengadaan", "") or ""),
                "tahapan_pengadaan": str(
                    row.get("tahapan_pengadaan", "") or ""
                ),
                "alamat": str(row.get("Alamat", "") or ""),
            }
            if upsert_spse_data(data_row):
              success_count += 1

        st.success(
            f"Berhasil menyinkronkan {success_count} data Non-Tender ke database"
            " cloud!"
        )
        st.rerun()
    except Exception as e:
      st.error(f"Gagal membaca file Excel: {e}")

# Ambil data dari Supabase Cloud dan filter kategori Non-Tender
df_all = get_all_spse_data()
if not df_all.empty and "kategori" in df_all.columns:
  df_nontender = df_all[df_all["kategori"].str.lower() == "non-tender"]
else:
  df_nontender = pd.DataFrame()

# TAB 1: TAMBAH DATA
with tab1:
  st.subheader("Formulir Input Non-Tender Baru")
  with st.form("form_tambah_nontender", clear_on_submit=True):
    kode_nontender = st.text_input("1. kode_nontender (Primary Key)")
    nama_nontender = st.text_input("2. nama_nontender")

    c1, c2 = st.columns(2)
    jenis_pengadaan = c1.selectbox("3. jenis_pengadaan", jenis_pengadaan_opsi)
    satuan_kerja = c2.text_input("4. satuan_kerja")

    c3, c4 = st.columns(2)
    tahapan_pengadaan = c3.selectbox("5. tahapan_pengadaan", tahapan_opsi)
    nama_pemenang = c4.text_input("6. nama_pemenang")

    c5, c6 = st.columns(2)
    tanggal_selesai = c5.date_input("7. tanggal selesai pemilihan")
    nilai_kontrak = c6.number_input(
        "8. nilai_kontrak (Rp)", min_value=0.0, format="%.2f"
    )

    status_bpjs = c4.selectbox("9. status_kepatuhan", ["Belum", "Sudah"])
    alamat = st.text_area("10. Alamat")

    c7, c8 = st.columns(2)
    email = c7.text_input("11. email")
    telepon = c8.text_input("12. telepon")

    submit_nt = st.form_submit_button("Simpan Data Non-Tender", type="primary")

    if submit_nt:
      if kode_nontender.strip() == "":
        st.error("kode_nontender wajib diisi sebagai pengenal unik!")
      else:
        data_baru = {
            "id_paket": kode_nontender.strip(),
            "nama_paket": nama_nontender,
            "kategori": "Non-Tender",
            "pagu": nilai_kontrak,
            "hps": 0.0,
            "pemenang": nama_pemenang,
            "status_kepatuhan": status_bpjs,
            "tanggal_tarik": str(tanggal_selesai),
            "email_pemenang": email,
            "telp_pemenang": telepon,
            "satuan_kerja": satuan_kerja,
            "jenis_pengadaan": jenis_pengadaan,
            "tahapan_pengadaan": tahapan_pengadaan,
            "alamat": alamat,
        }
        if upsert_spse_data(data_baru):
          st.success(
              f"Data Non-Tender dengan kode {kode_nontender} berhasil disimpan"
              " ke cloud Supabase!"
          )
          st.rerun()

# TAB 2: EDIT & HAPUS DATA
with tab2:
  st.subheader("Edit atau Hapus Data Berdasarkan kode_nontender")
  if not df_nontender.empty and "id_paket" in df_nontender.columns:
    df_nontender["label_edit"] = (
        df_nontender["id_paket"].astype(str)
        + " - "
        + df_nontender["nama_paket"].fillna("")
    )
    pilihan_edit = st.selectbox(
        "Pilih kode_nontender yang ingin dikelola:",
        df_nontender["label_edit"].tolist(),
    )

    if pilihan_edit:
      kode_pilih = pilihan_edit.split(" - ")[0]
      matched_row = df_nontender[df_nontender["id_paket"].astype(str) == kode_pilih]

      if not matched_row.empty:
        r = matched_row.iloc[0]
        st.info(f"Sedang mengelola kode_nontender: **{kode_pilih}**")

        with st.form(f"form_edit_nontender_{kode_pilih}"):
          u_nama = st.text_input(
              "nama_nontender", value=str(r.get("nama_paket", "") or "")
          )
          u_pemenang = st.text_input(
              "nama_pemenang", value=str(r.get("pemenang", "") or "")
          )

          uc1, uc2 = st.columns(2)
          u_nilai = uc1.number_input(
              "nilai_kontrak (Rp)",
              value=float(r.get("pagu", 0.0) or 0.0),
              format="%.2f",
          )
          stat_idx = (
              ["Belum", "Sudah"].index(r.get("status_kepatuhan", "Belum"))
              if r.get("status_kepatuhan") in ["Belum", "Sudah"]
              else 0
          )
          u_bpjs = uc2.selectbox(
              "status_kepatuhan", ["Belum", "Sudah"], index=stat_idx
          )

          uc3, uc4 = st.columns(2)
          u_email = uc3.text_input(
              "email", value=str(r.get("email_pemenang", "") or "")
          )
          u_telp = uc4.text_input(
              "telepon", value=str(r.get("telp_pemenang", "") or "")
          )

          u_satker = st.text_input(
              "satuan_kerja", value=str(r.get("satuan_kerja", "") or "")
          )
          u_jenis = st.text_input(
              "jenis_pengadaan",
              value=str(r.get("jenis_pengadaan", "") or ""),
          )
          u_tahap = st.text_input(
              "tahapan_pengadaan",
              value=str(r.get("tahapan_pengadaan", "") or ""),
          )
          u_alamat = st.text_area(
              "Alamat", value=str(r.get("alamat", "") or "")
          )

          submit_update = st.form_submit_button(
              "Simpan Perubahan", type="primary"
          )

          if submit_update:
            data_update = {
                "id_paket": kode_pilih,
                "nama_paket": u_nama,
                "kategori": "Non-Tender",
                "pagu": u_nilai,
                "hps": float(r.get("hps", 0.0) or 0.0),
                "pemenang": u_pemenang,
                "status_kepatuhan": u_bpjs,
                "tanggal_tarik": str(r.get("tanggal_tarik", "")),
                "email_pemenang": u_email,
                "telp_pemenang": u_telp,
                "satuan_kerja": u_satker,
                "jenis_pengadaan": u_jenis,
                "tahapan_pengadaan": u_tahap,
                "alamat": u_alamat,
            }
            if upsert_spse_data(data_update):
              st.success(
                  f"Data Non-Tender dengan kode {kode_pilih} berhasil"
                  " diperbarui di cloud!"
              )
              st.rerun()

        st.markdown("---")
        st.warning(
            "⚠️ Ingin menghapus data paket ini dari database cloud secara"
            " permanen?"
        )
        if st.button(
            f"🗑️ Hapus Paket Non-Tender ({kode_pilih})",
            type="secondary",
            key=f"del_nt_{kode_pilih}",
        ):
          try:
            supabase.table("tabel_spse_bpjs").delete().eq(
                "id_paket", kode_pilih
            ).execute()
            st.success(
                f"Data Non-Tender dengan kode {kode_pilih} berhasil dihapus dari"
                " cloud!"
            )
            st.rerun()
          except Exception as e:
            st.error(f"Gagal menghapus data: {e}")

    st.markdown("---")
    st.error("🚨 Zona Bahaya: Hapus Seluruh Data Non-Tender")
    with st.expander("⚠ Klik untuk opsi Hapus Semua Data Non-Tender"):
      st.warning(
          "Tindakan ini akan menghapus **seluruh** data Non-Tender dari"
          " database cloud secara permanen dan tidak dapat dikembalikan."
      )
      konfirmasi_hapus_semua = st.checkbox(
          "Saya yakin ingin menghapus seluruh data Non-Tender",
          key="chk_hapus_semua_nt",
      )
      if st.button(
          "🗑️ Hapus SEMUA Data Non-Tender Sekarang", type="primary"
      ):
        if konfirmasi_hapus_semua:
          try:
            supabase.table("tabel_spse_bpjs").delete().eq(
                "kategori", "Non-Tender"
            ).execute()
            st.success(
                "Seluruh data Non-Tender berhasil dihapus dari database cloud!"
            )
            st.rerun()
          except Exception as e:
            st.error(f"Gagal menghapus seluruh data: {e}")
        else:
          st.error(
              "Mohon centang kotak konfirmasi terlebih dahulu sebelum"
              " menghapus semua data."
          )
  else:
    st.info("Belum ada data Non-Tender tersimpan di cloud.")

# TAB 3: LAPORAN & NOTIFIKASI
with tab3:
  st.subheader("Rekapitulasi Paket Non-Tender & Peringatan Otomatis")
  if not df_nontender.empty:

    def evaluasi_berdasarkan_tanggal(row):
      status = str(row.get("status_kepatuhan", "Belum")).capitalize()
      tgl_str = str(
          row.get("tanggal_tarik", "")
          or row.get("tanggal selesai pemilihan", "")
      ).split(" ")[0]

      if status == "Sudah":
        return "✅ Selesai / Patuh"

      try:
        tgl_kontrak = datetime.strptime(tgl_str, "%Y-%m-%d")
        selisih_hari = (datetime.now() - tgl_kontrak).days

        if selisih_hari >= 1:
          return (
              f"🚨 URGENT: H+{selisih_hari} Selesai (Wajib Kirim Notifikasi)"
          )
        elif selisih_hari == 0:
          return "⚠️ Hari H Selesai Pemilihan"
        else:
          return "📅 Jadwal Mendatang"
      except Exception:
        return "🚨 Wajib Kirim Notifikasi (Belum Patuh)"

    df_tampil = pd.DataFrame()

    # Memetakan langsung dari kolom database Supabase secara bersih
    df_tampil["kode_nontender"] = df_nontender.get("id_paket", pd.Series()).fillna(
        "-"
    )
    df_tampil["nama_nontender"] = df_nontender.get(
        "nama_paket", pd.Series()
    ).fillna("-")
    df_tampil["jenis_pengadaan"] = df_nontender.get(
        "jenis_pengadaan", pd.Series()
    ).fillna("-")
    df_tampil["satuan_kerja"] = df_nontender.get(
        "satuan_kerja", pd.Series()
    ).fillna("-")
    df_tampil["tahapan_pengadaan"] = df_nontender.get(
        "tahapan_pengadaan", pd.Series()
    ).fillna("-")
    df_tampil["nama_pemenang"] = df_nontender.get(
        "pemenang", pd.Series()
    ).fillna("-")
    df_tampil["tanggal selesai pemilihan"] = df_nontender.get(
        "tanggal_tarik", pd.Series()
    ).fillna("-")
    df_tampil["nilai_kontrak"] = df_nontender.get("pagu", pd.Series()).fillna(
        0.0
    )
    df_tampil["Alamat"] = df_nontender.get("alamat", pd.Series()).fillna("-")
    df_tampil["email"] = df_nontender.get(
        "email_pemenang", pd.Series()
    ).fillna("-")
    df_tampil["telepon"] = df_nontender.get("telp_pemenang", pd.Series()).fillna(
        "-"
    )
    df_tampil["status_kepatuhan"] = df_nontender.get(
        "status_kepatuhan", pd.Series()
    ).fillna("Belum")

    df_tampil["Evaluasi_Otomatis"] = df_nontender.apply(
        evaluasi_berdasarkan_tanggal, axis=1
    )

    # Pengurutan: Pemilihan Berlangsung di atas, Status Belum di atas
    df_tampil["_sort_tahapan"] = df_tampil["tahapan_pengadaan"].apply(
        lambda x: 0 if "Pemilihan Berlangsung" in str(x) else 1
    )
    df_tampil["_sort_status"] = df_tampil["status_kepatuhan"].apply(
        lambda x: 0 if str(x).lower() == "belum" else 1
    )

    df_tampil = df_tampil.sort_values(
        by=["_sort_tahapan", "_sort_status"], ascending=[True, True]
    ).drop(columns=["_sort_tahapan", "_sort_status"])

    total_urgent = df_tampil["Evaluasi_Otomatis"].str.contains("URGENT").sum()
    total_belum = (
        df_tampil["status_kepatuhan"].str.capitalize() == "Belum"
    ).sum()

    if total_urgent > 0:
      st.error(
          f"🚨 **Peringatan Sistem:** Ditemukan **{total_urgent} paket** dari"
          f" total **{total_belum} paket** belum patuh yang sudah melewati"
          " jadwal (>= H+1). **Wajib segera dikirimi pesan notifikasi!**"
      )
    else:
      st.warning(
          f"⚠️ Ada **{total_belum} paket** yang status kepatuhannya masih"
          " 'Belum'."
      )

    st.dataframe(
        df_tampil,
        column_config={
            "kode_nontender": "kode_nontender",
            "nama_nontender": "nama_nontender",
            "jenis_pengadaan": "jenis_pengadaan",
            "satuan_kerja": "satuan_kerja",
            "tahapan_pengadaan": "tahapan_pengadaan",
            "nama_pemenang": "nama_pemenang",
            "tanggal selesai pemilihan": "tanggal selesai pemilihan",
            "nilai_kontrak": st.column_config.NumberColumn(
                "nilai_kontrak", format="Rp %.2f"
            ),
            "Alamat": "Alamat",
            "email": "email",
            "telepon": "telepon",
            "status_kepatuhan": "status_kepatuhan",
            "Evaluasi_Otomatis": "Status Peringatan (H+1)",
        },
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.subheader("📥 Unduh Laporan Data Non-Tender")
    csv_data = df_tampil.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Unduh Laporan Non-Tender ke Format CSV (.csv)",
        data=csv_data,
        file_name="Laporan_Kepatuhan_BPJS_NonTender.csv",
        mime="text/csv",
        type="primary",
    )

    st.markdown("---")
    st.subheader(
        "📨 Pusat Pengiriman Notifikasi (Email & WhatsApp) - Non-Tender"
    )

    with st.expander(
        "⚙️ Konfigurasi & Kirim Pesan Otomatis (Pemenang & PIC BPJS)",
        expanded=True,
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

      st.markdown("---")
      col_pic1, col_pic2 = st.columns(2)
      email_pic = col_pic1.text_input(
          "Email PIC BPJS",
          value="pic.bpjs@kendarikota.go.id",
          key="nt_pic_email",
      )
      hp_pic = col_pic2.text_input(
          "No. WhatsApp PIC BPJS (628...)",
          value="6281111222233",
          key="nt_pic_hp",
      )

      list_opsi_nt = (
          df_nontender["id_paket"].astype(str)
          + " - "
          + df_nontender["nama_paket"].fillna("")
      ).tolist()
      pilihan_notif_nt = st.selectbox(
          "Pilih kode_nontender & nama_nontender:",
          list_opsi_nt,
      )

      if pilihan_notif_nt:
        kode_pilih_nt = pilihan_notif_nt.split(" - ")[0]
        matched_rows_nt = df_nontender[
            df_nontender["id_paket"].astype(str) == kode_pilih_nt
        ]

        if not matched_rows_nt.empty:
          row_n = matched_rows_nt.iloc[0]
          pemenang = row_n.get("pemenang", "Penyedia") or "Penyedia"

          raw_email = row_n.get("email_pemenang", "")
          email_tujuan = (
              str(raw_email).strip()
              if raw_email and str(raw_email).lower() != "nan"
              else ""
          )

          raw_telp = row_n.get("telp_pemenang", "")
          telp_tujuan = (
              str(raw_telp).strip()
              if raw_telp and str(raw_telp).lower() != "nan"
              else ""
          )

          tgl_selesai_val = str(row_n.get("tanggal_tarik", "-"))
          status_pilih = row_n.get("status_kepatuhan", "Belum")

          st.info(
              f"📌 **Detail Paket Terpilih:**\n- Tanggal Selesai Pemilihan:"
              f" `{tgl_selesai_val}`\n- Status Kepatuhan:"
              f" `{status_pilih}`\n- Email Pemenang:"
              f" `{email_tujuan if email_tujuan else 'Belum ada email terdaftar'}`\n- No."
              f" WhatsApp Pemenang:"
              f" `{telp_tujuan if telp_tujuan else 'Belum ada nomor WA terdaftar'}`"
          )

          body_email_nt = f"""Kepada Yth. Pimpinan {pemenang},

Sehubungan dengan selesainya proses pemilihan paket Non-Tender {row_n.get('nama_paket', '')} (kode_nontender: {kode_pilih_nt}) pada tanggal {tgl_selesai_val}, sesuai dengan Peraturan Walikota Kendari dan MoU antara Pemerintah Kota Kendari, Kejaksaan Negeri Kendari dan BPJS, diharapkan agar Saudara segera menunaikan kewajiban kepatuhan BPJS Ketenagakerjaan mulai hari ini (sehari setelah tanggal selesai pemilihan).

Hormat kami,
Dinas Tenaga Kerja dan Perindustrian Kota Kendari"""

          wa_text_nt = f"Halo {pemenang},\n\nSehubungan dengan selesainya proses pemilihan paket Non-Tender {row_n.get('nama_paket', '')} (kode_nontender: {kode_pilih_nt}) pada tanggal {tgl_selesai_val}, sesuai dengan Peraturan Walikota Kendari dan MoU antara Pemerintah Kota Kendari, Kejaksaan Negeri Kendari dan BPJS, diharapkan agar Saudara segera menunaikan kewajiban kepatuhan BPJS Ketenagakerjaan mulai hari ini.\n\nHormat kami,\nDinas Tenaga Kerja dan Perindustrian Kota Kendari"

          body_email_pic = f"""Kepada Yth. Tim PIC BPJS,

Berikut disampaikan monitoring kepatuhan BPJS paket Non-Tender (aktif mulai H+1 tanggal selesai pemilihan):
- kode_nontender: {kode_pilih_nt}
- nama_nontender: {row_n.get('nama_paket', '')}
- Tanggal Selesai: {tgl_selesai_val}
- Nama Pemenang: {pemenang}
- Status BPJS: {status_pilih}

Mohon kiranya dapat diverifikasi dan ditindaklanjuti sesuai ketentuan yang berlaku.

Hormat kami,
Admin SPSE Pemerintah Kota Kendari"""

          wa_text_pic = f"Halo Tim PIC BPJS,\n\nBerikut monitoring kepatuhan paket Non-Tender (aktif mulai H+1 selesai pemilihan):\n- kode_nontender: {kode_pilih_nt}\n- nama_nontender: {row_n.get('nama_paket', '')}\n- Tgl Selesai: {tgl_selesai_val}\n- Pemenang: {pemenang}\n- Status BPJS: {status_pilih}\n\nTerima kasih."

          with st.expander("📄 Pratinjau Pesan (Pemenang & PIC BPJS)"):
            st.markdown("**1. Pesan untuk Pemenang:**")
            st.text_area("Teks Email Pemenang:", value=body_email_nt, height=100)
            st.text_area("Teks WA Pemenang:", value=wa_text_nt, height=100)
            st.markdown("---")
            st.markdown("**2. Pesan untuk PIC BPJS:**")
            st.text_area("Teks Email PIC BPJS:", value=body_email_pic, height=100)
            st.text_area("Teks WA PIC BPJS:", value=wa_text_pic, height=100)

          st.markdown("### 🚀 Aksi Pengiriman Pesan")
          col_a1, col_a2 = st.columns(2)

          with col_a1:
            st.markdown("#### Kirim ke Pemenang")
            if st.button("📧 Kirim Email ke Pemenang", key="btn_send_email_nt"):
              if not email_tujuan or "@" not in email_tujuan:
                st.error("Email pemenang belum valid atau kosong!")
              else:
                try:
                  msg = MIMEMultipart()
                  msg["From"] = smtp_email
                  msg["To"] = email_tujuan
                  msg["Subject"] = (
                      f"Pemberitahuan Kepatuhan BPJS - Non-Tender"
                      f" {kode_pilih_nt}"
                  )
                  msg.attach(MIMEText(body_email_nt, "plain"))

                  server = smtplib.SMTP("smtp.gmail.com", 587)
                  server.starttls()
                  server.login(smtp_email, smtp_pass)
                  server.sendmail(smtp_email, email_tujuan, msg.as_string())
                  server.quit()
                  st.success(
                      f"Email berhasil dikirim ke Pemenang ({email_tujuan})!"
                  )
                except Exception as e:
                  st.error(
                      f"Gagal mengirim email (pastikan App Password benar): {e}"
                  )

            if telp_tujuan:
              encoded_wa = urllib.parse.quote(wa_text_nt)
              wa_url = f"https://wa.me/{telp_tujuan}?text={encoded_wa}"
              st.markdown(
                  f'<a href="{wa_url}" target="_blank"><button'
                  ' style="background-color:#25D366; color:white; border:none;'
                  " padding:10px 20px; border-radius:5px; cursor:pointer; width:"
                  '100%; font-weight:bold; margin-top:5px;">💬 Kirim WhatsApp ke'
                  " Pemenang</button></a>",
                  unsafe_allow_html=True,
              )
            else:
              st.warning("Nomor WhatsApp pemenang belum tersedia.")

          with col_a2:
            st.markdown("#### Kirim ke PIC BPJS")
            if st.button(
                "📧 Kirim Email ke PIC BPJS", key="btn_send_email_pic_nt"
            ):
              if not email_pic or "@" not in email_pic:
                st.error("Email PIC BPJS belum valid atau kosong!")
              else:
                try:
                  msg_pic = MIMEMultipart()
                  msg_pic["From"] = smtp_email
                  msg_pic["To"] = email_pic
                  msg_pic["Subject"] = (
                      f"Laporan Kepatuhan BPJS Non-Tender - {kode_pilih_nt}"
                  )
                  msg_pic.attach(MIMEText(body_email_pic, "plain"))

                  server = smtplib.SMTP("smtp.gmail.com", 587)
                  server.starttls()
                  server.login(smtp_email, smtp_pass)
                  server.sendmail(smtp_email, email_pic, msg_pic.as_string())
                  server.quit()
                  st.success(
                      f"Email berhasil dikirim ke PIC BPJS ({email_pic})!"
                  )
                except Exception as e:
                  st.error(
                      f"Gagal mengirim email ke PIC (pastikan App Password"
                      f" benar): {e}"
                  )

            if hp_pic:
              encoded_wa_pic = urllib.parse.quote(wa_text_pic)
              wa_url_pic = f"https://wa.me/{hp_pic}?text={encoded_wa_pic}"
              st.markdown(
                  f'<a href="{wa_url_pic}" target="_blank"><button'
                  ' style="background-color:#25D366; color:white; border:none;'
                  " padding:10px 20px; border-radius:5px; cursor:pointer; width:"
                  '100%; font-weight:bold; margin-top:5px;">💬 Kirim WhatsApp ke'
                  " PIC BPJS</button></a>",
                  unsafe_allow_html=True,
              )
            else:
              st.warning("Nomor WhatsApp PIC BPJS belum diisi.")
  else:
    st.info("Belum ada data Non-Tender tersimpan di cloud.")
