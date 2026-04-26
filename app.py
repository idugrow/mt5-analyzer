import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import re

# --- FUNGSI MEMBERSIHKAN STRING ANGKA ---
def clean_numeric(value):
    if value is None: return 0.0
    # Ambil hanya angka, titik, dan tanda minus (menghapus spasi, currency, dll)
    cleaned = re.sub(r'[^0-9.\-]', '', str(value))
    try:
        return float(cleaned)
    except:
        return 0.0

@st.cache_data
def parse_mt5_xml(uploaded_file):
    try:
        tree = ET.parse(uploaded_file)
        root = tree.getroot()
        ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
        rows = root.findall('.//ss:Worksheet[1]//ss:Table//ss:Row', ns)
        
        data = []
        for row in rows:
            cells = [cell.text for cell in row.findall('.//ss:Data', ns)]
            data.append(cells)
        
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Mapping kolom asli ke nama standar kita
            mapping = {
                'Profit': ['Profit'],
                'Expected': ['Expected', 'Expected Payoff', 'Payoff'],
                'Profit Fact': ['Profit Fact', 'Profit factor', 'PF'],
                'Equity DD': ['Equity DD', 'Equity DD %', 'Drawdown (%)'],
                'Trades': ['Trades', 'Total Trades'],
                'JAM': ['JAM'], 'CND': ['CND'], 'EMA': ['EMA'], 
                'TTP': ['TTP'], 'SLP': ['SLP'],
                'SE': ['SE'], 'SS': ['SS'], 'R': ['R'], 'K': ['K'], 'J': ['J']
            }

            new_df = pd.DataFrame()
            for key, options in mapping.items():
                # Cari kolom di df asli
                found_col = None
                for opt in options:
                    if opt in df.columns:
                        found_col = opt
                        break
                
                if found_col:
                    # GUNAKAN PEMBERSIH ANGKA YANG LEBIH KUAT
                    new_df[key] = df[found_col].apply(clean_numeric)
                else:
                    new_df[key] = 1.0 if key in ['SE', 'SS', 'R', 'K', 'J'] else 0.0

            # Konversi khusus Hari ke String '1'/'0' untuk Key_ID
            for h in ['SE', 'SS', 'R', 'K', 'J']:
                new_df[h] = new_df[h].apply(lambda x: '1' if x > 0 else '0')

            # Create Key_ID
            new_df['Key_ID'] = (
                "JAM" + new_df['JAM'].astype(int).astype(str) + "_" +
                "CND" + new_df['CND'].astype(int).astype(str) + "_" +
                "EMA" + new_df['EMA'].astype(int).astype(str) + "_" +
                "TTP" + new_df['TTP'].astype(int).astype(str) + "_" +
                "SLP" + new_df['SLP'].astype(int).astype(str) + "_" +
                "DAYS" + new_df['SE'] + new_df['SS'] + new_df['R'] + new_df['K'] + new_df['J']
            )
            return new_df
    except Exception as e:
        st.error(f"Error parsing file: {e}")
    return None

# --- BAGIAN FILTERING DI DALAM UI ---
# Pastikan saat melakukan mask, kita memastikan semua kolom adalah numerik
if 'raw_dfs' in st.session_state:
    # ... (bagian slider sama seperti sebelumnya) ...
    
    filtered_dfs = []
    for i, df in enumerate(st.session_state['raw_dfs']):
        # Tambahkan konversi eksplisit ke float sebelum filtering untuk keamanan double
        mask = (
            (df['Trades'].astype(float) >= float(m_trades)) & 
            (df['Profit Fact'].astype(float) >= float(m_pf)) & 
            (df['Expected'].astype(float) >= float(m_payoff)) & 
            (df['Equity DD'].astype(float) <= float(m_dd))
        )
        f_df = df[mask].copy()
        filtered_dfs.append(f_df)
        # ...
