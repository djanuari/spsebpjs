from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import urllib.parse
from api_connector import get_all_spse_data, supabase, upsert_spse_data
import pandas as pd
import streamlit as st

if not st.session_state.get("logged_in"):
  st.warning("⚠️ Anda belum login. Silakan kembali ke halaman utama.")
  st.stop()

st.set_page_config(
    page_title="Tender / Seleksi", page_icon="🏛️", layout="wide"
)

st.title("🏛️ 1. Data Tender / Seleksi & Kepatuhan BPJS")
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

# Ambil data terbaru dari Supabase Cloud
df_all = get_all_spse_data()
if not df_all.empty and "kategori" in df_all.columns:
  df_tender = df_all[df_all["kategori"].str.lower() == "tender"]
else:
  df_tender = pd.DataFrame()

# TAB 1: TAMBAH DATA
with tab1:
  st.subheader("Formulir Input Tender / Seleksi Baru")
  with st.form("form_tambah_tender", clear_on_submit=True):
    kode_tender = st.text_input("1. Kode Tender (Unik)")
    nama_paket = st.text_input("2. Nama Paket")
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

    submit_t = st.form_submit_button("Simpan Data Tender", type="primary")

    if submit_t:
      if kode_tender.strip() == "":
        st.error("Kode Tender wajib diisi!")
      else:
        data_baru = {
            "id_paket": kode_tender.strip(),
            "nama_paket": nama_paket,
            "kategori": "Tender",
            "pagu": nilai_pagu,
            "hps": nilai_hps,
            "pemenang": nama_pemenang,
            "status_kepatuhan": status_bpjs,
            "tanggal_tarik": str(tanggal_penetapan),
            "email_pemenang": email_pemenang,
            "telp_pemenang": telp_pemenang,
            "keterangan": f"Satuan Kerja: {satuan_kerja} | Jenis: {jenis_pengadaan} | Kontrak: Rp {nilai_kontrak:,.2f}",
        }
        if upsert_spse_data(data_baru):
          st.success(
              f"Data Tender dengan kode {kode_tender} berhasil disimpan ke"
              " cloud!"
          )
          st.rerun()

# TAB 2: EDIT & HAPUS DATA
with tab2:
  st.subheader("Edit atau Hapus Data Berdasarkan Kode Tender")
  if not df_tender.empty and "id_paket" in df_tender.columns:
    df_tender["label_edit"] = (
        df_tender["id_paket"].astype(str)
        + " - "
        + df_tender["nama_paket"].fillna("")
    )
    pilihan_edit = st.selectbox(
        "Pilih Kode Tender yang ingin dikelola:",
        df_tender["label_edit"].tolist(),
    )

    if pilihan_edit:
      kode_pilih = pilihan_edit.split(" - ")[0]
      matched_row = df_tender[df_tender["id_paket"].astype(str) == kode_pilih]

      if not matched_row.empty:
        r = matched_row.iloc[0]
        st.info(f"Sedang mengelola Kode Tender: **{kode_pilih}**")

        with st.form(f"form_edit_tender_{kode_pilih}"):
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
                "kategori": "Tender",
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
                  f"Data Tender dengan kode {kode_pilih} berhasil diperbarui di"
                  " cloud!"
              )
              st.rerun()

        # Tombol Hapus Data Satuan
        st.markdown("---")
        if st.button(
            f"🗑️ Hapus Paket Tender ({kode_pilih})",
            type="secondary",
            key=f"del_t_{kode_pilih}",
        ):
          try:
            supabase.table("tabel_spse_bpjs").delete().eq(
                "id_paket", kode_pilih
            ).execute()
            st.success(
                f"Data Tender dengan kode {kode_pilih} berhasil dihapus dari"
                " cloud!"
            )
            st.rerun()
          except Exception as e:
            st.error(f"Gagal menghapus data: {e}")
  else:
    st.info("Belum ada data Tender tersimpan di cloud.")

# TAB 3: LAPORAN & NOTIFIKASI
with tab3:
  st.subheader("Rekapitulasi Paket Tender & Peringatan Otomatis")
  if not df_tender.empty:
    st.dataframe(df_tender, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📥 Unduh Laporan Data Tender")
    csv_data = df_tender.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Unduh Laporan Tender ke Format CSV (.csv)",
        data=csv_data,
        file_name="Laporan_Kepatuhan_BPJS_Tender.csv",
        mime="text/csv",
        type="primary",
    )
  else:
    st.info("Belum ada data Tender tersimpan di database cloud.")
