import streamlit as st
import pandas as pd

st.set_page_config(page_title="Emlak Radar PRO", layout="wide")

# --- BÖLGE ENDEKSLERİ (Antalya Örneği) ---
# Bunları piyasaya göre buradan kolayca güncelleyebilirsin
REGION_DATA = {
    "Konyaaltı": {"m2_fiyat": 60000, "kira_m2": 300, "hedef_amortisman": 240}, # 20 yıl
    "Finike": {"m2_fiyat": 35000, "kira_m2": 150, "hedef_amortisman": 280},
    "Muratpaşa": {"m2_fiyat": 45000, "kira_m2": 250, "hedef_amortisman": 220}
}

st.title("🚀 Emlak Radar v1.0 - Yatırım Analiz Merkezi")

# --- VERİ YÜKLEME ---
try:
    # Botun gönderdiği CSV'yi oku
    df = pd.read_csv("cekilen_ilanlar.csv")
    
    # Analiz Hesaplamaları
    region = "Konyaaltı" # Şimdilik sabit, bottan gelen veriye göre değişebilir
    target = REGION_DATA[region]
    
    df['Birim_m2'] = df['Fiyat'] / df['Metrekare']
    df['Tahmini_Kira'] = df['Metrekare'] * target['kira_m2']
    df['Amortisman_Yil'] = df['Fiyat'] / (df['Tahmini_Kira'] * 12)
    
    # Yatırım Skoru Hesapla (0-100 arası)
    # Fiyat bölgeden ucuzsa ve amortisman süresi kısaysa puan artar
    df['Skor'] = 100 - ((df['Birim_m2'] / target['m2_fiyat']) * 30) - ((df['Amortisman_Yil'] / (target['hedef_amortisman']/12)) * 30)
    df['Skor'] = df['Skor'].clip(0, 100)

    # --- ARAYÜZ ---
    st.subheader(f"📍 {region} Bölgesi Analiz Sonuçları")
    
    # Özet Metrikler
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Taranan İlan", len(df))
    c2.metric("Bölge Ort. m²", f"{target['m2_fiyat']:,} TL")
    c3.metric("Fırsat Sayısı (Skor > 80)", len(df[df['Skor'] > 80]))

    st.divider()

    # Tabloyu Göster (Skora göre sıralı)
    st.write("### 💎 En İyi Yatırım Seçenekleri")
    
    # Görselleştirme: Skora göre renklendirme ve emoji ekleme
    def make_pretty(val):
        return '✅' if val > 80 else '⛔' if val < 50 else '🟡'

    df['Durum'] = df['Skor'].apply(make_pretty)
    
    display_df = df[['Durum', 'Skor', 'Fiyat', 'Metrekare', 'Amortisman_Yil', 'Birim_m2']].sort_values(by='Skor', ascending=False)
    
    st.dataframe(display_df.style.format({
        'Fiyat': '{:,.0f} TL',
        'Skor': '{:.1f}',
        'Amortisman_Yil': '{:.1f} Yıl',
        'Birim_m2': '{:,.0f} TL'
    }))

except Exception as e:
    st.warning("Henüz 'cekilen_ilanlar.csv' dosyası yüklenmemiş veya formatı hatalı. Lütfen botu çalıştırıp dosyayı GitHub'a yükleyin.")
    st.error(f"Hata Detayı: {e}")
