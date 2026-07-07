import pandas as pd
import time
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import re
from rouge_score import rouge_scorer
from tqdm import tqdm

# 1. PERSIAPAN DATA BAHASA
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)

# 2. FUNGSI MESIN NLP (5 Fitur Kalimat)
def proses_summarization(teks_kotor, judul_dokumen=""):
    noises = [r'SCROLL TO CONTINUE WITH CONTENT', r'Tonton juga video.*', r'Baca juga:.*', r'Halaman selanjutnya.*', r'\[Gambas:.*\]']
    for noise in noises:
        teks_kotor = re.sub(noise, '', str(teks_kotor), flags=re.IGNORECASE)
        
    teks_bersih = re.sub(r'\s+', ' ', teks_kotor).strip()
    kalimat_list = sent_tokenize(teks_bersih)
    
    if len(kalimat_list) <= 3:
        return teks_bersih
        
    stop_words = set(stopwords.words('indonesian'))
    kata_list = word_tokenize(teks_bersih.lower())
    
    frekuensi_kata = {}
    for kata in kata_list:
        if kata not in stop_words and kata.isalnum():
            frekuensi_kata[kata] = frekuensi_kata.get(kata, 0) + 1
            
    max_frekuensi = max(frekuensi_kata.values()) if frekuensi_kata else 1
    for kata in frekuensi_kata.keys():
        frekuensi_kata[kata] = frekuensi_kata[kata] / max_frekuensi

    max_panjang_kalimat = max([len(word_tokenize(k)) for k in kalimat_list]) if kalimat_list else 1
    judul_tokens = set([k.lower() for k in word_tokenize(str(judul_dokumen)) if k.isalnum() and k.lower() not in stop_words]) if judul_dokumen else set()

    skor_kalimat = []
    total_kalimat = len(kalimat_list)
    
    for indeks, kalimat in enumerate(kalimat_list):
        kata_kalimat_asli = word_tokenize(kalimat)
        kata_kalimat_lower = [k.lower() for k in kata_kalimat_asli]
        jumlah_kata = len(kata_kalimat_asli)
        
        if jumlah_kata == 0: continue

        skor_tf = sum([frekuensi_kata.get(k, 0) for k in kata_kalimat_lower]) / jumlah_kata
        skor_lokasi = (total_kalimat - indeks) / total_kalimat
        skor_panjang = jumlah_kata / max_panjang_kalimat
        
        skor_judul = 0
        if judul_tokens:
            irisan = set(kata_kalimat_lower).intersection(judul_tokens)
            skor_judul = len(irisan) / len(judul_tokens)
            
        proper_nouns = [kata for i, kata in enumerate(kata_kalimat_asli) if i > 0 and kata.istitle()]
        skor_entitas = len(proper_nouns) / jumlah_kata
        
        skor_total = skor_tf + (skor_lokasi * 1.5) + skor_panjang + skor_judul + skor_entitas
        if jumlah_kata < 6: skor_total *= 0.5
            
        skor_kalimat.append((skor_total, indeks, kalimat))
                        
    skor_kalimat.sort(key=lambda x: x[0], reverse=True)
    jumlah_kalimat_ringkasan = max(3, min(4, int(total_kalimat * 0.4)))
    kalimat_terpilih = skor_kalimat[:jumlah_kalimat_ringkasan]
    
    kalimat_terpilih.sort(key=lambda x: x[1])
    return " ".join([item[2].strip() for item in kalimat_terpilih])

# 3. FUNGSI EKSEKUSI PENGUJIAN DATASET
def evaluasi_dataset(path_csv):
    print(f"Membaca dataset dari: {path_csv}...")
    try:
        # Menyesuaikan nama kolom. Nanti bisa kamu ganti sesuai dengan nama kolom di file CSV kamu.
        df = pd.read_csv(path_csv)
    except FileNotFoundError:
        print(f"Error: File {path_csv} tidak ditemukan!")
        return

    # Validasi Kolom
    if 'teks_asli' not in df.columns or 'ringkasan_pakar' not in df.columns:
        print("Error: Dataset harus memiliki kolom 'teks_asli' dan 'ringkasan_pakar'.")
        return

    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=False)
    
    total_r1, total_r2, total_rl = 0, 0, 0
    jumlah_data = len(df)
    
    print(f"Memulai pengujian pada {jumlah_data} artikel berita...\n")
    start_time = time.time()

    # Iterasi setiap baris dengan loading bar (tqdm)
    for index, row in tqdm(df.iterrows(), total=jumlah_data, desc="Proses Evaluasi"):
        teks = str(row['teks_asli'])
        referensi = str(row['ringkasan_pakar'])
        
        # Ekstrak judul jika kolomnya ada di dataset (opsional)
        judul = str(row['judul']) if 'judul' in df.columns else ""

        # Dapatkan ringkasan dari mesin
        ringkasan_mesin = proses_summarization(teks, judul)
        
        # Hitung skor ROUGE
        scores = scorer.score(referensi, ringkasan_mesin)
        total_r1 += scores['rouge1'].fmeasure
        total_r2 += scores['rouge2'].fmeasure
        total_rl += scores['rougeL'].fmeasure

    waktu_eksekusi = round(time.time() - start_time, 2)
    
    # Kalkulasi rata-rata skor ROUGE untuk seluruh dataset
    avg_r1 = round((total_r1 / jumlah_data) * 100, 2)
    avg_r2 = round((total_r2 / jumlah_data) * 100, 2)
    avg_rl = round((total_rl / jumlah_data) * 100, 2)

    print("\n" + "="*40)
    print("🎯 HASIL EVALUASI DATASET (AVERAGE)")
    print("="*40)
    print(f"Total Data Diuji : {jumlah_data} dokumen")
    print(f"Waktu Komputasi  : {waktu_eksekusi} detik")
    print("-" * 40)
    print(f"ROUGE-1 (Unigram) : {avg_r1}%")
    print(f"ROUGE-2 (Bigram)  : {avg_r2}%")
    print(f"ROUGE-L (Struktur): {avg_rl}%")
    print("="*40)

# 4. TITIK JALAN PROGRAM
if __name__ == "__main__":
    # Ganti 'dataset_berita.csv' dengan nama file yang nanti akan kamu berikan
    FILE_DATASET = "dataset_berita.csv" 
    evaluasi_dataset(FILE_DATASET)