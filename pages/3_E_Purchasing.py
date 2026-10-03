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

# Ambil data terbaru khusus kategori E-Purchasing dari Supabase Cloud
df_all = get_all_spse_data()
if not df_all.empty and "kategori" in df_all.columns:
  df_ep = df_all[df_all["kategori"].str.lower() == "e-purchasing"]
else:
  df_ep = pd.DataFrame()

# TAB 1: TAMBAH DATA
with tab1:
  st.subheader("Formulir Input E-Purchasing / Mini Kompetisi Baru")
  with st.form("form_tambah_epurchasing", clear_on_submit=True):
    kode_paket = st.text_input("1. Kode Paket (Unik)")
    nama_paket = st.text_input("2. Nama Paket")

    c1, c2 = st.columns(2)
    pagu_paket = c1.number_input(
        "3. Pagu Paket (Rp)", min_value=0.0, format="%.2f"
    )
    hps_paket = c2.number_input(
        "4. HPS Paket (Rp)", min_value=0.0, format="%.2f"
    )

    jenis_pengadaan = st.selectbox("5. Jenis Pengadaan", jenis_pengadaan_opsi)
    nama_pemenang = st.text_input("6. Nama Pemenang / Penyedia")

    c3, c4 = st.columns(2)
    nilai_kontrak = c3.number_input(
        "7. Nilai Kontrak (Rp)", min_value=0.0, format="%.2f"
    )
    tanggal_penetapan = c4.date_input("8. Tanggal Penetapan Pemenang")

    alamat_pemenang = st.text_area("9. Alamat Pemenang")

    c5, c6 = st.columns(2)
    email_pemenang = c5.text_input("10. Email Pemenang")
    telp_pemenang = c6.text_input("11. Nomor Telepon Pemenang")

    status_bpjs = st.selectbox(
        "12. Sudah Memenuhi Ketentuan BPJS?", ["Belum", "Sudah"]
    )

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
            "tanggal_tarik": str(tanggal_penetapan),
            "email_pemenang": email_pemenang,
            "telp_pemenang": telp_pemenang,
            "keterangan": f"Jenis: {jenis_pengadaan} | Kontrak: Rp {nilai_kontrak:,.2f}",
        }
        if upsert_spse_data(data_baru):
          st.success(
              f"Data E-Purchasing dengan kode paket {kode_paket} berhasil"
              " disimpan ke cloud!"
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

        with st.form(f"form_edit_epurchasing_{kode_pilih}"):
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

        # Tombol Hapus Data Satuan
        st.markdown("---")
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
    st.dataframe(df_ep, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📥 Unduh Laporan Data E-Purchasing")
    csv_data = df_ep.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Unduh Laporan E-Purchasing ke Format CSV (.csv)",
        data=csv_data,
        file_name="Laporan_Kepatuhan_BPJS_EPurchasing.csv",
        mime="text/csv",
        type="primary",
    )
  else:
    st.info("Belum ada data E-Purchasing tersimpan di database cloud.")
