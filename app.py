import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

st.set_page_config(page_title="Algo-Optimizer Model One", layout="wide")

st.title("🚀 Algo-Optimizer: Fase 1 (MT5 Excel-XML Mode)")

uploaded_file = st.file_uploader("Pilih file XML MT5", type=['xml'])

if uploaded_file is not None:
    try:
        # 1. Parsing XML secara manual untuk format Excel Spreadsheet
        tree = ET.parse(uploaded_file)
        root = tree.getroot()
        
        # Namespace untuk Excel XML
        ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        
        # 2. Ambil semua baris (Row) dari Worksheet pertama
        rows = root.findall('.//ss:Worksheet[1]//ss:Table//ss:Row', ns)
        
        data = []
        for row in rows:
            # Ambil semua data sel dalam satu baris
            cells = [cell.text for cell in row.findall('.//ss:Data', ns)]
            data.append(cells)
        
        if len(data) > 1:
            # Baris pertama biasanya Header
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # --- PROSES CLEANING & KEY ID ---
            # Drop kolom yang tidak perlu
            kolom_dibuang = ['Pass', 'Result', 'Custom']
            df = df.drop(columns=[c for c in kolom_dibuang if c in df.columns])
            
            # Konversi kolom numerik (karena XML membacanya sebagai string)
            cols_numeric = ['Profit', 'Expected', 'Profit Fact', 'Equity DD', 'Trades', 'JAM', 'CND', 'EMA', 'TTP', 'SLP']
            for c in cols_numeric:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce')
            
            # Konversi True/False ke 1/0
            hari_cols = ['SE', 'SS', 'R', 'K', 'J']
            for col in hari_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.lower().str.strip().map({'true': '1', 'false': '0'})

            # Membuat Key_ID
            df['Key_ID'] = (
                "JAM" + df['JAM'].fillna(0).astype(int).astype(str) + "_" +
                "CND" + df['CND'].fillna(0).astype(int).astype(str) + "_" +
                "EMA" + df['EMA'].fillna(0).astype(int).astype(str) + "_" +
                "TTP" + df['TTP'].fillna(0).astype(int).astype(str) + "_" +
                "SLP" + df['SLP'].fillna(0).astype(int).astype(str) + "_" +
                "DAYS" + df['SE'].fillna('0').astype(str) + df['SS'].fillna('0').astype(str) + 
                df['R'].fillna('0').astype(str) + df['K'].fillna('0').astype(str) + df['J'].fillna('0').astype(str)
            )

            st.success(f"✅ Berhasil! Ditemukan {len(df)} baris data.")
            
            # Preview Hasil Akhir
            st.subheader("Preview Data dengan Key ID")
            kolom_tampilan = ['Key_ID', 'Profit', 'Expected', 'Profit Fact', 'Equity DD', 'Trades']
            tersedia = [c for c in kolom_tampilan if c in df.columns]
            st.dataframe(df[tersedia].head(10))
            
        else:
            st.error("File XML tidak memiliki data yang cukup.")

    except Exception as e:
        st.error(f"Gagal membaca XML: {e}")
