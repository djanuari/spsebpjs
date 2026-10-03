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
    page_title="E-Purchasing / Mini Kompetisi", page_icon="🛒", layout="wide"
)

st.title("🛒 3. Data E-Purchasing / Mini Kompetisi & Kepatuhan BPJS")
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

# Ambil data dari Supabase Cloud dan filter kategori E-Purchasing
df_all = get_all_spse_data()
if not df_all.empty and "kategori" in df_all.columns:
  df_ep = df_all[df_all["kategori"].str.lower() == "e-purchasing"]
else:
  df_ep = pd.DataFrame()

# TAB 1: TAMBAH DATA
with tab1:
  st.subheader("Formulir Input E-Purchasing Baru")
  with st.form("form_tambah_ep", clear_on_submit=True):
    kode_rup = st.text_input("1. Kode RUP")
    kode_paket = st.text_input("2. Kode Paket (Wajib unik sebagai Primary Key)")
    nama_paket = st.text_input("3. Nama Paket")

    c1, c2 = st.columns(2)
    pagu_paket = c1.number_input(
        "4. Pagu Paket (Rp)", min_value=0.0, format="%.2f"
    )
    hps_paket = c2.number_input(
        "5. HPS Paket (Rp)", min_value=0.0, format="%.2f"
    )

    jenis_pengadaan = st.selectbox("6. Jenis Pengadaan", jenis_pengadaan_opsi)
    nama_pemenang = st.text_input("7. Nama Pemenang / Nama Penyedia")

    c3, c4 = st.columns(2)
    nilai_kontrak = c3.number_input(
        "8. Nilai Kontrak (Rp)", min_value=0.0, format="%.2f"
    )
    tanggal_kontrak = c4.date_input("9. Tanggal Penetapan / Kontrak")

    status_bpjs = st.selectbox(
        "10. Sudah Memenuhi Ketentuan BPJS?", ["Belum", "Sudah"]
    )
    alamat_pemenang = st.text_area("11. Alamat Pemenang")

    c5, c6 = st.columns(2)
    email_pemenang = c5.text_input("12. Email Pemenang")
    telp_pemenang = c6.text_input("13. Nomor Telepon Pemenang")

    submit_ep = st.form_submit_button(
        "Simpan Data E-Purchasing", type="primary"
    )

    if submit_ep:
      if kode_paket.strip() == "":
        st.error("Kode Paket wajib diisi!")
      else:
        data_baru = {
            "id_paket": kode_paket.strip(),
            "nama_paket": nama_paket,
            "kategori": "E-Purchasing",
            "pagu": pagu_paket,
            "hps": hps_paket,
            "pemenang": nama_pemenang,
            "status_kepatuhan": status_bpjs,
            "tanggal_tarik": str(tanggal_kontrak),
            "email_pemenang": email_pemenang,
            "telp_pemenang": telp_pemenang,
            "keterangan": f"Kode RUP: {kode_rup} | Nilai Kontrak: {nilai_kontrak} | Jenis: {jenis_pengadaan} | Alamat: {alamat_pemenang}",
        }
        if upsert_spse_data(data_baru):
          st.success(
              f"Data E-Purchasing dengan kode {kode_paket} berhasil disimpan"
              " ke cloud Supabase!"
          )
          st.rerun()

# TAB 2: EDIT & HAPUS DATA
with tab2:
  st.subheader("Edit atau Hapus Data Berdasarkan Kode Paket")
  if not df_ep.empty and "id_paket" in df_ep.columns:
    df_ep["label_edit"] = (
        df_ep["id_paket"].astype(str)
        + " - "
        + df_ep["nama_paket"].fillna("")
    )
    pilihan_edit = st.selectbox(
        "Pilih Kode Paket yang ingin dikelola:", df_ep["label_edit"].tolist()
    )

    if pilihan_edit:
      kode_pilih = pilihan_edit.split(" - ")[0]
      matched_row = df_ep[df_ep["id_paket"].astype(str) == kode_pilih]

      if not matched_row.empty:
        r = matched_row.iloc[0]
        st.info(f"Sedang mengelola Kode Paket: **{kode_pilih}**")

        with st.form(f"form_edit_ep_{kode_pilih}"):
          u_nama = st.text_input(
              "Nama Paket", value=str(r.get("nama_paket", "") or "")
          )
          uc1, uc2 = st.columns(2)
          u_pagu = uc1.number_input(
              "Pagu Paket (Rp)",
              value=float(r.get("pagu", 0.0) or 0.0),
              format="%.2f",
          )
          u_hps = uc2.number_input(
              "HPS Paket (Rp)",
              value=float(r.get("hps", 0.0) or 0.0),
              format="%.2f",
          )

          u_pemenang = st.text_input(
              "Nama Pemenang / Penyedia",
              value=str(r.get("pemenang", "") or ""),
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
              "Keterangan / RUP / Nilai Kontrak / Alamat",
              value=str(r.get("keterangan", "") or ""),
          )

          submit_update = st.form_submit_button(
              "Simpan Perubahan", type="primary"
          )

          if submit_update:
            data_update = {
                "id_paket": kode_pilih,
                "nama_paket": u_nama,
                "kategori": "E-Purchasing",
                "pagu": u_pagu,
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
                  f"Data E-Purchasing dengan kode {kode_pilih} berhasil"
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
            f"🗑️ Hapus Paket E-Purchasing ({kode_pilih})",
            type="secondary",
            key=f"del_ep_{kode_pilih}",
        ):
          try:
            supabase.table("tabel_spse_bpjs").delete().eq(
                "id_paket", kode_pilih
            ).execute()
            st.success(
                f"Data E-Purchasing dengan kode {kode_pilih} berhasil dihapus"
                " dari cloud!"
            )
            st.rerun()
          except Exception as e:
            st.error(f"Gagal menghapus data: {e}")
  else:
    st.info("Belum ada data E-Purchasing tersimpan di cloud.")

# TAB 3: LAPORAN & NOTIFIKASI
with tab3:
  st.subheader("Rekapitulasi Paket E-Purchasing & Peringatan Otomatis")
  if not df_ep.empty:

    # Logika Evaluasi Otomatis (Mulai H+1 Tanggal Kontrak)
    def evaluasi_berdasarkan_tanggal(row):
      status = str(row.get("status_kepatuhan", "Belum")).capitalize()
      tgl_str = str(row.get("tanggal_tarik", "")).split(" ")[0]

      if status == "Sudah":
        return "✅ Selesai / Patuh"

      try:
        tgl_kontrak = datetime.strptime(tgl_str, "%Y-%m-%d")
        selisih_hari = (datetime.now() - tgl_kontrak).days

        if selisih_hari >= 1:
          return (
              f"🚨 URGENT: H+{selisih_hari} Kontrak (Wajib Kirim Notifikasi)"
          )
        elif selisih_hari == 0:
          return "⚠️ Hari H Kontrak"
        else:
          return "📅 Tanggal Kontrak Mendatang"
      except Exception:
        return "🚨 Wajib Kirim Notifikasi (Belum Patuh)"

    df_tampil = pd.DataFrame()
    df_tampil["kode_rup"] = df_ep.get("keterangan", "").apply(
        lambda x: (
            str(x).split("Kode RUP:")[1].split("|")[0].strip()
            if "Kode RUP:" in str(x)
            else "-"
        )
    )
    df_tampil["kode_paket"] = df_ep.get("id_paket", "")
    df_tampil["nama_paket"] = df_ep.get("nama_paket", "")
    df_tampil["pagu_paket"] = df_ep.get("pagu", 0.0)
    df_tampil["hps_paket"] = df_ep.get("hps", 0.0)
    df_tampil["jenis_pengadaan"] = df_ep.get("keterangan", "").apply(
        lambda x: (
            str(x).split("Jenis:")[1].split("|")[0].strip()
            if "Jenis:" in str(x)
            else "-"
        )
    )
    df_tampil["nama_pemenang / nama_penyedia"] = df_ep.get("pemenang", "")
    df_tampil["nilai_kontrak"] = df_ep.get("keterangan", "").apply(
        lambda x: (
            float(
                str(x)
                .split("Nilai Kontrak:")[1]
                .split("|")[0]
                .strip()
                .replace(",", "")
            )
            if "Nilai Kontrak:" in str(x)
            else 0.0
        )
    )
    df_tampil["alamat_pemenang"] = df_ep.get("keterangan", "").apply(
        lambda x: (
            str(x).split("Alamat:")[1].strip()
            if "Alamat:" in str(x)
            else "-"
        )
    )
    df_tampil["email_pemenang"] = df_ep.get("email_pemenang", "")
    df_tampil["telp_pemenang"] = df_ep.get("telp_pemenang", "")
    df_tampil["Status"] = df_ep.get("status_kepatuhan", "Belum")
    df_tampil["Evaluasi_Otomatis"] = df_ep.apply(
        evaluasi_berdasarkan_tanggal, axis=1
    )

    total_urgent = df_tampil["Evaluasi_Otomatis"].str.contains("URGENT").sum()
    total_belum = (df_tampil["Status"].str.capitalize() == "Belum").sum()

    if total_urgent > 0:
      st.error(
          f"🚨 **Peringatan Sistem:** Ditemukan **{total_urgent} paket** dari"
          f" total **{total_belum} paket** belum patuh yang sudah melewati"
          " tanggal kontrak (>= H+1). **Wajib segera dikirimi pesan"
          " notifikasi!**"
      )
    else:
      st.warning(
          f"⚠️ Ada **{total_belum} paket** yang status kepatuhannya masih"
          " 'Belum'."
      )

    st.dataframe(
        df_tampil,
        column_config={
            "kode_rup": "kode_rup",
            "kode_paket": "kode_paket",
            "nama_paket": "nama_paket",
            "pagu_paket": st.column_config.NumberColumn(
                "pagu_paket", format="Rp %.2f"
            ),
            "hps_paket": st.column_config.NumberColumn(
                "hps_paket", format="Rp %.2f"
            ),
            "jenis_pengadaan": "jenis_pengadaan",
            "nama_pemenang / nama_penyedia": "nama_pemenang / nama_penyedia",
            "nilai_kontrak": st.column_config.NumberColumn(
                "nilai_kontrak", format="Rp %.2f"
            ),
            "alamat_pemenang": "alamat_pemenang",
            "email_pemenang": "email_pemenang",
            "telp_pemenang": "telp_pemenang",
            "Status": "Status",
            "Evaluasi_Otomatis": "Status Peringatan (H+1 Kontrak)",
        },
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.subheader("📥 Unduh Laporan Data E-Purchasing")
    csv_data = df_tampil.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Unduh Laporan E-Purchasing ke Format CSV (.csv)",
        data=csv_data,
        file_name="Laporan_Kepatuhan_BPJS_EPurchasing.csv",
        mime="text/csv",
        type="primary",
    )

    st.markdown("---")
    st.subheader(
        "📨 Pusat Pengiriman Notifikasi (Email & WhatsApp) - E-Purchasing"
    )

    with st.expander(
        "⚙️ Konfigurasi & Kirim Pesan Otomatis (Pemenang & PIC BPJS)",
        expanded=True,
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

      st.markdown("---")
      col_pic1, col_pic2 = st.columns(2)
      email_pic = col_pic1.text_input(
          "Email PIC BPJS",
          value="pic.bpjs@kendarikota.go.id",
          key="ep_pic_email",
      )
      hp_pic = col_pic2.text_input(
          "No. WhatsApp PIC BPJS (628...)",
          value="6281111222233",
          key="ep_pic_hp",
      )

      list_opsi_ep = (
          df_ep["id_paket"].astype(str)
          + " - "
          + df_ep["nama_paket"].fillna("")
      ).tolist()
      pilihan_notif_ep = st.selectbox(
          "Pilih Kode & Nama Paket E-Purchasing:", list_opsi_ep, key="ep_sel_notif"
      )

      if pilihan_notif_ep:
        kode_pilih_ep = pilihan_notif_ep.split(" - ")[0]
        matched_rows_ep = df_ep[df_ep["id_paket"].astype(str) == kode_pilih_ep]

        if not matched_rows_ep.empty:
          row_e = matched_rows_ep.iloc[0]
          pemenang = row_e.get("pemenang", "Penyedia") or "Penyedia"

          raw_email = row_e.get("email_pemenang", "")
          email_tujuan = (
              str(raw_email).strip()
              if raw_email and str(raw_email).lower() != "nan"
              else ""
          )

          raw_telp = row_e.get("telp_pemenang", "")
          telp_tujuan = (
              str(raw_telp).strip()
              if raw_telp and str(raw_telp).lower() != "nan"
              else ""
          )

          tgl_kontrak_val = str(row_e.get("tanggal_tarik", "-"))
          status_pilih = row_e.get("status_kepatuhan", "Belum")

          st.info(
              f"📌 **Detail Paket Terpilih:**\n- Tanggal Penetapan/Kontrak:"
              f" `{tgl_kontrak_val}`\n- Status Kepatuhan:"
              f" `{status_pilih}`\n- Email Pemenang/Penyedia:"
              f" `{email_tujuan if email_tujuan else 'Belum ada email terdaftar'}`\n- No."
              f" WhatsApp Pemenang/Penyedia:"
              f" `{telp_tujuan if telp_tujuan else 'Belum ada nomor WA terdaftar'}`"
          )

          # Pesan untuk Penyedia / Pemenang E-Purchasing
          body_email_ep = f"""Kepada Yth. Pimpinan {pemenang},

Sehubungan dengan penetapan/kontrak paket E-Purchasing {row_e.get('nama_paket', '')} (Kode Paket: {kode_pilih_ep}) pada tanggal {tgl_kontrak_val}, sesuai dengan Peraturan Walikota Kendari dan MoU antara Pemerintah Kota Kendari, Kejaksaan Negeri Kendari dan BPJS, diharapkan agar Saudara segera menunaikan kewajiban kepatuhan BPJS Ketenagakerjaan mulai hari ini (sehari setelah tanggal penetapan).

Hormat kami,
Dinas Tenaga Kerja dan Perindustrian Kota Kendari"""

          wa_text_ep = f"Halo {pemenang},\n\nSehubungan dengan penetapan/kontrak paket E-Purchasing {row_e.get('nama_paket', '')} (Kode Paket: {kode_pilih_ep}) pada tanggal {tgl_kontrak_val}, sesuai dengan Peraturan Walikota Kendari dan MoU antara Pemerintah Kota Kendari, Kejaksaan Negeri Kendari dan BPJS, diharapkan agar Saudara segera menunaikan kewajiban kepatuhan BPJS Ketenagakerjaan mulai hari ini.\n\nHormat kami,\nDinas Tenaga Kerja dan Perindustrian Kota Kendari"

          # Pesan untuk PIC BPJS
          body_email_pic = f"""Kepada Yth. Tim PIC BPJS,

Berikut disampaikan monitoring kepatuhan BPJS paket E-Purchasing (aktif mulai H+1 tanggal penetapan):
- Kode Paket: {kode_pilih_ep}
- Nama Paket: {row_e.get('nama_paket', '')}
- Tanggal Kontrak: {tgl_kontrak_val}
- Nama Pemenang/Penyedia: {pemenang}
- Status BPJS: {status_pilih}

Mohon kiranya dapat diverifikasi dan ditindaklanjuti sesuai ketentuan yang berlaku.

Hormat kami,
Admin SPSE Pemerintah Kota Kendari"""

          wa_text_pic = f"Halo Tim PIC BPJS,\n\nBerikut monitoring kepatuhan paket E-Purchasing (aktif mulai H+1 penetapan):\n- Kode Paket: {kode_pilih_ep}\n- Paket: {row_e.get('nama_paket', '')}\n- Tgl Kontrak: {tgl_kontrak_val}\n- Penyedia: {pemenang}\n- Status BPJS: {status_pilih}\n\nTerima kasih."

          with st.expander("📄 Pratinjau Pesan (Penyedia & PIC BPJS)"):
            st.markdown("**1. Pesan untuk Penyedia / Pemenang:**")
            st.text_area("Teks Email Penyedia:", value=body_email_ep, height=100)
            st.text_area("Teks WA Penyedia:", value=wa_text_ep, height=100)
            st.markdown("---")
            st.markdown("**2. Pesan untuk PIC BPJS:**")
            st.text_area("Teks Email PIC BPJS:", value=body_email_pic, height=100)
            st.text_area("Teks WA PIC BPJS:", value=wa_text_pic, height=100)

          st.markdown("### 🚀 Aksi Pengiriman Pesan")
          col_a1, col_a2 = st.columns(2)

          with col_a1:
            st.markdown("#### Kirim ke Penyedia / Pemenang")
            if st.button("📧 Kirim Email ke Penyedia", key="btn_send_email_ep"):
              if not email_tujuan or "@" not in email_tujuan:
                st.error("Email penyedia belum valid atau kosong!")
              else:
                try:
                  msg = MIMEMultipart()
                  msg["From"] = smtp_email
                  msg["To"] = email_tujuan
                  msg["Subject"] = (
                      f"Pemberitahuan Kepatuhan BPJS - E-Purchasing"
                      f" {kode_pilih_ep}"
                  )
                  msg.attach(MIMEText(body_email_ep, "plain"))

                  server = smtplib.SMTP("smtp.gmail.com", 587)
                  server.starttls()
                  server.login(smtp_email, smtp_pass)
                  server.sendmail(smtp_email, email_tujuan, msg.as_string())
                  server.quit()
                  st.success(
                      f"Email berhasil dikirim ke Penyedia ({email_tujuan})!"
                  )
                except Exception as e:
                  st.error(
                      f"Gagal mengirim email (pastikan App Password benar): {e}"
                  )

            if telp_tujuan:
              encoded_wa = urllib.parse.quote(wa_text_ep)
              wa_url = f"https://wa.me/{telp_tujuan}?text={encoded_wa}"
              st.markdown(
                  f'<a href="{wa_url}" target="_blank"><button'
                  ' style="background-color:#25D366; color:white; border:none;'
                  " padding:10px 20px; border-radius:5px; cursor:pointer; width:"
                  '100%; font-weight:bold; margin-top:5px;">💬 Kirim WhatsApp ke'
                  " Penyedia</button></a>",
                  unsafe_allow_html=True,
              )
            else:
              st.warning("Nomor WhatsApp penyedia belum tersedia.")

          with col_a2:
            st.markdown("#### Kirim ke PIC BPJS")
            if st.button(
                "📧 Kirim Email ke PIC BPJS", key="btn_send_email_pic_ep"
            ):
              if not email_pic or "@" not in email_pic:
                st.error("Email PIC BPJS belum valid atau kosong!")
              else:
                try:
                  msg_pic = MIMEMultipart()
                  msg_pic["From"] = smtp_email
                  msg_pic["To"] = email_pic
                  msg_pic["Subject"] = (
                      f"Laporan Kepatuhan BPJS E-Purchasing - {kode_pilih_ep}"
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
    st.info("Belum ada data E-Purchasing tersimpan di cloud.")
