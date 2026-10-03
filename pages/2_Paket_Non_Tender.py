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
        data_baru = {
            "id_paket": kode_nontender.strip(),
            "nama_paket": nama_nontender,
            "kategori": "Non-Tender",
            "pagu": nilai_negosiasi,
            "hps": nilai_hps,
            "pemenang": nama_pemenang,
            "status_kepatuhan": status_bpjs,
            "tanggal_tarik": str(tanggal_kontrak),
            "email_pemenang": email_pemenang,
            "telp_pemenang": telp_pemenang,
            "keterangan": f"Satuan Kerja: {satuan_kerja} | Jenis: {jenis_pengadaan} | Alamat: {alamat_pemenang}",
        }
        if upsert_spse_data(data_baru):
          st.success(
              f"Data Non-Tender dengan kode {kode_nontender} berhasil disimpan ke"
              " cloud Supabase!"
          )
          st.rerun()

# TAB 2: EDIT & HAPUS DATA
with tab2:
  st.subheader("Edit atau Hapus Data Berdasarkan Kode Non-Tender")
  if not df_nontender.empty and "id_paket" in df_nontender.columns:
    df_nontender["label_edit"] = (
        df_nontender["id_paket"].astype(str)
        + " - "
        + df_nontender["nama_paket"].fillna("")
    )
    pilihan_edit = st.selectbox(
        "Pilih Kode Non-Tender yang ingin dikelola:",
        df_nontender["label_edit"].tolist(),
    )

    if pilihan_edit:
      kode_pilih = pilihan_edit.split(" - ")[0]
      matched_row = df_nontender[df_nontender["id_paket"].astype(str) == kode_pilih]

      if not matched_row.empty:
        r = matched_row.iloc[0]
        st.info(f"Sedang mengelola Kode Non-Tender: **{kode_pilih}**")

        with st.form(f"form_edit_nontender_{kode_pilih}"):
          u_nama = st.text_input(
              "Nama Paket", value=str(r.get("nama_paket", "") or "")
          )
          uc1, uc2 = st.columns(2)
          u_hps = uc1.number_input(
              "Nilai HPS (Rp)",
              value=float(r.get("hps", 0.0) or 0.0),
              format="%.2f",
          )
          u_nego = uc2.number_input(
              "Nilai Negosiasi (Rp)",
              value=float(r.get("pagu", 0.0) or 0.0),
              format="%.2f",
          )

          u_pemenang = st.text_input(
              "Nama Pemenang", value=str(r.get("pemenang", "") or "")
          )
          stat_idx = (
              ["Belum", "Sudah"].index(r.get("status_kepatuhan", "Belum"))
              if r.get("status_kepatuhan") in ["Belum", "Sudah"]
              else 0
          )
          u_bpjs = st.selectbox(
              "Status BPJS", ["Belum", "Sudah"], index=stat_idx
          )

          uc5, uc6 = st.columns(2)
          u_email = uc5.text_input(
              "Email Pemenang",
              value=str(r.get("email_pemenang", "") or ""),
          )
          u_telp = uc6.text_input(
              "Nomor Telepon Pemenang",
              value=str(r.get("telp_pemenang", "") or ""),
          )

          u_ket = st.text_area(
              "Keterangan / Satuan Kerja / Alamat",
              value=str(r.get("keterangan", "") or ""),
          )

          submit_update = st.form_submit_button(
              "Simpan Perubahan", type="primary"
          )

          if submit_update:
            data_update = {
                "id_paket": kode_pilih,
                "nama_paket": u_nama,
                "kategori": "Non-Tender",
                "pagu": u_nego,
                "hps": u_hps,
                "pemenang": u_pemenang,
                "status_kepatuhan": u_bpjs,
                "tanggal_tarik": str(r.get("tanggal_tarik", "")),
                "email_pemenang": u_email,
                "telp_pemenang": u_telp,
                "keterangan": u_ket,
            }
            if upsert_spse_data(data_update):
              st.success(
                  f"Data Non-Tender dengan kode {kode_pilih} berhasil"
                  " diperbarui di cloud!"
              )
              st.rerun()

        # Sistem Penghapusan Paket dari Database Supabase
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
  else:
    st.info("Belum ada data Non-Tender tersimpan di cloud.")

# TAB 3: LAPORAN & NOTIFIKASI
with tab3:
  st.subheader("Rekapitulasi Paket Non-Tender & Peringatan Otomatis")
  if not df_nontender.empty:
    # --- LOGIKA NOTIFIKASI PERINGATAN OTOMATIS ---
    def cek_notifikasi_status(row):
      status = str(row.get("status_kepatuhan", "Belum")).capitalize()
      if status == "Belum":
        return "🚨 Wajib Kirim Notifikasi (Belum Patuh)"
      else:
        return "✅ Selesai / Patuh"

    df_tampil = pd.DataFrame()
    df_tampil["kode_nontender"] = df_nontender.get("id_paket", "")
    df_tampil["nama_nontender"] = df_nontender.get("nama_paket", "")

    df_tampil["jenis_pengadaan"] = df_nontender.get("keterangan", "").apply(
        lambda x: (
            str(x).split("|")[1].replace("Jenis:", "").strip()
            if "|" in str(x) and len(str(x).split("|")) > 1
            else "-"
        )
    )
    df_tampil["satuan_kerja"] = df_nontender.get("keterangan", "").apply(
        lambda x: (
            str(x).split("|")[0].replace("Satuan Kerja:", "").strip()
            if "|" in str(x)
            else "-"
        )
    )

    df_tampil["nilai_hps"] = df_nontender.get("hps", 0.0)
    df_tampil["nilai_negosiasi"] = df_nontender.get("pagu", 0.0)
    df_tampil["tanggal_kontrak"] = df_nontender.get("tanggal_tarik", "")
    df_tampil["nama_pemenang"] = df_nontender.get("pemenang", "")

    df_tampil["alamat_pemenang"] = df_nontender.get("keterangan", "").apply(
        lambda x: (
            str(x).split("Alamat:")[1].strip()
            if "Alamat:" in str(x)
            else "-"
        )
    )
    df_tampil["email_pemenang"] = df_nontender.get("email_pemenang", "")
    df_tampil["telp_pemenang"] = df_nontender.get("telp_pemenang", "")
    df_tampil["Status"] = df_nontender.get("status_kepatuhan", "Belum")
    df_tampil["Peringatan_Notif"] = df_nontender.apply(
        cek_notifikasi_status, axis=1
    )

    # Tampilkan ringkasan jumlah paket yang wajib dikirim pesan
    total_belum = (df_tampil["Status"].str.capitalize() == "Belum").sum()
    if total_belum > 0:
      st.error(
          f"🚨 Perhatian: Ada **{total_belum} paket Non-Tender** yang status"
          " kepatuhan BPJS-nya masih **Belum** dan memerlukan pengiriman"
          " pesan/notifikasi segera!"
      )
    else:
      st.success(
          "✅ Seluruh paket Non-Tender telah memenuhi ketentuan kepatuhan"
          " BPJS."
      )

    st.dataframe(
        df_tampil,
        column_config={
            "kode_nontender": "kode_nontender",
            "nama_nontender": "nama_nontender",
            "jenis_pengadaan": "jenis_pengadaan",
            "satuan_kerja": "satuan_kerja",
            "nilai_hps": st.column_config.NumberColumn(
                "nilai_hps", format="Rp %.2f"
            ),
            "nilai_negosiasi": st.column_config.NumberColumn(
                "nilai_negosiasi", format="Rp %.2f"
            ),
            "tanggal_kontrak": "tanggal_kontrak",
            "nama_pemenang": "nama_pemenang",
            "alamat_pemenang": "alamat_pemenang",
            "email_pemenang": "email_pemenang",
            "telp_pemenang": "telp_pemenang",
            "Status": "Status",
            "Peringatan_Notif": "Peringatan Notifikasi",
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
          "Pilih Kode & Nama Paket Non-Tender:", list_opsi_nt, key="nt_sel_notif"
      )

      if pilihan_notif_nt:
        kode_pilih_nt = pilihan_notif_nt.split(" - ")[0]
        matched_rows_nt = df_nontender[
            df_nontender["id_paket"].astype(str) == kode_pilih_nt
        ]

        if not matched_rows_nt.empty:
          row_n = matched_rows_nt.iloc[0]
          pemenang = row_n.get("pemenang", "Pemenang") or "Pemenang"
          email_tujuan = (
              row_n.get("email_pemenang", "")
              or "Belum ada email terdaftar"
          )
          telp_tujuan = (
              row_n.get("telp_pemenang", "") or "Belum ada nomor WA terdaftar"
          )
          status_pilih = row_n.get("status_kepatuhan", "Belum")

          if status_pilih.capitalize() == "Belum":
            st.warning(
                "🚨 **Status Paket Ini Masih Belum Patuh:** Paket ini wajib"
                " segera dikirimi pesan peringatan BPJS!"
            )
          else:
            st.info(
                "✅ **Status Paket Ini Sudah Selesai/Patuh:** Pengiriman pesan"
                " bersifat konfirmasi ulang."
            )

          st.info(
              f"📌 **Kontak Pemenang Terdeteksi dari Database:**\n- Email:"
              f" `{email_tujuan}`\n- No. WhatsApp: `{telp_tujuan}`"
          )

          # Pesan untuk Pemenang
          body_email_nt = f"""Kepada Yth. Pimpinan {pemenang},

Sehubungan dengan penetapan pemenang untuk paket Non-Tender {row_n.get('nama_paket', '')} (Kode: {kode_pilih_nt}), sesuai dengan Peraturan Walikota Kendari dan MoU antara Pemerintah Kota Kendari, Kejaksaan Negeri Kendari dan BPJS, diharapkan agar Saudara segera menunaikan kewajiban Saudara terkait BPJS Ketenagakerjaan.

Hormat kami,
Dinas Tenaga Kerja dan Perindustrian Kota Kendari"""

          wa_text_nt = f"Halo {pemenang},\n\nSehubungan dengan penetapan pemenang untuk paket Non-Tender {row_n.get('nama_paket', '')} (Kode: {kode_pilih_nt}), sesuai dengan Peraturan Walikota Kendari dan MoU antara Pemerintah Kota Kendari, Kejaksaan Negeri Kendari dan BPJS, diharapkan agar Saudara segera menunaikan kewajiban Saudara terkait BPJS Ketenagakerjaan.\n\nHormat kami,\nDinas Tenaga Kerja dan Perindustrian Kota Kendari"

          # Pesan untuk PIC BPJS
          body_email_pic = f"""Kepada Yth. Tim PIC BPJS,

Berikut disampaikan laporan pemenang paket Non-Tender yang memerlukan verifikasi kepatuhan BPJS:
- Kode Paket: {kode_pilih_nt}
- Nama Paket: {row_n.get('nama_paket', '')}
- Nama Pemenang: {pemenang}
- Status BPJS: {status_pilih}

Mohon kiranya dapat ditindaklanjuti sesuai ketentuan yang berlaku.

Hormat kami,
Admin SPSE Pemerintah Kota Kendari"""

          wa_text_pic = f"Halo Tim PIC BPJS,\n\nBerikut disampaikan laporan pemenang paket Non-Tender untuk ditindaklanjuti:\n- Kode: {kode_pilih_nt}\n- Paket: {row_n.get('nama_paket', '')}\n- Pemenang: {pemenang}\n- Status BPJS: {status_pilih}\n\nTerima kasih."

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
            if st.button(
                "📧 Kirim Email ke Pemenang", key="btn_send_email_nt"
            ):
              if not email_tujuan or "@" not in email_tujuan:
                st.error("Email pemenang belum valid atau kosong!")
              else:
                try:
                  msg = MIMEMultipart()
                  msg["From"] = smtp_email
                  msg["To"] = email_tujuan
                  msg["Subject"] = (
                      f"Pemberitahuan Kepatuhan BPJS - Paket {kode_pilih_nt}"
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

            if telp_tujuan and telp_tujuan != "Belum ada nomor WA terdaftar":
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
            if st.button("📧 Kirim Email ke PIC BPJS", key="btn_send_email_pic"):
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
    st.info("Belum ada data Non-Tender tersimpan di database cloud.")
