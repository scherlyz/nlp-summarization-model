import pandas as pd
import json
import glob

# Otomatis mencari semua file yang namanya berawalan 'test.' di dalam folder indosum
file_list = glob.glob('indosum/test.*.jsonl')
file_csv = 'dataset_berita.csv'

data_list = []
print(f"🔍 Menemukan {len(file_list)} file test. Mulai memproses...")

for file_jsonl in file_list:
    print(f"Membaca {file_jsonl}...")
    with open(file_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            
            # Membongkar struktur 3 dimensi (Paragraf -> Kalimat -> Kata)
            teks_asli = " ".join([
                " ".join(kalimat) 
                for paragraf in data['paragraphs'] 
                for kalimat in paragraf
            ])
            
            # Membongkar struktur 2 dimensi (Kalimat -> Kata)
            ringkasan_pakar = " ".join([
                " ".join(kalimat) 
                for kalimat in data['summary']
            ])
            
            # Mengambil URL
            url_berita = data.get('source_url', '')
            
            data_list.append({
                'teks_asli': teks_asli,
                'ringkasan_pakar': ringkasan_pakar,
                'url': url_berita
            })

# Simpan ke CSV
df = pd.DataFrame(data_list)
df.to_csv(file_csv, index=False)
print(f"✅ Selesai! Total {len(df)} baris artikel berita berhasil digabungkan dan disimpan ke {file_csv}")