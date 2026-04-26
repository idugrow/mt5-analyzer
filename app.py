import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import io

st.set_page_config(page_title="Algo-Optimizer Model One", layout="wide")

# --- FUNGSI PARSING XML (DIBERIKAN CACHE AGAR STABIL) ---
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
            # Cleaning kolom
            kolom_dibuang = ['Pass', 'Result', 'Custom']
            df = df.drop(columns=[c for c in kolom_dibuang if c in df.columns])
            # Numerik
            cols_numeric = ['Profit', 'Expected', 'Profit Fact', 'Recovery', 'Equity DD', 'Trades', 'JAM', 'CND', 'EMA', 'TTP', 'SLP']
            for c in cols_numeric:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce')
            # Hari
            hari_cols = ['SE', 'SS', 'R', 'K', 'J']
            for col in hari_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.lower().str.strip().map({'true': '1', 'false': '0'})
            # Key ID
            df['Key_ID'] = (
                "JAM" + df['JAM'].fillna(0).astype(int).astype(str) + "_" +
                "CND" + df['CND'].fillna(0).astype(int).astype(str) + "_" +
                "EMA" + df['EMA'].fillna(0).astype(int).astype(str) + "_" +
                "TTP" + df['TTP'].fillna(0).astype(int).astype(str) + "_" +
                "SLP" + df['SLP'].fillna(0).astype(int).astype(str) + "_" +
                "DAYS" + df['SE'].fillna('0').astype(str) + df['SS'].fillna('0').astype(str) + 
                df['R'].fillna('0').astype(str) + df['K'].fillna('0').astype(str) + df['J'].fillna('0').astype(str)
            )
            return df
    except Exception as e:
        st.error(f"Gagal memproses file: {e}")
    return None

# --- UI UTAMA ---
st.title("🚀 Algo-Optimizer: Model One (Stable Version)")

# 1. UPLOAD SECTION
uploaded_files = st.file_uploader("Upload 5 File XML Anda", type=['xml'], accept_multiple_files=True)

if uploaded_files:
    if 'raw_dfs' not in st.session_state:
        st.session_state['raw_dfs'] = []
        for f in uploaded_files:
            processed_df = parse_mt5_xml(f)
            if processed_df is not None:
                st.session_state['raw_dfs'].append(processed_df)

    if len(st.session_state['raw_dfs']) > 0:
        # 2. SIDEBAR FILTER
        with st.sidebar:
            st.header("⚙️ Filter Kriteria")
            m_trades = st.slider("Min Trades", 0, 200, 40)
            m_pf = st.slider("Min Profit Factor", 1.0, 3.0, 1.25, step=0.05)
            m_payoff = st.number_input("Min Payoff", 0.0, 10.0, 0.4)
            m_dd = st.slider("Max Drawdown (%)", 1, 100, 15)

        # 3. APPLY FILTER
        filtered_dfs = []
        st.subheader("📊 Status Per Periode")
        cols = st.columns(len(st.session_state['raw_dfs']))
        
        for i, df in enumerate(st.session_state['raw_dfs']):
            mask = (df['Trades'] >= m_trades) & (df['Profit Fact'] >= m_pf) & \
                   (df['Expected'] >= m_payoff) & (df['Equity DD'] <= m_dd)
            f_df = df[mask].copy()
            filtered_dfs.append(f_df)
            with cols[i]:
                st.metric(f"File {i+1}", f"{len(f_df)} Row")

        # 4. INTERSECTION BUTTON
        st.divider()
        if st.button("🔍 CARI GOLDEN SETTING"):
            if len(filtered_dfs) == 5:
                # Logika Intersection
                res_ids = set(filtered_dfs[0]['Key_ID'])
                for d in filtered_dfs[1:]:
                    res_ids = res_ids.intersection(set(d['Key_ID']))
                
                if res_ids:
                    st.success(f"Ditemukan {len(res_ids)} Parameter Lolos Semua Era!")
                    # Gabungkan untuk hitung skor
                    combined = pd.concat([d[d['Key_ID'].isin(res_ids)] for d in filtered_dfs])
                    summary = combined.groupby('Key_ID').agg({
                        'Profit Fact': ['mean', 'std'],
                        'Profit': 'mean',
                        'Equity DD': 'max'
                    }).reset_index()
                    summary.columns = ['Key_ID', 'Avg_PF', 'Std_PF', 'Avg_Profit', 'Max_DD']
                    summary['Stability'] = 100 - (summary['Std_PF'] / summary['Avg_PF'] * 100)
                    summary = summary.sort_values('Stability', ascending=False)
                    
                    st.dataframe(summary.style.highlight_max(axis=0, subset=['Stability']))
                else:
                    st.error("Tidak ada irisan. Longgarkan filter Anda!")
            else:
                st.warning("Harap upload tepat 5 file untuk hasil maksimal.")

# Tombol Reset jika ingin upload ulang dari nol
if st.sidebar.button("Clear Cache & Upload Ulang"):
    st.session_state.clear()
    st.cache_data.clear()
    st.rerun()
