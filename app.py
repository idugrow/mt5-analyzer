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


# Cek apakah data sudah ada di session state dari Modul 1
if 'all_dfs' in st.session_state and len(st.session_state['all_dfs']) > 0:
    
    st.divider()
    st.header("🎯 FASE 2: Multi-Stage Filtering")
    
    # 1. Membuat Sidebar untuk Control Filter
    with st.sidebar:
        st.header("⚙️ Kriteria Filter")
        min_trades = st.slider("Minimal Trades", 0, 200, 40)
        min_pf = st.slider("Minimal Profit Factor", 1.0, 3.0, 1.25, step=0.05)
        min_payoff = st.number_input("Minimal Expected Payoff (Point)", 0.0, 5.0, 0.40, step=0.05)
        max_dd = st.slider("Maksimal Equity Drawdown (%)", 1, 100, 15)
        
        st.info(f"Kriteria saat ini:\n- Trades >= {min_trades}\n- PF >= {min_pf}\n- Payoff >= {min_payoff}\n- DD <= {max_dd}%")

    # 2. Proses Filtering untuk setiap file
    filtered_dfs = []
    
    st.subheader("📊 Hasil Penyaringan Per Periode")
    cols = st.columns(len(st.session_state['all_dfs']))
    
    for i, df in enumerate(st.session_state['all_dfs']):
        # Logika Filter
        mask = (
            (df['Trades'] >= min_trades) &
            (df['Profit Fact'] >= min_pf) &
            (df['Expected'] >= min_payoff) &
            (df['Equity DD'] <= max_dd)
        )
        
        df_filtered = df[mask].copy()
        filtered_dfs.append(df_filtered)
        
        # Tampilkan status di kolom dashboard
        with cols[i]:
            st.metric(label=f"File {i+1}", value=f"{len(df_filtered)} baris", delta=f"{len(df_filtered) - len(df)} terbuang", delta_color="inverse")

    # Simpan hasil filter ke session state untuk FASE 3
    st.session_state['filtered_dfs'] = filtered_dfs

    if any(len(d) == 0 for d in filtered_dfs):
        st.warning("⚠️ Perhatian: Ada periode yang memiliki 0 baris setelah difilter. Coba longgarkan kriteria slider Anda.")
    else:
        st.success("🔥 Semua periode memiliki kandidat pemenang. Siap lanjut ke FASE 3: Intersection?")
        if st.button("JALANKAN INTERSECTION (FASE 3)"):
            st.info("Tombol ditekan! Kita akan masuk ke logika pencarian irisan data.")
        st.session_state['all_dfs'] = all_dataframes
        st.info("Pondasi Fase 1 Selesai. Siap lanjut ke FASE 2: Filtering?")
# OKE
