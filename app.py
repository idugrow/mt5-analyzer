import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import plotly.express as px
import io

st.set_page_config(page_title="Hedge Fund Strategy Analyzer", layout="wide")
st.title("📊 Hedge Fund Portfolio Optimizer")
st.markdown("Dashboard analisis strategi otomatis dengan standar manajemen risiko institusi.")

# Sidebar Filter
st.sidebar.header("🛡️ Kriteria Filter")
min_trades = st.sidebar.number_input("Min. Trades", value=100, step=10)
min_sharpe = st.sidebar.number_input("Min. Sharpe Ratio", value=0.15, format="%.2f", step=0.01)
min_recovery = st.sidebar.number_input("Min. Recovery Factor", value=3.0, format="%.1f", step=0.1)
min_pf = st.sidebar.number_input("Min. Profit Factor", value=1.5, format="%.1f", step=0.1)
min_payoff = st.sidebar.number_input("Min. Expected Payoff ($)", value=5.0, format="%.1f", step=0.5)
max_dd = st.sidebar.slider("Max. Equity DD (%)", 0.0, 100.0, 10.0, step=0.5)
min_profit = st.sidebar.number_input("Min. Net Profit ($)", value=0.1, step=10.0)

st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("Upload File XML MT5", type=["xml"])

if uploaded_file is not None:
    try:
        string_data = uploaded_file.read().decode('utf-16' if 'utf-16' in str(uploaded_file) else 'utf-8')
        tree = ET.ElementTree(ET.fromstring(string_data))
        root = tree.getroot()
        
        all_rows = []
        for row in root.iter():
            if row.tag.endswith('Row'):
                cells = [cell.text for cell in row.iter() if cell.tag.endswith('Data')]
                if cells: all_rows.append(cells)
        
        if len(all_rows) > 1:
            df = pd.DataFrame(all_rows[1:], columns=all_rows[0])
            df.columns = [str(c).strip() for c in df.columns]

            # 1. MENGHAPUS KOLOM PASS (Jika ada)
            if 'Pass' in df.columns:
                df = df.drop(columns=['Pass'])

            dd_col = 'Equity DD %'
            numeric_cols = ['Profit', 'Trades', 'Sharpe Ratio', 'Recovery Factor', dd_col, 'Expected Payoff', 'Profit Factor']
            
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(r'[^-0-9.]', '', regex=True)
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            df = df.dropna(subset=['Trades', 'Profit'])

            # Filter
            mask = (
                (df['Trades'] >= min_trades) &
                (df['Sharpe Ratio'] >= min_sharpe) &
                (df['Recovery Factor'] >= min_recovery) &
                (df['Profit Factor'] >= min_pf) &
                (df['Expected Payoff'] >= min_payoff) &
                (df[dd_col] <= max_dd) &
                (df['Profit'] >= min_profit)
            )
            filtered_df = df[mask].copy()

            if not filtered_df.empty:
                st.success(f"✅ Filter Berhasil: {len(filtered_df)} Strategi Lolos Seleksi.")
                
                filtered_df['Rank_Score'] = (filtered_df['Sharpe Ratio'] * 0.5) + (filtered_df['Recovery Factor'] * 0.5)
                filtered_df = filtered_df.sort_values('Rank_Score', ascending=False)

                # Tabel Tanpa Kolom Pass
                st.subheader("🏆 Strategi Pilihan Berdasarkan Stabilitas")
                st.dataframe(filtered_df, use_container_width=True)

                # Grafik
                st.subheader("📈 Analisis Sebaran Risiko & Profit")
                fig = px.scatter(
                    filtered_df, x=dd_col, y="Profit", size="Sharpe Ratio", color="Rank_Score",
                    hover_data=['Profit Factor', 'Expected Payoff'],
                    labels={dd_col: "Equity Drawdown (%)"},
                    color_continuous_scale="RdYlGn"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Ekspor Data ke CSV", csv, "filtered_portfolio.csv", "text/csv")
            else:
                st.warning("⚠️ Tidak ada strategi yang lolos filter.")
        else:
            st.error("❌ Data tidak ditemukan.")
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
