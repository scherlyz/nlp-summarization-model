# Sintesa: Sistem Peringkas Teks Berbasis NLP

Sintesa adalah aplikasi web interaktif berbasis **Natural Language Processing (NLP)** yang dirancang untuk merangkum artikel berita, dokumen, atau teks panjang menjadi poin-poin intisari (*Key Takeaways*). Aplikasi ini menggunakan pendekatan **Smart Extractive Summarization** yang dimodifikasi dengan aturan jurnalistik (Piramida Terbalik) untuk menghasilkan ringkasan yang padat, akurat, dan minim *noise*.

## ✨ Fitur Utama

- **🔗 Tarik Berita Otomatis (Web Scraping):** Ekstrak teks utama dari URL portal berita secara instan tanpa mengikutkan iklan atau menu navigasi.
- **📄 Dukungan Unggah File:** Mendukung ekstraksi teks dari dokumen berformat `.pdf` dan `.txt`.
- **✍️ Input Teks Manual:** Tempel (*copy-paste*) teks langsung ke dalam aplikasi.
- **🧠 Smart NLP Engine:**
  - **Advanced Cleaning:** Filter otomatis untuk membuang *noise* khas portal berita (seperti "SCROLL TO CONTINUE WITH CONTENT", dll).
  - **Position Weighting:** Memprioritaskan kalimat di awal paragraf utama (Piramida Terbalik) untuk menjaga konteks berita (Siapa, Apa, Kapan).
  - **Length Penalty:** Normalisasi skor untuk menghindari pemilihan kalimat yang sekadar panjang namun bertele-tele.
- **📱 UI Responsif:** Antarmuka web yang dibangun dengan Streamlit, mendukung mode Terang/Gelap (*Light/Dark Mode*) secara otomatis.

## 🛠️ Teknologi yang Digunakan

- **Bahasa Pemrograman:** Python 3.x
- **Frontend / Framework Web:** [Streamlit](https://streamlit.io/)
- **Pemrosesan NLP:** [NLTK](https://www.nltk.org/) (Natural Language Toolkit)
- **Ekstraksi Artikel Web:** `newspaper3k` & `lxml_html_clean`
- **Ekstraksi PDF:** `pdfplumber`

## 🚀 Cara Instalasi dan Menjalankan Aplikasi

Ikuti langkah-langkah berikut untuk menjalankan Sintesa di komputer lokal Anda:

### 1. Persiapan Direktori
Pastikan semua file proyek (seperti `app.py`) berada di dalam satu folder. Buka terminal atau *command prompt* dan arahkan ke folder tersebut.

### 2. Instalasi Dependensi (Library)
Jalankan perintah berikut di terminal untuk menginstal semua pustaka yang dibutuhkan:
```bash
pip install streamlit pdfplumber newspaper3k lxml_html_clean nltk
