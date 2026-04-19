import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import plotly.express as px
import io

st.set_page_config(page_title="MT5 Portfolio Analyzer", layout="wide")
st.title("📊 MT5 Hedge Fund Strategy Analyzer")

st.sidebar.header("📂 Data & Filter")
uploaded_file = st.sidebar.file_uploader("Upload File XML MT5", type=["xml"])

min_trades = st.sidebar.slider("Minimal Total Trades", 0, 1000, 100)
min_sharpe = st.sidebar.number_input("Minimal Sharpe Ratio", value=0.15, step=0.01)
min_recovery = st.sidebar.number_input("Minimal Recovery Factor", value=3.0, step=0.1)

if uploaded_file is not None:
    try:
        # Membaca konten file
        string_data = uploaded_file.read().decode('utf-16' if 'utf-16' in str(uploaded_file) else 'utf-8')
        
        # MT5 XML sebenarnya adalah format spreadsheet (Excel XML)
        # Kita gunakan pandas read_xml jika tersedia, atau parse manual yang lebih fleksibel
        try:
            # Cara 1: Menggunakan fungsi bawaan pandas untuk XML spreadsheet
            df = pd.read_xml(io.StringIO(string_data), xpath=".//ss:Row", namespaces={'ss': 'urn:schemas-microsoft-com:office:spreadsheet'})
        except:
            # Cara 2: Manual Parsing jika Namespace bermasalah
            tree = ET.ElementTree(ET.fromstring(string_data))
            root = tree.getroot()
            
            all_rows = []
            # Mencari semua baris tanpa mempedulikan namespace
            for row in root.iter():
                if row.tag.endswith('Row'):
                    cells = [cell.text for cell in row.iter() if cell.tag.endswith('Data')]
                    if cells:
                        all_rows.append(cells)
            
            if len(all_rows) > 1:
                df = pd.DataFrame(all_rows[1:], columns=all_rows[0])
            else:
                st.error("Format data di dalam XML tidak ditemukan. Pastikan Anda melakukan klik kanan pada hasil optimasi MT5 lalu pilih 'Export to XML'.")
                st.stop()

        # Membersihkan Data
        df.columns = [str(c).strip() for c in df.columns]
        
        # Konversi kolom penting ke angka
        numeric_cols = ['Profit', 'Trades', 'Sharpe Ratio', 'Recovery Factor', 'Drawdown %', 'Expected Payoff']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r'[^-0-9.]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Hapus baris yang gagal dikonversi (kosong)
        df = df.dropna(subset=['Trades', 'Profit'])

        # Filter
        filtered_df = df[
            (df['Trades'] >= min_trades) & 
            (df['Sharpe Ratio'] >= min_sharpe) & 
            (df['Recovery Factor'] >= min_recovery)
        ].copy()

        if not filtered_df.empty:
            st.success(f"Ditemukan {len(filtered_df)} strategi yang memenuhi syarat.")
            
            # Perhitungan Final Score
            filtered_df['Final_Score'] = (filtered_df['Sharpe Ratio'] * 0.5) + (filtered_df['Recovery Factor'] * 0.5)
            filtered_df = filtered_df.sort_values('Final_Score', ascending=False)

            st.subheader("🏆 Top Strategi Hasil Filter")
            st.dataframe(filtered_df.head(15), use_container_width=True)

            fig = px.scatter(
                filtered_df, x="Drawdown %", y="Profit", size="Sharpe Ratio", color="Final_Score",
                hover_data=['Trades'], title="Visualisasi Portofolio"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Strategi ditemukan, tapi tidak ada yang lolos kriteria filter Anda.")

    except Exception as e:
        st.error(f"Terjadi kesalahan teknis: {e}")
