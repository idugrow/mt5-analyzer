import streamlit as st
import pandas as pd

st.set_page_config(page_title="Algo-Optimizer Model One", layout="wide")

st.title("🚀 Algo-Optimizer: Fase 1 (Pembersihan & Key ID)")
st.write("Upload file hasil optimasi MT5 Anda untuk memulai proses cleaning.")

# 1. Widget Upload File
uploaded_file = st.file_uploader("Pilih file CSV MT5", type=['csv'])

if uploaded_file is not None:
    # 2. Membaca data (Mengantisipasi pemisah koma atau titik koma)
    try:
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        
        # 3. Drop kolom Noise
        kolom_dibuang = ['Pass', 'Result', 'Custom']
        df = df.drop(columns=[c for c in kolom_dibuang if c in df.columns])
        
        # 4. Konversi True/False menjadi 1/0 agar Key ID ringkas
        hari_cols = ['SE', 'SS', 'R', 'K', 'J']
        for col in hari_cols:
            if col in df.columns:
                # Mengubah ke string lower dulu agar seragam, lalu map ke 1/0
                df[col] = df[col].astype(str).str.lower().map({'true': '1', 'false': '0'})

        # 5. Membuat Key_ID Unik berdasarkan Gambar Anda
        # Kita gunakan kolom: JAM, CND, EMA, TTP, SLP, SE, SS, R, K, J
        df['Key_ID'] = (
            "JAM" + df['JAM'].astype(str) + "_" +
            "CND" + df['CND'].astype(str) + "_" +
            "EMA" + df['EMA'].astype(str) + "_" +
            "TTP" + df['TTP'].astype(str) + "_" +
            "SLP" + df['SLP'].astype(str) + "_" +
            "DAYS" + df['SE'].astype(str) + df['SS'].astype(str) + 
            df['R'].astype(str) + df['K'].astype(str) + df['J'].astype(str)
        )

        st.success("✅ File Berhasil Diolah!")
        
        # 6. Menampilkan Hasil Preview
        st.subheader("Preview Data dengan Key ID")
        kolom_tampilan = ['Key_ID', 'Profit', 'Expected', 'Profit Fact', 'Equity DD', 'Trades']
        # Menampilkan hanya kolom yang ada saja agar tidak error
        tersedia = [c for c in kolom_tampilan if c in df.columns]
        st.dataframe(df[tersedia].head(10))

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")

else:
    st.info("Silakan upload file CSV untuk melihat hasilnya.")
