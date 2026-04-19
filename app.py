import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import plotly.express as px
import io

st.set_page_config(page_title="MT5 Portfolio Analyzer", layout="wide")
st.title("📊 MT5 Hedge Fund Strategy Analyzer")

st.sidebar.header("📂 Data & Filter")
uploaded_file = st.sidebar.file_uploader("Upload File XML MT5", type=["xml"])

# Filter UI
min_trades = st.sidebar.slider("Minimal Total Trades", 0, 1000, 100)
min_sharpe = st.sidebar.number_input("Minimal Sharpe Ratio", value=0.15, step=0.01)
min_recovery = st.sidebar.number_input("Minimal Recovery Factor", value=3.0, step=0.1)

if uploaded_file is not None:
    try:
        # Membaca konten file
        string_data = uploaded_file.read().decode('utf-16' if 'utf-16' in str(uploaded_file) else 'utf-8')
        
        # Manual Parsing untuk format XML MS Excel
        tree = ET.ElementTree(ET.fromstring(string_data))
        root = tree.getroot()
        
        all_rows = []
        for row in root.iter():
            if row.tag.endswith('Row'):
                cells = [cell.text for cell in row.iter() if cell.tag.endswith('Data')]
                if cells:
                    all_rows.append(cells)
        
        if len(all_rows) > 1:
            # Menggunakan baris pertama sebagai header
            df = pd.DataFrame(all_rows[1:], columns=all_rows[0])
            df.columns = [str(c).strip() for c in df.columns]

            # --- PENYESUAIAN NAMA KOLOM SESUAI FILE ANDA ---
            # Nama kolom drawdown di file Anda adalah 'Equity DD %'
            dd_col = 'Equity DD %' 
            
            # Konversi kolom penting ke angka
            numeric_cols = ['Profit', 'Trades', 'Sharpe Ratio', 'Recovery Factor', dd_col, 'Expected Payoff', 'Profit Factor']
            for col in numeric_cols:
                if col in df.columns:
                    # Bersihkan karakter non-numerik kecuali titik dan minus
                    df[col] = df[col].astype(str).str.replace(r'[^-0-9.]', '', regex=True)
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Hapus baris yang tidak valid
            df = df.dropna(subset=['Trades', 'Profit'])

            # Filter Logika
            filtered_df = df[
                (df['Trades'] >= min_trades) & 
                (df['Sharpe Ratio'] >= min_sharpe) & 
                (df['Recovery Factor'] >= min_recovery)
            ].copy()

            if not filtered_df.empty:
                st.success(f"✅ Berhasil! Ditemukan {len(filtered_df)} strategi tangguh.")
                
                # Skor Gabungan (Ranking)
                filtered_df['Final_Score'] = (filtered_df['Sharpe Ratio'] * 0.5) + (filtered_df['Recovery Factor'] * 0.5)
                filtered_df = filtered_df.sort_values('Final_Score', ascending=False)

                # Tampilan Tabel
                st.subheader("🏆 Top Strategi Hasil Filter")
                st.dataframe(filtered_df, use_container_width=True)

                # Visualisasi (Sudah disesuaikan ke 'Equity DD %')
                st.subheader("📈 Visualisasi Portofolio (Profit vs Drawdown)")
                fig = px.scatter(
                    filtered_df, 
                    x=dd_col, 
                    y="Profit", 
                    size="Sharpe Ratio", 
                    color="Final_Score",
                    hover_data=['Trades', 'Profit Factor', 'Expected Payoff'],
                    color_continuous_scale="Viridis",
                    labels={dd_col: "Drawdown (%)"},
                    title="Analisis Kualitas: Semakin ke kiri atas semakin baik"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Tombol Download
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Data Filtered (CSV)", csv, "strategi_pilihan.csv", "text/csv")
            else:
                st.warning("⚠️ Tidak ada strategi yang lolos kriteria filter.")
        else:
            st.error("❌ Data tidak ditemukan dalam file XML.")

    except Exception as e:
        st.error(f"Terjadi kesalahan teknis: {e}")
