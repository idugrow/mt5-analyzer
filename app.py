import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

st.set_page_config(page_title="Algo-Optimizer Model One", layout="wide")

# --- FUNGSI PENCARI KOLOM OTOMATIS (Mencegah KeyError) ---
def get_col(df, target_names):
    """Mencari kolom yang paling mendekati dari daftar nama yang mungkin."""
    for name in target_names:
        if name in df.columns:
            return name
    return None

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
            
            # Konversi kolom ke numerik dengan pencarian nama fleksibel
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
                col_name = get_col(df, options)
                if col_name:
                    new_df[key] = pd.to_numeric(df[col_name], errors='coerce')
                else:
                    # Jika kolom hari tidak ada, anggap True (1) agar tidak rusak
                    new_df[key] = 1 if key in ['SE', 'SS', 'R', 'K', 'J'] else 0

            # Hari Konversi (Jika aslinya string 'true'/'false')
            for h in ['SE', 'SS', 'R', 'K', 'J']:
                new_df[h] = new_df[h].apply(lambda x: '1' if str(x).lower() in ['true', '1', '1.0'] else '0')

            # Create Key_ID
            new_df['Key_ID'] = (
                "JAM" + new_df['JAM'].fillna(0).astype(int).astype(str) + "_" +
                "CND" + new_df['CND'].fillna(0).astype(int).astype(str) + "_" +
                "EMA" + new_df['EMA'].fillna(0).astype(int).astype(str) + "_" +
                "TTP" + new_df['TTP'].fillna(0).astype(int).astype(str) + "_" +
                "SLP" + new_df['SLP'].fillna(0).astype(int).astype(str) + "_" +
                "DAYS" + new_df['SE'] + new_df['SS'] + new_df['R'] + new_df['K'] + new_df['J']
            )
            return new_df
    except Exception as e:
        st.error(f"Error parse: {e}")
    return None

# --- UI UTAMA ---
st.title("🚀 Algo-Optimizer: Model One (Anti-Error Version)")

uploaded_files = st.file_uploader("Upload 5 File XML Anda", type=['xml'], accept_multiple_files=True)

if uploaded_files:
    if 'raw_dfs' not in st.session_state or len(st.session_state['raw_dfs']) != len(uploaded_files):
        st.session_state['raw_dfs'] = [parse_mt5_xml(f) for f in uploaded_files if parse_mt5_xml(f) is not None]

    if st.session_state['raw_dfs']:
        with st.sidebar:
            st.header("⚙️ Filter")
            m_trades = st.slider("Min Trades", 0, 200, 40)
            m_pf = st.slider("Min PF", 1.0, 3.0, 1.25, step=0.05)
            m_payoff = st.number_input("Min Payoff", 0.0, 10.0, 0.4)
            m_dd = st.slider("Max DD (%)", 1, 100, 15)

        filtered_dfs = []
        st.subheader("📊 Status")
        cols = st.columns(len(st.session_state['raw_dfs']))
        
        for i, df in enumerate(st.session_state['raw_dfs']):
            # Filter menggunakan nama kolom yang sudah distandarisasi ('Profit Fact')
            mask = (df['Trades'] >= m_trades) & (df['Profit Fact'] >= m_pf) & \
                   (df['Expected'] >= m_payoff) & (df['Equity DD'] <= m_dd)
            f_df = df[mask].copy()
            filtered_dfs.append(f_df)
            cols[i].metric(f"File {i+1}", f"{len(f_df)} Row")

        if st.button("🔍 CARI GOLDEN SETTING"):
            if len(filtered_dfs) >= 2:
                res_ids = set(filtered_dfs[0]['Key_ID'])
                for d in filtered_dfs[1:]:
                    res_ids = res_ids.intersection(set(d['Key_ID']))
                
                if res_ids:
                    st.success(f"Ditemukan {len(res_ids)} Parameter!")
                    combined = pd.concat([d[d['Key_ID'].isin(res_ids)] for d in filtered_dfs])
                    summary = combined.groupby('Key_ID').agg({
                        'Profit Fact': ['mean', 'std'], 'Profit': 'mean', 'Equity DD': 'max'
                    }).reset_index()
                    summary.columns = ['Key_ID', 'Avg_PF', 'Std_PF', 'Avg_Profit', 'Max_DD']
                    summary['Stability'] = 100 - (summary['Std_PF'].fillna(0) / summary['Avg_PF'] * 100)
                    st.dataframe(summary.sort_values('Stability', ascending=False))
                else:
                    st.error("Tidak ada irisan!")
