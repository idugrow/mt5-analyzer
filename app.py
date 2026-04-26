import pandas as pd

def modul_1_processing(file_path):
    # 1. Membaca data
    df = pd.read_csv(file_path)
    
    # 2. Drop kolom yang tidak diperlukan (Noise)
    kolom_dibuang = ['Pass', 'Result', 'Custom']
    df = df.drop(columns=[c for c in kolom_dibuang if c in df.columns])
    
    # 3. Konversi True/False menjadi 1/0 untuk kolom hari (SE, SS, R, K, J)
    hari_cols = ['SE', 'SS', 'R', 'K', 'J']
    for col in hari_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().map({'true': '1', 'false': '0'})

    # 4. Membuat Key_ID Unik
    # Format: JAM9_CND5_EMA10_TTP150_SLP900_SE0_SS1_R1_K1_J0
    df['Key_ID'] = (
        "JAM" + df['JAM'].astype(str) + "_" +
        "CND" + df['CND'].astype(str) + "_" +
        "EMA" + df['EMA'].astype(str) + "_" +
        "TTP" + df['TTP'].astype(str) + "_" +
        "SLP" + df['SLP'].astype(str) + "_" +
        "SE" + df['SE'].astype(str) + "_" +
        "SS" + df['SS'].astype(str) + "_" +
        "R" + df['R'].astype(str) + "_" +
        "K" + df['K'].astype(str) + "_" +
        "J" + df['J'].astype(str)
    )
    
    return df

# --- CARA COBA DI KOMPUTER ANDA ---
# Ganti 'nama_file_anda.csv' dengan file asli Anda
# df_hasil = modul_1_processing('nama_file_anda.csv')
# print(df_hasil[['Key_ID', 'Profit', 'Trades']].head())
