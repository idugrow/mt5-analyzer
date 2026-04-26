import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

st.set_page_config(page_title="Algo-Optimizer Model One", layout="wide")

st.title("🚀 Algo-Optimizer: Fase 1 & 2 (Multi-File Processing)")
st.write("Silakan upload ke-5 file XML hasil optimasi Anda (Rentang 2006-2025).")

# 1. Widget Upload Multiple Files
uploaded_files = st.file_uploader("Pilih 5 file XML MT5", type=['xml'], accept_multiple_files=True)

# List untuk menampung data dari setiap file
all_dataframes = []

if uploaded_files:
    if len(uploaded_files) > 5:
        st.warning("⚠️ Anda mengunggah lebih dari 5 file. Sistem hanya akan memproses 5 file pertama.")
        uploaded_files = uploaded_files[:5]

    for i, file in enumerate(uploaded_files):
        try:
            # Parsing XML Excel Schema
            tree = ET.parse(file)
            root = tree.getroot()
            ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
            rows = root.findall('.//ss:Worksheet[1]//ss:Table//ss:Row', ns)
            
            data = []
            for row in rows:
                cells = [cell.text for cell in row.findall('.//ss:Data', ns)]
                data.append(cells)
            
            if len(data) > 1:
                df = pd.DataFrame(data[1:], columns=data[0])
                
                # Pembersihan Kolom
                kolom_dibuang = ['Pass', 'Result', 'Custom']
                df = df.drop(columns=[c for c in kolom_dibuang if c in df.columns])
                
                # Konversi Numerik
                cols_numeric = ['Profit', 'Expected', 'Profit Fact', 'Equity DD', 'Trades', 'JAM', 'CND', 'EMA', 'TTP', 'SLP']
                for c in cols_numeric:
                    if c in df.columns:
                        df[c] = pd.to_numeric(df[c], errors='coerce')
                
                # Konversi Hari (True/False -> 1/0)
                hari_cols = ['SE', 'SS', 'R', 'K', 'J']
                for col in hari_cols:
                    if col in df.columns:
                        df[col] = df[col].astype(str).str.lower().str.strip().map({'true': '1', 'false': '0'})

                # Pembuatan Key_ID
                df['Key_ID'] = (
                    "JAM" + df['JAM'].fillna(0).astype(int).astype(str) + "_" +
                    "CND" + df['CND'].fillna(0).astype(int).astype(str) + "_" +
                    "EMA" + df['EMA'].fillna(0).astype(int).astype(str) + "_" +
                    "TTP" + df['TTP'].fillna(0).astype(int).astype(str) + "_" +
                    "SLP" + df['SLP'].fillna(0).astype(int).astype(str) + "_" +
                    "DAYS" + df['SE'].fillna('0').astype(str) + df['SS'].fillna('0').astype(str) + 
                    df['R'].fillna('0').astype(str) + df['K'].fillna('0').astype(str) + df['J'].fillna('0').astype(str)
                )
                
                # Beri label periode agar tidak tertukar
                df['Periode'] = f"File_{i+1}"
                
                all_dataframes.append(df)
                st.success(f"✅ {file.name} berhasil diproses!")
            
        except Exception as e:
            st.error(f"Gagal memproses {file.name}: {e}")

    # Jika semua file sudah ter-upload (misal sudah ada data)
    if all_dataframes:
        st.divider()
        st.subheader("📊 Status Ingestion Data")
        for idx, temp_df in enumerate(all_dataframes):
            st.write(f"File {idx+1}: {len(temp_df)} baris data ditemukan.")
        
        # Simpan ke session state agar bisa digunakan di Modul selanjutnya tanpa upload ulang
        st.session_state['all_dfs'] = all_dataframes
        st.info("Pondasi Fase 1 Selesai. Siap lanjut ke FASE 2: Filtering?")
