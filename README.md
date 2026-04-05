# 🤖 3D Model Generator AI Agent

Tek bir görselden STL 3D baskı dosyası üreten Python masaüstü yapay zeka uygulaması.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/hibrahimisik/3D-Model-Generator/blob/main/colab_app.ipynb)

| Bileşen | Teknoloji |
|---------|-----------|
| **Masaüstü Arayüz** | PyQt6 (koyu tema) |
| **Colab Arayüzü** | Gradio |
| **LLM** | Groq API — `llama-3.3-70b-versatile` + `llama-3.2-11b-vision-preview` |
| **Görsel → 3D** | [TRELLIS](https://github.com/microsoft/TRELLIS) (Microsoft) |

---

## 🚀 Google Colab ile Çalıştır (Önerilen)

TRELLIS **NVIDIA CUDA GPU** gerektirir. Ücretsiz GPU için Google Colab kullanın:

### Hızlı Başlangıç
1. Yukarıdaki **"Open in Colab"** rozetine tıklayın
2. `Çalışma Zamanı → Çalışma zamanı türünü değiştir → T4 GPU` seçin
3. Hücreleri sırasıyla çalıştırın
4. Kurulum bittikten sonra runtime'ı yeniden başlatın
5. Gradio arayüzü açılır — public link ile paylaşabilirsiniz

### Adım Adım
| Hücre | İşlem | Süre |
|-------|-------|------|
| Adım 1 | GPU kontrolü | ~5 sn |
| Adım 2 | Bağımlılık kurulumu + **runtime restart** | ~5-10 dk |
| Adım 3 | Proje setup + GitHub'dan klonla | ~1 dk |
| Adım 4 | TRELLIS modeli yükle (~2 GB) | ~3-5 dk |
| Adım 5 | Groq API anahtarı (isteğe bağlı) | ~5 sn |
| Adım 6 | Gradio uygulamasını başlat | ~10 sn |

## 🖥️ Ekran Görüntüsü

```
┌─────────────────────────────────────────────────────────┐
│  🤖 3D Model Generator        ⚙️ Ayarlar  🗑 Sıfırla   │
├────────────────────────┬────────────────────────────────┤
│  💬 SOHBET             │  🖼️ GÖRSEL & 3D DÖNÜŞTÜRME     │
│                        │                                │
│  🤖 Asistan:           │  ┌──────────────────────────┐  │
│  Merhaba! Görselinizi  │  │                          │  │
│  yükleyin...           │  │    [Görsel Önizleme]     │  │
│                        │  │                          │  │
│  Sen 🖼️:               │  └──────────────────────────┘  │
│  Bu nesneyi analiz et  │                                │
│                        │  🔄 STL'e Dönüştür             │
│  🤖 Asistan:           │  ████████████░░░  75%          │
│  Görsel bir kupa...    │  Mesh çıkarılıyor...           │
│                        │                                │
│  [Mesaj yazın...    ]  │  ⬇️ STL Dosyasını İndir        │
│  📎 Görsel Yükle  ➤   │                                │
└────────────────────────┴────────────────────────────────┘
```

---

## 🚀 Kurulum

### 1. Depoyu klonlayın
```bash
git clone <repo-url>
cd 3D-Model-Generator
```

### 2. Otomatik kurulum (önerilen)
```bash
chmod +x setup.sh
./setup.sh
```

### 3. Manuel kurulum
```bash
# Sanal ortam oluştur
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Bağımlılıkları kur
pip install -r requirements.txt

# TripoSR kur
pip install git+https://github.com/VAST-AI-Research/TripoSR.git
```

---

## 🔑 Groq API Anahtarı

Uygulama **Groq API**'sini kullanmaktadır. Groq'un ücretsiz katmanı oldukça cömert limitler sunmaktadır.

1. [https://console.groq.com/](https://console.groq.com/) adresine gidin
2. Ücretsiz hesap oluşturun
3. **API Keys** sekmesinden yeni anahtar üretin (`gsk_...`)
4. Uygulamada ⚙️ **Ayarlar → API Anahtarı** alanına yapıştırın

> **Not:** Görsel → STL dönüştürme işlemi API anahtarı **gerektirmez**. TripoSR tamamen yerel çalışır.

---

## 🎯 Kullanım

```bash
# Uygulamayı başlat
python main.py
```

### Adım adım:
1. ⚙️ **Ayarlar**'dan Groq API anahtarınızı girin
2. **📎 Görsel Yükle** ile bir fotoğraf seçin (PNG, JPG, WEBP...)
3. Asistan görseli otomatik olarak analiz eder
4. **🔄 STL'e Dönüştür** düğmesine tıklayın
5. Dönüştürme tamamlanınca **⬇️ STL Dosyasını İndir** ile dosyayı kaydedin
6. STL dosyasını **Cura**, **PrusaSlicer** veya **Meshmixer** ile açın

---

## 🧩 Proje Yapısı

```
3D-Model-Generator/
├── main.py                  # Uygulama giriş noktası
├── requirements.txt         # Python bağımlılıkları
├── setup.sh                 # Otomatik kurulum scripti
├── config.json              # Kullanıcı ayarları (otomatik oluşturulur)
│
├── ui/
│   ├── main_window.py       # Ana PyQt6 penceresi
│   ├── settings_dialog.py   # Ayarlar diyalogu
│   └── styles.py            # Koyu tema CSS
│
├── agent/
│   └── llm_agent.py         # Groq LLM entegrasyonu
│
├── converter/
│   └── image_to_stl.py      # TripoSR dönüştürücü
│
├── utils/
│   └── config_manager.py    # Konfigürasyon yönetimi
│
├── uploads/                 # Yüklenen görseller
└── output/                  # Üretilen STL dosyaları
```

---

## ⚙️ Desteklenen Modeller

### Metin Modelleri (Groq)
| Model | Açıklama |
|-------|----------|
| `llama-3.3-70b-versatile` | ⭐ Önerilen — Yüksek kaliteli |
| `mixtral-8x7b-32768` | Geniş bağlam penceresi |
| `gemma2-9b-it` | Hızlı ve hafif |

### Görsel Modelleri (Groq Vision)
| Model | Açıklama |
|-------|----------|
| `llama-3.2-11b-vision-preview` | ⭐ Önerilen — Dengeli |
| `llama-3.2-90b-vision-preview` | Yüksek kalite (yavaş) |

---

## 🔧 TripoSR Hakkında

[TripoSR](https://github.com/VAST-AI-Research/TripoSR), Stability AI ve Tripo AI tarafından geliştirilen açık kaynaklı tek görsel → 3D model dönüştürücüsüdür.

- **Model:** `stabilityai/TripoSR` (HuggingFace Hub)
- **Boyut:** ~1.5 GB (ilk kullanımda otomatik indirilir)
- **GPU:** Destekleniyor (CUDA), CPU'da da çalışır (yavaş)
- **Çıktı:** STL, OBJ, GLB

### Mesh Çözünürlüğü
| Değer | Kalite | Süre (CPU) |
|-------|--------|------------|
| 128 | Düşük/Hızlı | ~2-3 dk |
| 256 | Orta ⭐ | ~5-8 dk |
| 512 | Yüksek | ~15-20 dk |

---

## 📋 Sistem Gereksinimleri

| Bileşen | Minimum | Önerilen |
|---------|---------|----------|
| Python | 3.9+ | 3.11+ |
| RAM | 8 GB | 16 GB |
| Depolama | 5 GB | 10 GB |
| GPU | Yok | NVIDIA CUDA |
| İşletim Sistemi | Windows/macOS/Linux | - |

---

## 🐛 Sorun Giderme

### TripoSR kurulumunda hata
```bash
pip install --upgrade pip setuptools wheel
pip install git+https://github.com/VAST-AI-Research/TripoSR.git --no-build-isolation
```

### CUDA bellek hatası
Ayarlar'dan **Mesh Çözünürlüğü**'nü 128 veya 64'e düşürün.

### API 401 hatası
Groq API anahtarınızın geçerli olduğunu kontrol edin.

### macOS'ta PyQt6 sorunu
```bash
pip install --upgrade PyQt6 PyQt6-Qt6 PyQt6-sip
```

---

## 📄 Lisans

MIT License — Özgürce kullanın, değiştirin ve dağıtın.

