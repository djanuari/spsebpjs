def upsert_spse_data(data_dict):
  """Menyimpan atau memperbarui data termasuk email dan telp ke cloud"""
  try:
    cleaned_dict = {
        k: (
            clean_value(v)
            if not isinstance(v, str)
            else (v if v.strip() != "" else None)
        )
        for k, v in data_dict.items()
    }

    supabase.table("tabel_spse_bpjs").upsert(
        cleaned_dict, on_conflict="id_paket"
    ).execute()
    return True
  except Exception as e:
    st.error(f"Gagal menyimpan data ke cloud: {e}")
    return False
