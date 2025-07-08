# Snake AI - Generation 11 (v0.10)

## Genel Yapı
- **Model Tipi**: Deep Q-Learning (DQN) tabanlı bir sinir ağı
- **Kullanım Amacı**: Snake oyununu öğrenen ve oynayan yapay zeka sistemi

## Ağ Mimarisi
1. **Giriş Katmanı**
   - Toplam 33 nöron
   - 25 nöron (5x5 görüş matrisi)
   - 4 nöron (yemek yönü vektörü)
   - 4 nöron (mevcut yön vektörü)

2. **Gizli Katmanlar**
   - İlk katman: 128 nöron + ReLU
   - İkinci katman: 128 nöron + ReLU
   - Üçüncü katman: 64 nöron + ReLU

3. **Çıkış Katmanı**
   - 3 nöron (düz, sağa dön, sola dön)

## Öğrenme Parametreleri
- **Batch Size**: 128
- **Bellek Kapasitesi**: 200,000 deneyim
- **Gamma (İndirim Faktörü)**: 0.99
- **Başlangıç Epsilon**: 1.0
- **Minimum Epsilon**: 0.001
- **Hedef Oyun Sayısı**: 200
- **Hedef Ağ Güncelleme**: Her 400 adımda bir

## Dropout Mekanizması
- İlk katman: %20
- İkinci katman: %30
- Üçüncü katman: %30
- Not: Dropout sadece eğitimin belirli bir aşamasından sonra aktif olur

## Ödül Sistemi
1. **Yemek Ödülü**: +12.0
2. **Ölüm Cezası**: -15.0
3. **Hayatta Kalma Puanı**:
   - Dinamik sistem
   - Yılan uzunluğuna bağlı
   - Başlangıç: +0.1'den başlayıp azalıyor
   - İzin verilen adım sayısı = 50 + (yılan_uzunluğu * 3)

## Özel Özellikler
- Çift ağ sistemi (DQN + Hedef Ağ)
- Dinamik dropout aktivasyonu
- Adaptif hayatta kalma ödül sistemi
- Deneyim tekrarı (Experience Replay)
- Epsilon-greedy keşif stratejisi

## Görüş Sistemi
- 5x5 görüş matrisi
- Duvar: -0.5
- Yemek: +1.0
- Yılan vücudu: -1.0
- Boş alan: 0.0

## Optimizasyon
- Optimizer: Adam
- Learning Rate: 0.001
