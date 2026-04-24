import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="MT5 Quant Analyzer", layout="wide")

st.title("🛡️ Hedge Fund Optimization Filter")
st.markdown("""
Aplikasi ini menyaring hasil optimasi MetaTrader 5 (XML) untuk menemukan parameter yang paling robust.
Fokus pada **stabilitas**, bukan sekadar profit besar.
""")

# --- SIDEBAR: KONTROL FILTER ---
st.sidebar.header("📂 Data & Parameter")
uploaded_file = st.sidebar.file_uploader("Upload File XML MT5", type=["xml"])

st.sidebar.subheader("🎯 Batas Minimal")
min_trades = st.sidebar.slider("Minimal Trades", 0, 1000, 100)
min_sharpe = st.sidebar.number_input("Minimal Sharpe Ratio", value=0.15, step=0.01)
min_recovery = st.sidebar.number_input("Minimal Recovery Factor", value=3.0, step=0.1)

st.sidebar.subheader("⚖️ Scoring Weight")
w_sharpe = st.sidebar.slider("Bobot Sharpe Ratio", 0.0, 1.0, 0.5)
w_recovery = 1.0 - w_sharpe

# --- FUNGSI PEMBANTU ---
def parse_mt5_xml(file):
    tree = ET.parse(file)
    root = tree.getroot()
    
    rows = []
    # Mencari tag Row yang berisi data Cell
    for row in root.findall(".//Row"):
        cols = [col.text if col.text is not None else "" for col in row.findall(".//Cell")]
        if cols:
            rows.append(cols)
    return rows

# --- LOGIKA UTAMA ---
if uploaded_file is not None:
    try:
        data_rows = parse_mt5_xml(uploaded_file)
        
        if len(data_rows) > 1:
            # Ambil header dan data
            df = pd.DataFrame(data_rows[1:], columns=data_rows[0])
            
            # 1. Bersihkan Nama Kolom (Hapus spasi)
            df.columns = [str(c).strip() for c in df.columns]
            
            # 2. Kamus Pemetaan Kolom (Bahasa Inggris & Indonesia)
            mapping = {
                'Trades': ['Trades', 'Transaksi', 'Total Trades'],
                'Profit': ['Profit', 'Keuntungan', 'Net Profit'],
                'Sharpe Ratio': ['Sharpe Ratio', 'Sharpe', 'Nisbah Sharpe'],
                'Recovery Factor': ['Recovery Factor', 'Recovery', 'Faktor Pemulihan'],
                'Drawdown %': ['Drawdown %', 'Drawdown', 'Penurunan %']
            }
            
            # Ganti nama kolom secara otomatis jika ditemukan kecocokan
            for standard_name, aliases in mapping.items():
                for alias in aliases:
                    if alias in df.columns:
                        df.rename(columns={alias: standard_name}, inplace=True)
                        break

            # 3. Konversi Data ke Angka (Hapus simbol $, %, dll)
            target_cols = ['Profit', 'Trades', 'Sharpe Ratio', 'Recovery Factor', 'Drawdown %']
            for col in target_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(r'[^-0-9.]', '', regex=True)
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # 4. Filter Data
            # Pastikan kolom yang dibutuhkan ada
            required = ['Trades', 'Sharpe Ratio', 'Recovery Factor']
            if all(item in df.columns for item in required):
                
                filtered_df = df[
                    (df['Trades'] >= min_trades) & 
                    (df['Sharpe Ratio'] >= min_sharpe) & 
                    (df['Recovery Factor'] >= min_recovery)
                ].copy()

                if not filtered_df.empty:
                    # Perhitungan Skor Final
                    filtered_df['Final_Score'] = (filtered_df['Sharpe Ratio'] * w_sharpe) + (filtered_df['Recovery Factor'] * w_recovery)
                    filtered_df = filtered_df.sort_values('Final_Score', ascending=False)

                    # Tampilan Metrik Ringkasan
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Kandidat Lolos", len(filtered_df))
                    c2.metric("Profit Tertinggi", f"{filtered_df['Profit'].max():,.0f}")
                    c3.metric("Sharpe Tertinggi", f"{filtered_df['Sharpe Ratio'].max():.2f}")

                    # Visualisasi Scatter Plot
                    st.subheader("📈 Visualisasi Robustness")
                    fig = px.scatter(
                        filtered_df, 
                        x="Drawdown %", 
                        y="Profit", 
                        size="Sharpe Ratio", 
                        color="Final_Score",
                        hover_data=['Trades', 'Recovery Factor'],
                        color_continuous_scale="RdYlGn",
                        template="plotly_dark",
                        height=600
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Tabel Hasil
                    st.subheader("🏆 Daftar Parameter Terbaik")
                    st.dataframe(filtered_df.head(20), use_container_width=True)
                    
                    # Download Button
                    csv = filtered_df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Simpan Hasil Filter (CSV)", csv, "MT5_Filtered_Results.csv", "text/csv")
                else:
                    st.warning("⚠️ Tidak ada data yang lolos filter. Coba turunkan kriteria di sidebar.")
            else:
                st.error(f"❌ Kolom wajib tidak ditemukan. Kolom yang ada: {df.columns.tolist()}")
        else:
            st.error("❌ File XML kosong atau tidak memiliki baris data.")
            
    except Exception as e:
        st.error(f"Terjadi kesalahan teknis: {e}")
else:
    st.info("👋 Selamat datang! Silakan unggah file XML hasil optimasi MT5 Anda untuk memulai.")
