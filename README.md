# Audio Splitter

Aplikasi lokal untuk memotong file audio (`.m4a`, `.mp3`, `.wav`, `.aac`, `.ogg`, `.flac`, `.opus`, `.wma`, `.m4b`, `.aiff`) menjadi beberapa bagian dengan durasi tetap (10, 20, atau 30 menit). Tersedia versi browser (Streamlit) dan versi desktop (CustomTkinter). Pemrosesan memakai `ffmpeg` dengan `-c copy` sehingga cepat dan tanpa re-encode.

## Yang perlu disiapkan

1. Python 3.10 atau lebih baru.
2. `ffmpeg` sudah terpasang dan bisa dipanggil dari terminal.
3. Koneksi internet hanya dibutuhkan saat instalasi dependensi Python, bukan saat memotong audio.

Cek `ffmpeg` di terminal:

```bash
ffmpeg -version
```

Jika perintah di atas gagal, pasang `ffmpeg` terlebih dahulu. Di macOS:

```bash
brew install ffmpeg
```

## Instalasi (sekali saja)

1. Buka terminal.
2. Masuk ke folder proyek ini:

```bash
cd /Users/mohamadarifmujaki/Development/Audio-Spiltter
```

3. Buat dan aktifkan virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

4. Pasang dependensi aplikasi:

```bash
pip install -r requirements.txt
```

Setelah langkah ini, setiap kali membuka terminal baru, aktifkan lagi virtual environment dengan:

```bash
cd /Users/mohamadarifmujaki/Development/Audio-Spiltter
source .venv/bin/activate
```

## Menjalankan versi web (browser)

1. Pastikan virtual environment aktif (`source .venv/bin/activate`).
2. Jalankan aplikasi web dengan perintah ini:

```bash
streamlit run app.py
```

3. Buka alamat yang muncul di terminal, biasanya `http://localhost:8501`.
4. Di browser:
   - Unggah file audio.
   - Pilih durasi potongan: 10, 20, atau 30 menit.
   - Klik **Pilih folder…** untuk memilih folder output.
   - Klik **Potong audio**.
5. Hasil disimpan di subfolder bernama file di dalam folder output yang dipilih. Contoh: folder output `Hasil` dan file `Podcast.m4a` menghasilkan `Hasil/Podcast/Podcast_1.m4a`, `Podcast_2.m4a`, dan seterusnya.
6. Unduh tiap potongan lewat tombol unduh di halaman, atau buka langsung folder hasil di komputer Anda.
7. Untuk menghentikan server web, kembali ke terminal lalu tekan `Ctrl+C`.

Catatan penting:

- Jalankan `app.py`, bukan `splitter.py`.
- Jika halaman kosong atau hitam, hentikan server lalu jalankan ulang `streamlit run app.py`.
- Versi web memakai dialog folder sistem (bukan dialog di dalam browser). Jika dialog tidak terlihat, cek jendela lain dengan `Cmd+Tab`.
- Jika dialog folder membuat Python berhenti mendadak, muat ulang halaman setelah memperbarui kode aplikasi.

## Menjalankan versi desktop

1. Pastikan virtual environment aktif (`source .venv/bin/activate`).
2. Jalankan aplikasi desktop:

```bash
python desktop_app.py
```

3. Di jendela aplikasi:
   - Klik **Pilih file…** untuk memilih file audio.
   - Pilih durasi potongan: 10, 20, atau 30 menit.
   - Klik **Pilih folder…** untuk memilih folder output.
   - Klik **Potong audio**.
4. Hasil disimpan dengan pola folder yang sama seperti versi web: subfolder bernama file di dalam folder output yang dipilih.
5. Daftar path hasil muncul di bagian bawah jendela aplikasi.
6. Tutup jendela aplikasi untuk menghentikan program.

Jika muncul pesan bahwa Tkinter tidak tersedia, pasang dukungan Tkinter untuk versi Python Anda. Di macOS dengan Homebrew, contohnya:

```bash
brew install python-tk@3.14
```

Sesuaikan versi Python jika berbeda.

## Deploy ke Streamlit Community Cloud

1. Pastikan file `packages.txt` ada di root repositori dan berisi baris `ffmpeg`.
2. Pastikan `requirements.txt` ikut ter-commit.
3. Deploy ulang aplikasi setelah perubahan dependensi dipush ke repositori.
4. Di pengaturan deploy, pilih `app.py` sebagai entry point.

Server cloud tidak memakai `ffmpeg` dari komputer lokal Anda. `ffmpeg` harus dipasang di lingkungan server lewat `packages.txt`.

Di deploy cloud, dialog folder lokal tidak tersedia. Isi path folder output di server, atau biarkan nilai baku `.work/output`.

## Privasi

File yang diunggah dan hasil potongan hanya disimpan di mesin Anda. Tidak ada unggahan ke layanan cloud; aplikasi dijalankan sepenuhnya di komputer lokal.

## Catatan teknis

Dengan `-c copy`, titik potong mengikuti batas frame/keyframe. Durasi setiap segmen bisa sedikit menyimpang dari kelipatan menit yang dipilih. Segmen terakhir bisa lebih pendek dari durasi yang dipilih.
