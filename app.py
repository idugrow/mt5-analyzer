import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import plotly.express as px

# Konfigurasi Tampilan
st.set_page_config(page_title="MT5 Portfolio Analyzer", layout="wide")

st.title("📊 MT5 Hedge Fund Strategy Analyzer")
st.markdown("Analisis hasil optimasi MT5 secara sistematis untuk membangun portofolio yang stabil.")

# Sidebar untuk Kontrol
st.sidebar.header("📂 Data & Filter")
uploaded_file = st.sidebar.file_uploader("Upload File XML MT5", type=["xml"])

min_trades = st.sidebar.slider("Minimal Total Trades", 0, 1000, 100)
min_sharpe = st.sidebar.number_input("Minimal Sharpe Ratio", value=0.15, step=0.01)
min_recovery = st.sidebar.number_input("Minimal Recovery Factor", value=3.0, step=0.1)

# Pembobotan Skor
st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ Scoring Weight")
w_sharpe = st.sidebar.slider("Bobot Sharpe", 0.0, 1.0, 0.5)
w_recovery = st.sidebar.slider("Bobot Recovery", 0.0, 1.0, 0.5)

if uploaded_file is not None:
    try:
        # Parsing XML
        tree = ET.parse(uploaded_file)
        root = tree.getroot()
        
        # Mencari tabel data dalam struktur XML MT5
        rows = []
        for row in root.findall(".//Row"):
            cols = [col.text if col.text is not None else "" for col in row.findall(".//Cell")]
            if cols:
                rows.append(cols)
        
        if len(rows) > 1:
            # Baris pertama sebagai header
            df = pd.DataFrame(rows[1:], columns=rows[0])
            
            # Membersihkan data (Konversi string ke angka)
            numeric_cols = ['Profit', 'Trades', 'Sharpe Ratio', 'Recovery Factor', 'Drawdown %', 'Expected Payoff', 'Profit Factor']
            for col in numeric_cols:
                if col in df.columns:
                    # Hapus spasi, koma, persen, dan simbol mata uang
                    df[col] = df[col].astype(str).str.replace(r'[^-0.9.]', '', regex=True)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Filter Data sesuai input sidebar
            filtered_df = df[
                (df['Trades'] >= min_trades) & 
                (df['Sharpe Ratio'] >= min_sharpe) & 
                (df['Recovery Factor'] >= min_recovery)
            ].copy()

            if not filtered_df.empty:
                # Perhitungan Skor Gabungan
                # Normalisasi sederhana untuk ranking
                filtered_df['Final_Score'] = (
                    (filtered_df['Sharpe Ratio'] * w_sharpe) + 
                    (filtered_df['Recovery Factor'] * w_recovery)
                )
                filtered_df = filtered_df.sort_values('Final_Score', ascending=False)

                # Indikator Ringkasan
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Strategi", len(df))
                c2.metric("Lolos Filter", len(filtered_df))
                c3.metric("Top Sharpe", f"{filtered_df['Sharpe Ratio'].max():.2f}")

                # Tabel 10 Besar
                st.subheader("🏆 Top 10 Strategi Paling Robust")
                st.dataframe(filtered_df.head(10), use_container_width=True)

                # Grafik Analisis
                st.subheader("📈 Peta Kekuatan Strategi (Profit vs Drawdown)")
                fig = px.scatter(
                    filtered_df, 
                    x="Drawdown %", 
                    y="Profit", 
                    size="Sharpe Ratio", 
                    color="Final_Score",
                    hover_data=['Trades', 'Expected Payoff'],
                    color_continuous_scale="Viridis",
                    title="Titik yang besar dan berada di kiri atas adalah strategi terbaik"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Fitur Download Hasil Filter
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Hasil Filter (CSV)", csv, "filtered_strategies.csv", "text/csv")
                
            else:
                st.warning("⚠️ Tidak ada strategi yang memenuhi kriteria filter. Coba turunkan batasan Anda.")
        else:
            st.error("❌ Struktur file XML tidak dikenali. Pastikan ini hasil export optimasi MT5.")
            
    except Exception as e:
        st.error(f"Gagal memproses file: {e}")
else:
    st.info("💡 Silakan upload file XML hasil optimasi dari MetaTrader 5 Anda untuk memulai analisis.")
