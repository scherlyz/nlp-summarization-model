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

# State untuk menyimpan teks utama dan judul
if 'teks_ekstraksi' not in st.session_state:
    st.session_state.teks_ekstraksi = ""
if 'judul_ekstraksi' not in st.session_state:
    st.session_state.judul_ekstraksi = ""

# ---------------------------------------------------------
# 2. MESIN NLP (Berdasarkan Paper Badrus Zaman, 2011)
# ---------------------------------------------------------
def proses_summarization(teks_kotor, judul_dokumen=""):
    start_time = time.time()
    
    # PEMBERSIHAN NOISE (Sama seperti sebelumnya)
    noises = [
        r'SCROLL TO CONTINUE WITH CONTENT',
        r'Tonton juga video.*',
        r'Baca juga:.*',
        r'Halaman selanjutnya.*',
        r'\[Gambas:.*\]'
    ]
    for noise in noises:
        teks_kotor = re.sub(noise, '', teks_kotor, flags=re.IGNORECASE)
        
    teks_bersih = re.sub(r'\s+', ' ', teks_kotor).strip()
    kalimat_list = sent_tokenize(teks_bersih)
    
    if len(kalimat_list) <= 3:
        return teks_bersih, len(teks_kotor), len(teks_bersih), round(time.time() - start_time, 2)
        
    # PERSIAPAN FITUR (Tokenisasi & Stopwords)
    stop_words = set(stopwords.words('indonesian'))
    kata_list = word_tokenize(teks_bersih.lower())
    
    # Fitur 1: Hitung max TF
    frekuensi_kata = {}
    for kata in kata_list:
        if kata not in stop_words and kata.isalnum():
            frekuensi_kata[kata] = frekuensi_kata.get(kata, 0) + 1
            
    max_frekuensi = max(frekuensi_kata.values()) if frekuensi_kata else 1
    for kata in frekuensi_kata.keys():
        frekuensi_kata[kata] = frekuensi_kata[kata] / max_frekuensi

    # Fitur 3: Cari kalimat terpanjang untuk Panjang Relatif
    max_panjang_kalimat = max([len(word_tokenize(k)) for k in kalimat_list]) if kalimat_list else 1
    
    # Fitur 4: Tokenisasi judul untuk Kemiripan Judul
    judul_tokens = set([k.lower() for k in word_tokenize(judul_dokumen) if k.isalnum() and k.lower() not in stop_words]) if judul_dokumen else set()

    # MENGHITUNG 5 FITUR UNTUK SETIAP KALIMAT
    skor_kalimat = []
    total_kalimat = len(kalimat_list)
    
    for indeks, kalimat in enumerate(kalimat_list):
        kata_kalimat_asli = word_tokenize(kalimat)
        kata_kalimat_lower = [k.lower() for k in kata_kalimat_asli]
        jumlah_kata = len(kata_kalimat_asli)
        
        if jumlah_kata == 0:
            continue

        # Fitur 1: Term Frequency (TF)
        skor_tf = sum([frekuensi_kata.get(k, 0) for k in kata_kalimat_lower]) / jumlah_kata
        
        # Fitur 2: Letak Kalimat (Makin awal letaknya, nilainya mendekati 1)
        skor_lokasi = (total_kalimat - indeks) / total_kalimat
        
        # Fitur 3: Panjang Relatif Kalimat
        skor_panjang = jumlah_kata / max_panjang_kalimat
        
        # Fitur 4: Kemiripan dengan Judul (Irisan kata kalimat dengan kata judul)
        skor_judul = 0
        if judul_tokens:
            irisan = set(kata_kalimat_lower).intersection(judul_tokens)
            skor_judul = len(irisan) / len(judul_tokens)
            
        # Fitur 5: Kata Nama Diri / Proper Noun (Huruf kapital selain di awal kalimat)
        proper_nouns = [kata for i, kata in enumerate(kata_kalimat_asli) if i > 0 and kata.istitle()]
        skor_entitas = len(proper_nouns) / jumlah_kata
        
        # Total Skor (Kombinasi linear dari 5 fitur)
        # Penambahan bobot kali 1.5 untuk lokasi karena sangat krusial di teks berita
        skor_total = skor_tf + (skor_lokasi * 1.5) + skor_panjang + skor_judul + skor_entitas
        
        # Penalti untuk kalimat yang terlalu pendek (sisa noise)
        if jumlah_kata < 6:
            skor_total *= 0.5
            
        skor_kalimat.append((skor_total, indeks, kalimat))
                        
    # EKSTRAKSI POIN-POIN
    skor_kalimat.sort(key=lambda x: x[0], reverse=True)
    jumlah_kalimat_ringkasan = max(3, min(4, int(total_kalimat * 0.4)))
    kalimat_terpilih = skor_kalimat[:jumlah_kalimat_ringkasan]
    
    # Urutkan kembali berdasarkan indeks asli agar narasi kronologis
    kalimat_terpilih.sort(key=lambda x: x[1])
    
    ringkasan_final = [f"• {item[2].strip()}" for item in kalimat_terpilih]
    ringkasan = "\n\n".join(ringkasan_final)
    
    end_time = time.time()
    return ringkasan, len(teks_kotor), len(ringkasan), round((end_time - start_time), 2)

# ---------------------------------------------------------
# 3. ANTARMUKA WEB
# ---------------------------------------------------------
st.title("Sintesa: Sistem Peringkas Teks")
st.write("Mengekstrak ringkasan berita secara otomatis menggunakan metode NLP berbasis fitur kalimat.")

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
                        st.session_state.judul_ekstraksi = artikel.title # Ambil Judul Web
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
            st.session_state.judul_ekstraksi = uploaded_file.name # Gunakan nama file sbg judul
            st.success("File berhasil diekstrak! Klik Ekstrak Summarization di bawah.")

# --- TAB 3: INPUT TEKS MANUAL ---
with tab3:
    judul_manual = st.text_input("Judul Teks (Opsional):")
    teks_manual = st.text_area("Tempel teks berita di sini:", height=250)
    if teks_manual:
        st.session_state.teks_ekstraksi = teks_manual
        st.session_state.judul_ekstraksi = judul_manual

# ---------------------------------------------------------
# 4. EKSEKUSI & HASIL
# ---------------------------------------------------------
st.markdown("---")
if st.button("⚡ Ekstrak Summarization", use_container_width=True):
    if not st.session_state.teks_ekstraksi.strip():
        st.warning("Teks masih kosong. Silakan masukkan data terlebih dahulu.")
    else:
        with st.spinner('Menganalisis 5 Fitur Kalimat...'):
            # Memasukkan Teks DAN Judul ke dalam fungsi
            ringkasan, len_awal, len_akhir, waktu = proses_summarization(
                st.session_state.teks_ekstraksi, 
                st.session_state.judul_ekstraksi
            )
            
            st.subheader("📝 Summarization:")
            st.info(ringkasan) 
            
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            col1.metric(label="Panjang Asli", value=f"{len_awal} kar")
            col2.metric(label="Panjang Ringkasan", value=f"{len_akhir} kar")
            col3.metric(label="Waktu Proses", value=f"{waktu} dtk")