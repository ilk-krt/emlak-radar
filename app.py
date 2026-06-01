import streamlit as st
import pandas as pd
import time
import re

st.set_page_config(page_title="Emlak Radar PRO", layout="wide")

# --- BÖLGE ENDEKSLERİ (Antalya Endeksleri) ---
REGION_DATA = {
    "Konyaaltı": {"m2_fiyat": 60000, "kira_m2": 300, "hedef_amortisman": 240}, 
    "Finike": {"m2_fiyat": 35000, "kira_m2": 150, "hedef_amortisman": 280},
    "Muratpaşa": {"m2_fiyat": 45000, "kira_m2": 250, "hedef_amortisman": 220}
}

st.title("🚀 Emlak Radar v1.0 - Yatırım Analiz Merkezi")

# --- 1. SORUNUN ÇÖZÜMÜ: ÖNBELLEK BYPASS & MANUEL GÜNCELLEME MOTORU ---
col_refresh, _ = st.columns([1, 4])
with col_refresh:
    if st.button("🔄 Verileri Yeniden Tara & Güncelle", use_container_width=True):
        st.cache_data.clear() # Tüm Streamlit veri belleğini sıfırlar
        st.toast("Bellek temizlendi, diskteki en güncel CSV dosyası okunuyor!", icon="🔄")
        time.sleep(0.3)

@st.cache_data
def load_and_sync_csv():
    # Dosyayı diskten önbellek korumalı okur
    return pd.read_csv("cekilen_ilanlar.csv")

# --- VERİ YÜKLEME VE ANALİZ HATTI ---
try:
    df_raw = load_and_sync_csv()
    df = df_raw.copy()
    
    # --- 2. SORUNUN ÇÖZÜMÜ: SÜTUN VE URL NORMALLEŞTİRME MOTORU ---
    # Sütun isimlerindeki gizli boşlukları temizle
    df.columns = df.columns.str.strip()
    
    # Botun yazabileceği olası link varyasyonlarını tek bir standart "Link" sütununa eşitle
    column_rename_matrix = {}
    for col in df.columns:
        if col.lower() in ['link', 'url', 'ilan_link', 'ilan_url', 'detay_link']:
            column_rename_matrix[col] = 'Link'
    
    if column_rename_matrix:
        df = df.rename(columns=column_rename_matrix)
        
    # Link sütunu hiç yoksa veya boşsa güvenli kategori yönlendirmesi sağla
    if 'Link' not in df.columns:
        df['Link'] = "https://www.emlakjet.com/satilik-konut/antalya-konyaalti/"
    else:
        # Link hücrelerindeki boşlukları temizle ve string'e dönüştür
        df['Link'] = df['Link'].astype(str).str.strip()
        
        # Göreceli (Relative) URL'leri ve protokol hatalarını onaran fonksiyon
        def sanitize_listing_url(url_str):
            if not url_str or url_str == 'nan' or url_str == '':
                return "https://www.emlakjet.com/satilik-konut/antalya-konyaalti/"
            
            # Çift slash ile başlayan hatalı protokolleri düzelt
            if url_str.startswith('//'):
                return "https:" + url_str
                
            # Eğer link doğrudan domain içermiyorsa (Örn: /ilan/satilik-daire-123)
            if not url_str.startswith('http://') and not url_str.startswith('https://'):
                base_domain = "https://www.emlakjet.com"
                if url_str.startswith('/'):
                    return base_domain + url_str
                else:
                    return base_domain + "/" + url_str
            return url_str

        df['Link'] = df['Link'].apply(sanitize_listing_url)

    # --- BÖLGE SEÇİM KOKPİTİ ---
    available_regions = list(REGION_DATA.keys())
    region = st.selectbox("Analiz Edilecek Yatırım Bölgesi:", available_regions, index=0)
    target = REGION_DATA[region]
    
    # Matematiksel Analiz Alanı
    df['Birim_m2'] = df['Fiyat'] / df['Metrekare']
    df['Tahmini_Kira'] = df['Metrekare'] * target['kira_m2']
    df['Amortisman_Yil'] = df['Fiyat'] / (df['Tahmini_Kira'] * 12)
    
    # Rasyonel Yatırım Skoru Formülü
    df['Skor'] = 100 - ((df['Birim_m2'] / target['m2_fiyat']) * 30) - ((df['Amortisman_Yil'] / (target['hedef_amortisman']/12)) * 30)
    df['Skor'] = df['Skor'].clip(0, 100)

    # --- METRİK GOSTERGELERİ ---
    st.subheader(f"📍 {region} Bölgesi Güncel Analiz Tablosu")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Filtrelenen İlan", len(df))
    c2.metric("Bölge Gösterge m² Değeri", f"{target['m2_fiyat']:,} TL")
    c3.metric("Yüksek Skorlu Fırsat Sayısı (Skor > 80)", len(df[df['Skor'] > 80]))

    st.divider()

    # --- TABLO MATRİSİ ---
    st.write("### 💎 En İyi Yatırım Seçenekleri")
    
    def get_status(val):
        if val > 80: return "✅ Fırsat"
        if val < 50: return "⛔ Riskli"
        return "🟡 Normal"

    df['Durum'] = df['Skor'].apply(get_status)
    
    display_df = df[['Durum', 'Skor', 'Fiyat', 'Metrekare', 'Amortisman_Yil', 'Birim_m2', 'Link']].sort_values(by='Skor', ascending=False)
    
    st.data_editor(
        display_df,
        column_config={
            "Link": st.column_config.LinkColumn(
                "İlan Detayı",
                help="Orijinal ilan sayfasına yönlendirir",
                display_text="İlanı Aç 🔗"
            ),
            "Fiyat": st.column_config.NumberColumn("Fiyat", format="%d TL"),
            "Skor": st.column_config.ProgressColumn(
                "Yatırım Skoru", 
                min_value=0, 
                max_value=100, 
                format="%.1f"
            ),
            "Amortisman_Yil": st.column_config.NumberColumn("Geri Dönüş", format="%.1f Yıl"),
            "Birim_m2": st.column_config.NumberColumn("Birim m²", format="%d TL")
        },
        disabled=True, 
        hide_index=True, 
        use_container_width=True 
    )

except Exception as e:
    st.warning("Veri kaynağı 'cekilen_ilanlar.csv' senkronize edilemedi veya dosya içeriği boş.")
    st.error(f"Hata Kodu: {e}")
