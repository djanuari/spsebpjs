import streamlit as st

st.set_page_config(
    page_title="Monev SPSE & BPJS", page_icon="🏛️", layout="wide"
)

# Inisialisasi Session State untuk Login
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False

if not st.session_state.logged_in:
  st.markdown(
      """
        <style>
        .login-card {
            max-width: 400px;
            margin: 100px auto;
            padding: 30px;
            background-color: #f8f9fa;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        </style>
    """,
      unsafe_allow_html=True,
  )

  col1, col2, col3 = st.columns([1, 1.5, 1])
  with col2:
    st.markdown(
        "<h2 style='text-align: center; color: #2c3e50;'>🔐 Login Administrator</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #7f8c8d;'>Sistem Monitoring"
        " Pengadaan SPSE & BPJS</p>",
        unsafe_allow_html=True,
    )

    with st.form("form_login"):
      username = st.text_input("Username")
      password = st.text_input("Password", type="password")
      submit = st.form_submit_button("Masuk Sistem", use_container_width=True)

      if submit:
        if username == "admin" and password == "12345":
          st.session_state.logged_in = True
          st.success("Login Berhasil!")
          st.rerun()
        else:
          st.error("Username atau Password salah!")
  st.stop()

# Jika sudah login, tampilkan halaman utama & petunjuk navigasi
st.title("🏛️ Dashboard Monitoring SPSE & Kepatuhan BPJS")
st.markdown("---")
st.success("Anda berhasil masuk sebagai Administrator.")

st.info("""
    ### 📂 Petunjuk Navigasi Menu (Sidebar di Samping Kiri):
    * **1_Paket_Tender**: Mengelola data paket tender/seleksi, nilai pagu, negosiasi, tanggal penetapan, data pemenang, serta status ketentuan BPJS (*Sudah / Belum*).
    * **2_Paket_Non_Tender**: Mengelola data paket non-tender, nilai pagu, negosiasi, tanggal tanda tangan kontrak, data pemenang, serta status ketentuan BPJS (*Sudah / Belum*).
""")

st.markdown("---")
if st.button("🚪 Keluar (Logout)", type="secondary"):
  st.session_state.logged_in = False
  st.rerun()