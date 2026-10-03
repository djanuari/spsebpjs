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

tahapan_opsi = ["Pemilihan Berlangsung", "Pemilihan Selesai", "Kontrak"]

# TAB 1: UPLOAD / IMAMOR EXCEL E-PURCHASING
with tab_import:
  st.subheader("📤 Unggah File Excel Rujukan E-Purchasing")
  st.info(
      "Unggah file Excel Anda di sini. Sistem akan menyinkronkan data"
      " E-Purchasing secara presisi ke database cloud."
  )

  uploaded_excel = st.file_uploader(
      "Pilih file Excel (.xlsx)", type=["xlsx", "xls"], key="ep_excel"
  )
  if uploaded_excel is not None:
    try:
      df_import = pd.read_excel(uploaded_excel)
      st.write(
          f"Berhasil membaca file dengan {len(df_import)} baris data. Contoh"
          " data teratas:"
      )
      st.dataframe(df_import.head(3), use_container_width=True)

      if st.button(
          "🚀 Proses & Simpan Data E-Purchasing ke Database",
          key="btn_proc_ep",
          type="primary",
      ):
        success_count = 0
        with st.spinner("Sedang menyinkronkan data E-Purchasing ke Supabase..."):
          for _, row in df_import.iterrows():
            kode = str(
                row.get("kode_paket", "")
                or row.get("id_paket", "")
                or row.get("kode_RUP", "")
                or ""
            ).strip()
            if not kode or kode.lower() == "nan":
              continue

            satuan_kerja = str(row.get("satuan_kerja", "") or "")
            jenis_pengadaan = str(row.get("jenis_pengadaan", "") or "")
            tahapan_pengadaan = str(
                row.get("tahapan_pengadaan", "")
                or row.get("status_paket", "")
                or "Kontrak"
            )
            alamat = str(
                row.get("Alamat", "") or row.get("alamat", "") or ""
            )

            combined_ket = (
                f"[SK]:{satuan_kerja}|[JP]:{jenis_pengadaan}|[TP]:{tahapan_pengadaan}|[AL]:{alamat}"
            )

            # Ambil Nilai Kontrak / Total Nilai
            val_nilai = 0.0
            for col_n in [
                "nilai_kontrak",
                "total_nilai",
                "pagu",
                "nilai_pagu",
                "pagu_paket",
            ]:
              if col_n in row and pd.notna(row[col_n]):
                try:
                  raw_v = row[col_n]
                  if isinstance(raw_v, (int, float)):
                    val_nilai = float(raw_v)
                  else:
                    clean_s = (
                        str(raw_v)
                        .replace("Rp", "")
                        .replace(".", "")
                        .replace(",", ".")
                        .strip()
                    )
                    val_nilai = float(clean_s)
                  if val_nilai > 0:
                    break
                except Exception:
                  pass

            # Ambil Nama Pemenang / Penyedia
            val_pemenang = "-"
            for col_p in [
                "nama_pemenang",
                "nama_penyedia",
                "pemenang",
                "penyedia",
            ]:
              if col_p in row and pd.notna(row[col_p]):
                p_str = str(row[col_p]).strip()
                if p_str and p_str.lower() != "nan" and p_str != "-":
                  val_pemenang = p_str
                  break

            val_tgl = str(
                row.get("tanggal penetapan", "")
                or row.get("tanggal selesai pemilihan", "")
                or row.get("tanggal_tarik", "")
                or ""
            ).strip()
            if val_tgl.lower() == "nan":
              val_tgl = ""

            data_row = {
                "id_paket": kode,
                "nama_paket": str(
                    row.get("nama_paket", "")
                    or row.get("uraian_pekerjaan", "")
                    or "-"
                ),
                "kategori": "E-Purchasing",
                "pagu": val_nilai,  # Disimpan ke kolom 'pagu' di Supabase
                "hps": 0.0,
                "pemenang": val_pemenang,
                "status_kepatuhan": str(
                    row.get("status_kepatuhan", "Belum") or "Belum"
                ),
                "tanggal_tarik": val_tgl,
                "email_pemenang": str(
                    row.get("email", "")
                    or row.get("email_pemenang", "")
                    or ""
                ),
                "telp_pemenang": str(
                    row.get("telepon", "")
                    or row.get("telp_pemenang", "")
                    or ""
                ),
                "keterangan": combined_ket,
            }
            if upsert_spse_data(data_row):
              success_count += 1

        st.success(
            f"Berhasil menyinkronkan {success_count} data E-Purchasing ke"
            " database cloud!"
        )
        st.rerun()
    except Exception as e:
      st.error(f"Gagal membaca file Excel: {e}")

# Ambil data dari Supabase Cloud dan filter kategori E-Purchasing
df_all = get_all_spse_data()
if not df_all.empty and "kategori" in df_all.columns:
  df_ep = df_all[df_all["kategori"].str.lower() == "e-purchasing"]
else:
  df_ep = pd.DataFrame()

# TAB 2: TAMBAH DATA MANUAL
with tab1:
  st.subheader("Formulir Input E-Purchasing Baru")
  with st.form("form_tambah_ep", clear_on_submit=True):
    kode_paket = st.text_input("1. Kode Paket (Primary Key)")
    nama_paket = st.text_input("2. Nama Paket")

    c1, c2 = st.columns(2)
    jenis_pengadaan = c1.selectbox("3. Jenis Pengadaan", jenis_pengadaan_opsi)
    satuan_kerja = c2.text_input("4. Satuan Kerja")

    c3, c4 = st.columns(2)
    tahapan_pengadaan = c3.selectbox("5. Tahapan / Status Paket", tahapan_opsi)
    nama_pemenang = c4.text_input("6. Nama Pemenang / Penyedia")

    c5, c6 = st.columns(2)
    tanggal_penetapan = c5.date_input("7. Tanggal Penetapan / Kontrak")
    nilai_kontrak = c6.number_input(
        "8. Nilai Kontrak / Pagu (Rp)", min_value=0.0, format="%.2f"
    )

    status_bpjs = c4.selectbox("9. Sudah Memenuhi Ketentuan BPJS?", ["Belum", "Sudah"])
    alamat = st.text_area("10. Alamat Pemenang")

    c7, c8 = st.columns(2)
    email = c7.text_input("11. Email Pemenang")
    telepon = c8.text_input("12. Nomor Telepon Pemenang")

    submit_ep = st.form_submit_button("Simpan Data E-Purchasing", type="primary")

    if submit_ep:
      if kode_paket.strip() == "":
        st.error("Kode Paket wajib diisi sebagai pengenal unik!")
      else:
        combined_ket = (
            f"[SK]:{satuan_kerja}|[JP]:{jenis_pengadaan}|[TP]:{tahapan_pengadaan}|[AL]:{alamat}"
        )
        data_baru = {
            "id_paket": kode_paket.strip(),
            "nama_paket": nama_paket,
            "kategori": "E-Purchasing",
            "pagu": nilai_kontrak,
            "hps": 0.0,
            "pemenang": nama_pemenang,
            "status_kepatuhan": status_bpjs,
            "tanggal_tarik": str(tanggal_penetapan),
            "email_pemenang": email,
            "telp_pemenang": telepon,
            "keterangan": combined_ket,
        }
        if upsert_spse_data(data_baru):
          st.success(
              f"Data E-Purchasing dengan kode {kode_paket} berhasil disimpan"
              " ke cloud Supabase!"
          )
          st.rerun()

# TAB 3: EDIT & HAPUS DATA
with tab2:
  st.subheader("Edit atau Hapus Data Berdasarkan Kode Paket")
  if not df_ep.empty and "id_paket" in df_ep.columns:
    df_ep["label_edit"] = (
        df_ep["id_paket"].astype(str) + " - " + df_ep["nama_paket"].fillna("")
    )
    pilihan_edit = st.selectbox(
        "Pilih Kode Paket yang ingin dikelola:",
        df_ep["label_edit"].tolist(),
        key="sel_edit_ep",
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
          u_pemenang = st.text_input(
              "Nama Pemenang", value=str(r.get("pemenang", "") or "")
          )

          uc1, uc2 = st.columns(2)
          u_nilai = uc1.number_input(
              "Nilai Kontrak / Pagu (Rp)",
              value=float(r.get("pagu", 0.0) or 0.0),
              format="%.2f",
          )
          stat_idx = (
              ["Belum", "Sudah"].index(r.get("status_kepatuhan", "Belum"))
              if r.get("status_kepatuhan") in ["Belum", "Sudah"]
              else 0
          )
          u_bpjs = uc2.selectbox(
              "Status Kepatuhan", ["Belum", "Sudah"], index=stat_idx
          )

          uc3, uc4 = st.columns(2)
          u_email = uc3.text_input(
              "Email", value=str(r.get("email_pemenang", "") or "")
          )
          u_telp = uc4.text_input(
              "Telepon", value=str(r.get("telp_pemenang", "") or "")
          )

          u_ket = st.text_area(
              "Keterangan / Atribut", value=str(r.get("keterangan", "") or "")
          )

          submit_update = st.form_submit_button(
              "Simpan Perubahan", type="primary"
          )

          if submit_update:
            data_update = {
                "id_paket": kode_pilih,
                "nama_paket": u_nama,
                "kategori": "E-Purchasing",
                "pagu": u_nilai,
                "hps": float(r.get("hps", 0.0) or 0.0),
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

        st.markdown("---")
        st.warning(
            "⚠️ Ingin menghapus paket E-Purchasing ini dari database cloud"
            " secara permanen?"
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

    st.markdown("---")
    st.error("🚨 Zona Bahaya: Hapus Seluruh Data E-Purchasing")
    with st.expander("⚠ Klik untuk opsi Hapus Semua Data E-Purchasing"):
      st.warning(
          "Tindakan ini akan menghapus **seluruh** data E-Purchasing dari"
          " database cloud secara permanen."
      )
      konfirmasi_hapus_semua = st.checkbox(
          "Saya yakin ingin menghapus seluruh data E-Purchasing",
          key="chk_hapus_semua_ep",
      )
      if st.button(
          "🗑️ Hapus SEMUA Data E-Purchasing Sekarang",
          key="btn_del_all_ep",
          type="primary",
      ):
        if konfirmasi_hapus_semua:
          try:
            supabase.table("tabel_spse_bpjs").delete().eq(
                "kategori", "E-Purchasing"
            ).execute()
            st.success(
                "Seluruh data E-Purchasing berhasil dihapus dari database cloud!"
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
    st.info("Belum ada data E-Purchasing tersimpan di cloud.")

# TAB 4: LAPORAN & UNDUH
with tab3:
  st.subheader("Rekapitulasi Paket E-Purchasing & Laporan")
  if not df_ep.empty:

    def extract_val(text, tag):
      try:
        if not text or pd.isna(text):
          return "-"
        text_str = str(text)
        parts = text_str.split("|")
        for p in parts:
          if f"[{tag}]:" in p:
            val = p.split(f"[{tag}]:")[1].strip()
            return val if val and val != "None" else "-"
        return text_str if text_str.lower() != "nan" else "-"
      except Exception:
        return "-"

    df_tampil = pd.DataFrame()
    df_tampil["kode_paket"] = df_ep.get("id_paket", pd.Series()).fillna("-")
    df_tampil["nama_paket"] = df_ep.get("nama_paket", pd.Series()).fillna("-")

    ket_series = df_ep.get("keterangan", pd.Series())
    df_tampil["jenis_pengadaan"] = ket_series.apply(
        lambda x: extract_val(x, "JP")
    )
    df_tampil["satuan_kerja"] = ket_series.apply(lambda x: extract_val(x, "SK"))
    df_tampil["tahapan_pengadaan"] = ket_series.apply(
        lambda x: extract_val(x, "TP")
    )
    df_tampil["Alamat"] = ket_series.apply(lambda x: extract_val(x, "AL"))

    df_tampil["nama_pemenang"] = (
        df_ep.get("pemenang", pd.Series())
        .fillna("-")
        .replace("", "-")
        .apply(lambda x: str(x) if str(x).lower() != "nan" else "-")
    )
    df_tampil["tanggal_penetapan"] = df_ep.get(
        "tanggal_tarik", pd.Series()
    ).fillna("-")

    raw_pagu = df_ep.get("pagu", pd.Series()).fillna(0.0)

    def format_rupiah(val):
      try:
        num = float(val)
        if num == 0:
          return "Rp 0,00"
        formatted_num = f"{num:,.2f}"
        return (
            "Rp "
            + formatted_num.replace(",", "X").replace(".", ",").replace(
                "X", "."
            )
        )
      except Exception:
        return "Rp 0,00"

    df_tampil["nilai_kontrak"] = raw_pagu.apply(format_rupiah)
    df_tampil["email"] = df_ep.get("email_pemenang", pd.Series()).fillna("-")
    df_tampil["telepon"] = df_ep.get("telp_pemenang", pd.Series()).fillna("-")
    df_tampil["status_kepatuhan"] = df_ep.get(
        "status_kepatuhan", pd.Series()
    ).fillna("Belum")

    st.dataframe(df_tampil, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📥 Unduh Laporan E-Purchasing")
    csv_data = df_tampil.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Unduh Laporan E-Purchasing ke Format CSV (.csv)",
        data=csv_data,
        file_name="Laporan_Kepatuhan_BPJS_E_Purchasing.csv",
        mime="text/csv",
        type="primary",
    )
  else:
    st.info("Belum ada data E-Purchasing tersimpan di cloud.")
