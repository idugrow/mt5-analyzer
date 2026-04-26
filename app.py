import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Algo-Optimizer Model One", layout="wide")

st.title("🚀 Algo-Optimizer: Fase 1 (XML Repair Mode)")
st.write("Upload file XML hasil optimasi MT5 Anda.")

uploaded_file = st.file_uploader("Pilih file XML MT5", type=['xml'])

if uploaded_file is not None:
    try:
        # Membaca isi file sebagai string
        string_data = uploaded_file.read().decode('utf-16') # MT5 biasanya pakai UTF-16
        
        # Gunakan read_html pada string data tersebut
        all_dfs = pd.read_html(io.StringIO(string_data))
        
        if len(all_dfs) > 0:
            # Mencari tabel yang punya kolom terbanyak (biasanya itu tabel data utamanya)
            df = max(all_dfs, key=len)
            
            # --- PROSES CLEANING ---
            # Drop kolom Noise
            kolom_dibuang = ['Pass', 'Result', 'Custom']
            df = df.drop(columns=[c for c in kolom_dibuang if c in df.columns])
            
            # Konversi True/False ke 1/0
            hari_cols = ['SE', 'SS', 'R', 'K', 'J']
            for col in hari_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.lower().str.strip().map({'true': '1', 'false': '0'})

            # Membuat Key_ID
            # Kita pakai fillna('?') jika ada kolom yang hilang agar tidak error
            cols_required = ['JAM', 'CND', 'EMA', 'TTP', 'SLP', 'SE', 'SS', 'R', 'K', 'J']
            for c in cols_required:
                if c not in df.columns:
                    df[c] = "X" # Penanda jika kolom tidak ditemukan

            df['Key_ID'] = (
                "JAM" + df['JAM'].astype(str) + "_" +
                "CND" + df['CND'].astype(str) + "_" +
                "EMA" + df['EMA'].astype(str) + "_" +
                "TTP" + df['TTP'].astype(str) + "_" +
                "SLP" + df['SLP'].astype(str) + "_" +
                "DAYS" + df['SE'].astype(str) + df['SS'].astype(str) + 
                df['R'].astype(str) + df['K'].astype(str) + df['J'].astype(str)
            )

            st.success(f"✅ Berhasil! Ditemukan {len(df)} baris data.")
            
            # Preview
            st.subheader("Preview Data")
            kolom_tampilan = ['Key_ID', 'Profit', 'Expected', 'Profit Fact', 'Equity DD', 'Trades']
            tersedia = [c for c in kolom_tampilan if c in df.columns]
            st.dataframe(df[tersedia].head(10))
        else:
            st.error("File terbaca, tapi tidak ditemukan tabel data di dalamnya.")

    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        st.info("Saran: Coba buka file XML tersebut di Notepad, apakah isinya terlihat seperti teks tabel (HTML) atau kode XML murni?")
