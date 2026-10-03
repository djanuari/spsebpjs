from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import urllib.parse
from api_connector import get_all_spse_data, upsert_spse_data, supabase
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
    ["➕ Tambah Data", "✏️ Edit / Perbarui Data", "📋 Daftar & Laporan"]
)

jenis_pengadaan_opsi = [
    "Pekerjaan Konstruksi",
    "Jasa Konsultansi Konstruksi",
    "Jasa Konsultansi Non Konstruksi",
    "Jasa Lainnya",
    "Pengadaan Barang",
]

# Ambil data terbaru khusus kategori Non-Tender dari Supabase Cloud
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
        data_baru = {
            "id_paket": kode_nontender.strip(),
            "nama_paket": nama_nontender,
            "kategori": "Non-Tender",
            "pagu": nilai_pagu,
            "hps": nilai_hps,
            "pemenang": nama_pemenang,
            "status_kepatuhan": status_bpjs,
            "tanggal_tarik": str(tanggal_penetapan),
            "keterangan": f"Satuan Kerja: {satuan_kerja} | Jenis: {jenis_pengadaan} | Kontrak: Rp {nilai_kontrak:,.2f}",
        }
        if upsert_spse_data(data_baru):
          st.success(
              f"Data Non-Tender dengan kode {kode_nontender} berhasil disimpan ke"
              " cloud!"
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
          u_pagu = uc1.number_input(
              "Nilai Pagu (Rp)",
              value=float(r.get("pagu", 0.0) or 0.0),
              format="%.2f",
          )
          u_hps = uc2.number_input(
              "Nilai HPS (Rp)",
              value=float(r.get("hps", 0.0) or 0.0),
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
          u_ket = st.text_area(
              "Keterangan / Satuan Kerja",
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
                "pagu": u_pagu,
                "hps": u_hps,
                "pemenang": u_pemenang,
                "status_kepatuhan": u_bpjs,
                "tanggal_tarik": str(r.get("tanggal_tarik", "")),
                "keterangan": u_ket,
            }
            if upsert_spse_data(data_update):
              st.success(
                  f"Data Non-Tender dengan kode {kode_pilih} berhasil"
                  " diperbarui di cloud!"
              )
              st.rerun()

        # Tombol Hapus Data (Diletakkan di luar form agar aman)
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
    st.info("Belum ada data Non-Tender tersimpan di cloud untuk diedit.")

# TAB 3: LAPORAN & NOTIFIKASI
with tab3:
  st.subheader("Rekapitulasi Paket Non-Tender & Peringatan Otomatis")

  if not df_nontender.empty:
    hari_ini = datetime.now().date()


    def cek_status_notif_nt(row):
      try:
        tgl_val = row.get("tanggal_tarik")
        if not tgl_val:
          return "⏳ Menunggu Jadwal"
        tgl_str = str(tgl_val).split()[0]
        tgl_penetapan = datetime.strptime(tgl_str, "%Y-%m-%d").date()
        status = str(row.get("status_kepatuhan", "Belum")).capitalize()

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
          status = row_n.get("status_kepatuhan", "Belum")

          if "Wajib Kirim" in str(row_n.get("status_peringatan", "")):
            st.error(
                "🚨 Status Paket Ini: **Jatuh Tempo (Wajib Kirim Notifikasi"
                " BPJS)**"
            )

          body_email_nt = f"""Kepada Yth. Pimpinan {pemenang},

Sehubungan dengan penetapan pemenang untuk paket Non-Tender {row_n.get('nama_paket', '')} (Kode: {kode_pilih_nt}), sesuai dengan Peraturan Walikota Kendari dan MoU antara Pemerintah Kota Kendari, Kejaksaan Negeri Kendari dan BPJS, diharapkan agar Saudara segera menunaikan kewajiban Saudara terkait BPJS Ketenagakerjaan.

Hormat kami,
Dinas Tenaga Kerja dan Perindustrian Kota Kendari"""

          wa_text_nt = f"Halo {pemenang},\n\nSehubungan dengan penetapan pemenang untuk paket Non-Tender {row_n.get('nama_paket', '')} (Kode: {kode_pilih_nt}), sesuai dengan Peraturan Walikota Kendari dan MoU antara Pemerintah Kota Kendari, Kejaksaan Negeri Kendari dan BPJS, diharapkan agar Saudara segera menunaikan kewajiban Saudara terkait BPJS Ketenagakerjaan.\n\nHormat kami,\nDinas Tenaga Kerja dan Perindustrian Kota Kendari"

          with st.expander("📄 Pratinjau Pesan Email & WhatsApp"):
            st.text_area("Teks Email:", value=body_email_nt, height=120)
            st.text_area("Teks WA:", value=wa_text_nt, height=120)

          if st.button(
              "📧 Kirim Email Uji Coba ke Sistem", key="btn_send_nt"
          ):
            st.success("Simulasi pengiriman email berhasil diproses!")
  else:
    st.info("Belum ada data Non-Tender tersimpan di database cloud.")
