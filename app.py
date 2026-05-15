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

    # --- TABLO GÖSTERİMİ (Link ve Skor Destekli) ---
    st.write("### 💎 En İyi Yatırım Seçenekleri")
    
    # Emoji fonksiyonunu skor sütununa entegre edelim
    def get_status(val):
        if val > 80: return "✅ Fırsat"
        if val < 50: return "⛔ Riskli"
        return "🟡 Normal"

    df['Durum'] = df['Skor'].apply(get_status)
    
    # Eğer botun eski sürümü çalıştıysa ve Link sütunu yoksa kodun çökmesini engelle
    if 'Link' not in df.columns:
        df['Link'] = "https://www.emlakjet.com/satilik-konut/antalya-konyaalti/"
        
    # Gösterilecek sütunları seç (Link dahil)
    display_df = df[['Durum', 'Skor', 'Fiyat', 'Metrekare', 'Amortisman_Yil', 'Birim_m2', 'Link']].sort_values(by='Skor', ascending=False)
    
    st.data_editor(
        display_df,
        column_config={
            "Link": st.column_config.LinkColumn(
                "İlan Detayı",
                help="İlan sayfasına gitmek için tıkla",
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
        disabled=True, # Tablodaki verilerin elle değiştirilmesini engeller
        hide_index=True, # Sol baştaki 0,1,2 gibi indeks numaralarını gizler
        use_container_width=True # Tabloyu ekrana tam yayar
    )

except Exception as e:
    st.warning("Henüz 'cekilen_ilanlar.csv' dosyası yüklenmemiş veya formatı hatalı. Lütfen botu çalıştırıp dosyayı GitHub'a yükleyin.")
    st.error(f"Hata Detayı: {e}")
