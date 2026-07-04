import streamlit as st
import pdfplumber
import time
from newspaper import Article
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import re

# ---------------------------------------------------------
# 0. DOWNLOAD DATA BAHASA
# ---------------------------------------------------------
@st.cache_resource
def download_nltk_data():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')

download_nltk_data()

# ---------------------------------------------------------
# 1. KUSTOMISASI UI/UX
# ---------------------------------------------------------
st.set_page_config(page_title="Sintesa - NLP Summarizer", layout="centered", page_icon="🌿")

custom_css = """
<style>
    .stTextArea textarea { font-size: 16px !important; line-height: 1.5 !important; }
    .stAlert { font-size: 16px !important; line-height: 1.6 !important; }
    .stMarkdown p { font-size: 16px; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

if 'teks_ekstraksi' not in st.session_state:
    st.session_state.teks_ekstraksi = ""

# ---------------------------------------------------------
# 2. MESIN NLP (Diperbarui dengan Aturan Jurnalistik & Filter Noise)
# ---------------------------------------------------------
def proses_summarization(teks_kotor):
    start_time = time.time()
    
    # 1. PEMBERSIHAN NOISE PORTAL BERITA
    # Menghapus teks sampah yang sering menempel saat scraping
    noises = [
        r'SCROLL TO CONTINUE WITH CONTENT',
        r'Tonton juga video.*',
        r'Baca juga:.*',
        r'Halaman selanjutnya.*',
        r'\[Gambas:.*\]'
    ]
    for noise in noises:
        teks_kotor = re.sub(noise, '', teks_kotor, flags=re.IGNORECASE)
        
    # Membersihkan spasi berlebih
    teks_bersih = re.sub(r'\s+', ' ', teks_kotor).strip()
    kalimat_list = sent_tokenize(teks_bersih)
    
    if len(kalimat_list) <= 3:
        return teks_bersih, len(teks_kotor), len(teks_bersih), round(time.time() - start_time, 2)
        
    # 2. MENGHITUNG BOBOT KATA (Term Frequency)
    stop_words = set(stopwords.words('indonesian'))
    kata_list = word_tokenize(teks_bersih.lower())
    
    frekuensi_kata = {}
    for kata in kata_list:
        if kata not in stop_words and kata.isalnum():
            frekuensi_kata[kata] = frekuensi_kata.get(kata, 0) + 1
                
    max_frekuensi = max(frekuensi_kata.values()) if frekuensi_kata else 1
    for kata in frekuensi_kata.keys():
        frekuensi_kata[kata] = frekuensi_kata[kata] / max_frekuensi
        
    # 3. MENGHITUNG SKOR KALIMAT CERDAS (Piramida Terbalik)
    skor_kalimat = []
    for indeks, kalimat in enumerate(kalimat_list):
        skor = 0
        kata_kalimat = word_tokenize(kalimat.lower())
        jumlah_kata = len(kata_kalimat)
        
        for kata in kata_kalimat:
            if kata in frekuensi_kata:
                skor += frekuensi_kata[kata]
        
        # A. Normalisasi Skor (Bagi skor dengan jumlah kata)
        # Agar kalimat yang sekadar "panjang" tidak otomatis mengalahkan kalimat pendek yang berbobot
        if jumlah_kata > 0:
            skor = skor / jumlah_kata
            
        # B. Bobot Posisi (Sangat Penting untuk Berita)
        # Kalimat ke-1 dan ke-2 di berita biasanya adalah inti (Lead). Kita beri bonus besar!
        if indeks == 0:
            skor += 2.0
        elif indeks == 1:
            skor += 1.0
            
        # C. Penalti Kalimat
        # Kurangi skor kalimat yang terlalu pendek (biasanya sisa noise) atau terlalu panjang (bertele-tele)
        if jumlah_kata < 6 or jumlah_kata > 40:
            skor *= 0.5
            
        skor_kalimat.append((skor, indeks, kalimat))
                        
    # 4. EKSTRAKSI POIN-POIN
    # Urutkan berdasarkan skor tertinggi untuk mencari kalimat paling relevan
    skor_kalimat.sort(key=lambda x: x[0], reverse=True)
    
    # Ambil maksimal 4 kalimat terbaik, atau 40% dari total artikel
    jumlah_kalimat_ringkasan = max(3, min(4, int(len(kalimat_list) * 0.4)))
    kalimat_terpilih = skor_kalimat[:jumlah_kalimat_ringkasan]
    
    # Urutkan kembali berdasarkan indeks asli agar alur ceritanya logis dan tidak melompat
    kalimat_terpilih.sort(key=lambda x: x[1])
    
    # Bentuk menjadi poin-poin (bullet points)
    ringkasan_final = [f"• {item[2].strip()}" for item in kalimat_terpilih]
    ringkasan = "\n\n".join(ringkasan_final)
    
    end_time = time.time()
    return ringkasan, len(teks_kotor), len(ringkasan), round((end_time - start_time), 2)

# ---------------------------------------------------------
# 3. ANTARMUKA WEB
# ---------------------------------------------------------
st.title("Sintesa: Sistem Peringkas Teks")
st.write("Sistem otomatis akan mengekstrak ringkasan dari teks Anda.")

tab1, tab2, tab3 = st.tabs(["🔗 Link Berita", "📄 Unggah File", "✍️ Input Teks"])

# --- TAB 1: SCRAPING DARI URL ---
with tab1:
    url_berita = st.text_input("Masukkan URL artikel berita:")
    if st.button("Tarik Teks Berita"):
        if url_berita:
            with st.spinner("Menyedot artikel dari website..."):
                try:
                    artikel = Article(url_berita, language='id')
                    artikel.download()
                    artikel.parse()
                    if artikel.text:
                        st.session_state.teks_ekstraksi = artikel.text
                        st.success(f"Berhasil menarik artikel: **{artikel.title}**")
                        st.text_area("Pratinjau Teks Asli:", st.session_state.teks_ekstraksi, height=200)
                    else:
                        st.error("Teks tidak ditemukan di tautan tersebut.")
                except Exception as e:
                    st.error(f"Gagal menarik berita. Error: {e}")

# --- TAB 2: UPLOAD FILE ---
with tab2:
    uploaded_file = st.file_uploader("Pilih file (.txt atau .pdf)", type=['txt', 'pdf'])
    if uploaded_file is not None:
        teks_sementara = ""
        if uploaded_file.name.endswith(".pdf"):
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    ekstrak = page.extract_text()
                    if ekstrak:
                        teks_sementara += ekstrak + "\n"
        elif uploaded_file.name.endswith(".txt"):
            teks_sementara = uploaded_file.getvalue().decode("utf-8")
            
        if teks_sementara:
            st.session_state.teks_ekstraksi = teks_sementara
            st.success("File berhasil diekstrak! Klik Ringkas Teks di bawah.")

# --- TAB 3: INPUT TEKS MANUAL ---
with tab3:
    teks_manual = st.text_area("Tempel teks berita di sini:", height=250)
    if teks_manual:
        st.session_state.teks_ekstraksi = teks_manual

# ---------------------------------------------------------
# 4. EKSEKUSI & HASIL
# ---------------------------------------------------------
st.markdown("---")
if st.button("⚡ Ekstrak Summarization", use_container_width=True):
    if not st.session_state.teks_ekstraksi.strip():
        st.warning("Teks masih kosong. Silakan masukkan data terlebih dahulu.")
    else:
        with st.spinner('Menganalisis dan menyusun intisari bacaan...'):
            ringkasan, len_awal, len_akhir, waktu = proses_summarization(st.session_state.teks_ekstraksi)
            
            st.subheader("📝 Summarization:")
            st.info(ringkasan) 
            
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            col1.metric(label="Panjang Asli", value=f"{len_awal} kar")
            col2.metric(label="Panjang Ringkasan", value=f"{len_akhir} kar")
            col3.metric(label="Waktu Proses", value=f"{waktu} dtk")