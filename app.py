import streamlit as st
import pandas as pd

st.set_page_config(page_title="Algo-Optimizer Model One", layout="wide")

st.title("🚀 Algo-Optimizer: Fase 1 (XML Processing)")
st.write("Upload file XML hasil optimasi MT5 Anda.")

# 1. Widget Upload File
uploaded_file = st.file_uploader("Pilih file XML MT5", type=['xml'])

if uploaded_file is not None:
    try:
        # 2. Membaca XML
        # MT5 XML biasanya memiliki struktur tabel di dalamnya
        all_dfs = pd.read_html(uploaded_file)
        
        # Biasanya tabel data ada di index terakhir atau satu-satunya tabel
        df = all_dfs[-1] 

        # 3. Drop kolom Noise (Pass, Result, Custom)
        kolom_dibuang = ['Pass', 'Result', 'Custom']
        df = df.drop(columns=[c for c in kolom_dibuang if c in df.columns])
        
        # 4. Konversi True/False menjadi 1/0
        # Di XML, terkadang nilainya string 'true'/'false' atau 'True'/'False'
        hari_cols = ['SE', 'SS', 'R', 'K', 'J']
        for col in hari_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.lower().strip().map({'true': '1', 'false': '0'})

        # 5. Membuat Key_ID Unik
        # Menggunakan kolom sesuai gambar: JAM, CND, EMA, TTP, SLP + Days
        df['Key_ID'] = (
            "JAM" + df['JAM'].astype(str) + "_" +
            "CND" + df['CND'].astype(str) + "_" +
            "EMA" + df['EMA'].astype(str) + "_" +
            "TTP" + df['TTP'].astype(str) + "_" +
            "SLP" + df['SLP'].astype(str) + "_" +
            "DAYS" + df['SE'].astype(str) + df['SS'].astype(str) + 
            df['R'].astype(str) + df['K'].astype(str) + df['J'].astype(str)
        )

        st.success(f"✅ Berhasil mengolah {len(df)} baris data dari XML!")
        
        # 6. Menampilkan Preview
        st.subheader("Preview Data")
        kolom_tampilan = ['Key_ID', 'Profit', 'Expected', 'Profit Fact', 'Equity DD', 'Trades']
        tersedia = [c for c in kolom_tampilan if c in df.columns]
        st.dataframe(df[tersedia].head(10))

    except Exception as e:
        st.error(f"Gagal membaca XML. Pastikan file benar-benar hasil ekspor MT5. Error: {e}")

else:
    st.info("Silakan upload file XML untuk memulai.")
