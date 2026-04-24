import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import plotly.express as px

# Konfigurasi Tampilan
st.set_page_config(page_title="MT5 Quant Analyzer", layout="wide")

st.title("🛡️ Hedge Fund Optimization Filter")
st.markdown("Fokus pada stabilitas: Saring parameter terbaik berdasarkan Sharpe dan Recovery.")

# --- SIDEBAR: KONTROL FILTER ---
st.sidebar.header("📂 Data & Parameter")
uploaded_file = st.sidebar.file_uploader("Upload File XML MT5", type=["xml"])

# Filter Teknis (Hanya yang esensial)
st.sidebar.subheader("🎯 Batas Minimal")
min_trades = st.sidebar.slider("Minimal Trades", 0, 1000, 100)
min_sharpe = st.sidebar.number_input("Minimal Sharpe Ratio", value=0.15, step=0.01)
min_recovery = st.sidebar.number_input("Minimal Recovery Factor", value=3.0, step=0.1)

# Pembobotan Skor Final
st.sidebar.subheader("⚖️ Scoring Weight")
w_sharpe = st.sidebar.slider("Bobot Sharpe Ratio", 0.0, 1.0, 0.5)
w_recovery = 1.0 - w_sharpe

# --- PROSES DATA ---
if uploaded_file is not None:
    try:
        # Parsing XML MT5
        tree = ET.parse(uploaded_file)
        root = tree.getroot()
        
        rows = []
        for row in root.findall(".//Row"):
            cols = [col.text if col.text is not None else "" for col in row.findall(".//Cell")]
            if cols: rows.append(cols)
        
        if len(rows) > 1:
            df = pd.DataFrame(rows[1:], columns=rows[0])
            
            # Cleaning & Conversion (Menghapus %, $, dan koma)
            numeric_cols = ['Profit', 'Trades', 'Sharpe Ratio', 'Recovery Factor', 'Drawdown %', 'Profit Factor']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(r'[^-0.9.]', '', regex=True)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # FILTERING (Expected Payoff dihapus dari sini)
            filtered_df = df[
                (df['Trades'] >= min_trades) & 
                (df['Sharpe Ratio'] >= min_sharpe) & 
                (df['Recovery Factor'] >= min_recovery)
            ].copy()

            if not filtered_df.empty:
                # PERHITUNGAN FINAL SCORE
                filtered_df['Final_Score'] = (filtered_df['Sharpe Ratio'] * w_sharpe) + (filtered_df['Recovery Factor'] * w_recovery)
                filtered_df = filtered_df.sort_values('Final_Score', ascending=False)

                # DASHBOARD UTAMA
                col1, col2, col3 = st.columns(3)
                col1.metric("Kandidat Lolos", len(filtered_df))
                col2.metric("Top Profit", f"{filtered_df['Profit'].max():,.0f}")
                col3.metric("Top Sharpe", f"{filtered_df['Sharpe Ratio'].max():.2f}")

                # VISUALISASI: SCATTER PLOT
                st.subheader("📈 Peta Kualitas Parameter")
                fig = px.scatter(
                    filtered_df, 
                    x="Drawdown %", 
                    y="Profit", 
                    size="Sharpe Ratio", 
                    color="Final_Score",
                    hover_data=['Trades', 'Recovery Factor'],
                    color_continuous_scale="RdYlGn",
                    height=600
                )
                st.plotly_chart(fig, use_container_width=True)

                # TABEL DATA
                st.subheader("🏆 Tabel Parameter Terbaik")
                st.dataframe(filtered_df.head(15), use_container_width=True)
                
                # DOWNLOAD HASIL
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Filtered Results (CSV)", csv, "HedgeFund_Results.csv", "text/csv")
                
            else:
                st.warning("⚠️ Kriteria terlalu ketat. Tidak ada parameter yang lolos filter.")
        else:
            st.error("❌ File XML tidak berisi data tabel yang valid.")
            
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Silakan upload file XML dari MT5 Anda untuk memulai analisis.")
