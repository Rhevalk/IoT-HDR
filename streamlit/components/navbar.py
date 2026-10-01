import streamlit as st
from datetime import datetime

def navbar():
    st.markdown(f"""
    <style>
        /* 1. Header Utama */
        header[data-testid="stHeader"] {{
            height: 3.5rem;
            position: relative;
            display: flex;
            align-items: center;
            border-bottom: none !important;
        }}

        /* 2. Judul di Sisi Kiri */
        header[data-testid="stHeader"]::before {{
            content: "CIN Fram Dashboard";
            font-weight: bold;
            font-size: 28px;
            position: absolute;
            left: 80px;
            top: 50%;
            transform: translateY(-50%);
            white-space: nowrap;
        }}

        /* 3. Jam di Sisi Kanan (Sebelum Titik Tiga) */
        /* Kita gunakan selector khusus agar tidak bentrok */
        [data-testid="stStatusWidget"] {{
            visibility: hidden;
            display: none !important;
        }}

        header[data-testid="stHeader"]::after {{
            content: "{datetime.now().strftime('%H:%M:%S')}";
            font-size: 20px;
            position: absolute;
            right: 60px; /* Jarak pas sebelum ⋮ */
            top: 50%;
            transform: translateY(-50%);
            font-weight: 600;
        }}

        /* 4. Border Bawah Modern (Tidak Full) */
        /* Kita tempelkan ke kontainer pembungkus utama */
        .stApp {{
            border-top: 1px solid transparent;
        }}
        
        /* Garis melayang di bawah header */
        header[data-testid="stHeader"] {{
            height: 3.5rem;
            position: fixed;
            display: flex;
            align-items: center;
           
            /* Efek Bayangan Melayang */
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.05); 
            border-bottom: none !important;
            z-index: 999;
        }}
        
        /* Menghapus garis lama agar tidak bentrok */
        header[data-testid="stHeader"] > div:first-child::after {{
            content: none !important;
        }}

        /* 5. Bersihkan Elemen Bawaan */
        header[data-testid="stHeader"] .stDeployButton {{
            display: none;
        }}

        /* 5. Paksa Hapus Tombol Deploy & Kontainer Toolbar */

        /* Menghapus kontainer tombol deploy berdasarkan test-id */
        div[data-testid="stDeploymentButton"] {{
            display: none !important;
        }}
        
        /* Menghapus wrapper tombol (div yang Anda temukan) */
        div[data-testid="stToolbarActions"] {{
            display: none !important;
        }}
        
        /* Menghapus tombol header secara umum agar tidak muncul kembali saat update */
        button[data-testid="stBaseButton-header"] {{
            display: none !important;
        }}
        
        /* Menghilangkan spasi kosong yang ditinggalkan di sisi kanan */
        header[data-testid="stHeader"] .stToolbar {{
            display: none !important;
        }}
        
        /* Penyesuaian padding agar konten tidak tertutup header kustom */
        .block-container {{
            padding-top: 4.5rem;
        }}
    </style>
    """, unsafe_allow_html=True)
