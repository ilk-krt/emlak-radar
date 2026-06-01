import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Emlak Radar PRO", layout="wide")

# --- 1. BÖLGE ENDEKSLERİ (ÇIRALI EKLENDİ) ---
REGION_DATA = {
    "Konyaaltı": {"m2_fiyat": 60000, "kira_m2": 300, "hedef_amortisman": 240}, 
    "Çıralı": {"m2_fiyat": 90000, "kira_m2": 600, "hedef_amortisman": 180}, # Turistik/Bungalow bölgesi (Kısa amortisman)
    "Finike": {"m2_fiyat": 35000, "kira_m2": 150, "hedef_amortisman": 280},
    "Muratpaşa": {"m2_fiyat": 45000, "kira_m2": 250, "hedef_amortisman": 220}
}

st.title("🚀 Emlak Radar v1.1 - Yatırım Analiz Merkezi")

# --- 2. ZORUNLU GÜNCELLEME BUTONU ---
# Bu buton sayfayı yeniden yükler. Cache (önbellek) kullanmadığımız için 
# her tıklamada diskteki "cekilen_ilanlar.csv" dosyası ZORLA yeniden okunur.
col_btn, _ = st.columns([1, 4])
with col_btn:
    if st.button("🔄 İlanları Diskten Zorla Yeniden Oku", type="primary", use_container_width=True):
        st.rerun()

# --- 3. DİSKTEN CANLI VERİ OKUMA (ÖNBELLEKSİZ) ---
def load_live_csv():
    # st.cache_data KALDIRILDI! Asla eski veriyi tutmaz.
    return pd.read_csv("cekilen_ilanlar.csv")

try:
    df = load_live_csv()
    
    # Sütun isimlerindeki boşlukları temizle
    df.columns = df.columns.str.strip()
    
    # Olası tüm link sütunu isimlerini "Link" olarak standartlaştır
    rename_dict = {}
    for col in df.columns:
        if col.lower() in ['link', 'url', 'ilan_link', 'ilan_url', 'detay_link']:
            rename_dict[col] = 'Link'
    if rename_dict:
        df = df.rename(columns=rename_dict)
        
    if 'Link' not in df.columns:
        df['Link'] = "https://www.google.com/search?q=antalya+emlak" # Sütun hiç yoksa güvenlik ağı
        
    # --- 4. ZIRHLI LİNK ONARIM MOTORU ---
    def force_valid_url(val):
        val = str(val).strip()
        if pd.isna(val) or val.lower() == 'nan' or val == '':
            return "https://www.google.com"
            
        # 1. Aşama: Eğer hücrenin içinde "http" ile başlayan bir link varsa (örn HTML içindeyse) onu çekip çıkar.
        urls = re.findall(r'(https?://[^\s"\'<>]+)', val)
        if urls: 
            return urls[0]
            
        # 2. Aşama: Linkte "http" yok ama emlak sitesinin kendi yoluysa
        if val.startswith('www.'): 
            return 'https://' + val
        if val.startswith('//'): 
            return 'https:' + val
        if val.startswith('/'): 
            return 'https://www.emlakjet.com' + val # Göreceli linkse varsayılan siteyi ekle
            
        # 3. Aşama: Sadece saçma sapan bir metin geldiyse, direkt https:// eklemeyi dene
        if "." in val:
            return "https://" + val
            
        return "https://www.google.com/search?q=" + val.replace(" ", "+")

    df['Link'] = df['Link'].apply(force_valid_url)

    # --- 5. BÖLGE SEÇİMİ VE ANALİZ ---
    region = st.selectbox("Analiz Edilecek Yatırım Bölgesi:", list(REGION_DATA.keys()), index=0)
    target = REGION_DATA[region]
    
    # Hata almamak için sayısal sütunları temizle ve dönüştür
    df['Fiyat'] = pd.to_numeric(df['Fiyat'], errors='coerce').fillna(0)
    df['Metrekare'] = pd.to_numeric(df['Metrekare'], errors='coerce').fillna(1) # Sıfıra bölme hatasını engellemek için
    
    df['Birim_m2'] = df['Fiyat'] / df['Metrekare']
    df['Tahmini_Kira'] = df['Metrekare'] * target['kira_m2']
    df['Amortisman_Yil'] = df['Fiyat'] / (df['Tahmini_Kira'] * 12)
    
    df['Skor'] = 100 - ((df['Birim_m2'] / target['m2_fiyat']) * 30) - ((df['Amortisman_Yil'] / (target['hedef_amortisman']/12)) * 30)
    df['Skor'] = df['Skor'].clip(0, 100)

    # --- 6. ARAYÜZ VE TABLO ---
    st.subheader(f"📍 {region} Bölgesi Güncel Analiz Tablosu")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Filtrelenen İlan", len(df))
    c2.metric("Bölge Gösterge m² Değeri", f"{target['m2_fiyat']:,} TL")
    c3.metric("Yüksek Skorlu Fırsat Sayısı (Skor > 80)", len(df[df['Skor'] > 80]))

    st.divider()

    def get_status(val):
        if val >= 80: return "✅ Fırsat"
        if val <= 50: return "⛔ Riskli"
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
                min_value=0, max_value=100, format="%.1f"
            ),
            "Amortisman_Yil": st.column_config.NumberColumn("Geri Dönüş", format="%.1f Yıl"),
            "Birim_m2": st.column_config.NumberColumn("Birim m²", format="%d TL")
        },
        disabled=True, 
        hide_index=True, 
        use_container_width=True 
    )

except Exception as e:
    st.warning("Veri okunamadı. Botun 'cekilen_ilanlar.csv' dosyasını çalışma dizinine başarıyla kaydettiğinden emin olun.")
    st.error(f"Teknik Hata Detayı: {e}")
