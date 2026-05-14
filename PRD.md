# PRD — Pemotong Audio (Audio Splitter)

Dokumen ini merangkum kebutuhan produk berdasarkan perilaku aplikasi yang sudah ada di codebase. Bahasa sengaja dibuat jelas agar tim produk, desain, dan engineering punya acuan yang sama.

## 1. Ringkasan produk

Pemotong Audio adalah aplikasi untuk memecah satu file audio panjang menjadi beberapa file berdurasi tetap (10, 20, atau 30 menit). Hasil akhir disimpan di folder lokal yang dipilih pengguna, dengan penamaan berurutan mulai dari `_1`.

Produk tersedia dalam dua bentuk:

- **Versi web** berbasis Streamlit (`app.py`)
- **Versi desktop** berbasis CustomTkinter (`desktop_app.py`)

Keduanya memakai mesin pemotongan yang sama (`splitter.py`) dan `ffmpeg`.

## 2. Masalah yang diselesaikan

Pengguna sering punya rekaman panjang (podcast, kuliah, audiobook, musik) yang sulit diputar atau diatur sekaligus. Mereka butuh cara cepat memecah file tanpa mengedit manual di DAW, tanpa bergantung pada layanan cloud yang menyimpan file secara permanen.

## 3. Tujuan produk

- Memotong audio dengan durasi potongan yang dapat diprediksi.
- Menyimpan hasil ke folder lokal pengguna, bukan ke repositori cloud permanen.
- Menjaga proses tetap sederhana: pilih file, pilih durasi, pilih folder, proses.
- Mendukung banyak format audio umum.
- Menyediakan opsi mempertahankan format asal (lebih cepat) atau mengonversi ke MP3.

## 4. Non-tujuan (di luar cakupan saat ini)

- Akun pengguna, login, atau penyimpanan riwayat di server.
- Kolaborasi multi-pengguna atau berbagi file lewat link.
- Edit audio lanjutan (fade, normalisasi, metadata tagging, dsb.).
- Pemotongan berbasis silence detection atau marker manual.
- Durasi potongan kustom di luar 10/20/30 menit.
- Hosting file hasil di server untuk diunduh ulang dari aplikasi.

## 5. Pengguna target

- **Pengguna lokal** yang menjalankan aplikasi di komputer sendiri (web localhost atau desktop).
- **Pengguna cloud web** yang mengakses deploy Streamlit Community Cloud, tetapi tetap menyimpan hasil ke folder lokal lewat browser Chromium.
- Pengguna yang nyaman memilih folder output sendiri dan ingin kontrol atas lokasi file.

## 6. Platform dan jalur distribusi

| Platform | Entry point | Pemilihan folder output |
| --- | --- | --- |
| Web lokal | `streamlit run app.py` | Dialog sistem (macOS/Windows/Linux) bila tersedia |
| Web cloud | Deploy Streamlit + `packages.txt` (`ffmpeg`) | Komponen browser CCv2 + File System Access API |
| Desktop | `python desktop_app.py` | Dialog file/folder native (Tkinter + fallback OS) |

## 7. Kebutuhan fungsional

### 7.1 Input audio

- Pengguna memilih satu file audio per proses.
- Format yang diterima: `.m4a`, `.mp3`, `.wav`, `.aac`, `.ogg`, `.flac`, `.opus`, `.wma`, `.m4b`, `.aiff`, `.aif`.
- File kosong atau format tidak didukung ditolak dengan pesan error yang jelas.
- Versi web menerima unggahan lewat `st.file_uploader`.

### 7.2 Konfigurasi pemotongan

- Durasi tiap potongan: **10**, **20**, atau **30 menit**.
- Format hasil:
  - **Pertahankan format asal** — memakai mode salin stream (`-c copy`) bila memungkinkan.
  - **Konversi ke MP3** — re-encode dengan `libmp3lame` bila sumber bukan MP3.

### 7.3 Pemrosesan

- Pemotongan dilakukan oleh `ffmpeg` lewat `split_audio()`.
- Aplikasi menolak berjalan bila `ffmpeg` tidak tersedia.
- Pada cloud, ketersediaan `ffmpeg` bergantung pada `packages.txt` dan/atau fallback `imageio-ffmpeg`.

### 7.4 Output dan penamaan

- Hasil disimpan di subfolder bernama stem file input di dalam folder output yang dipilih.
- Contoh: input `Podcast.m4a`, folder output `Hasil` → `Hasil/Podcast/Podcast_1.m4a`, `Podcast_2.m4a`, dan seterusnya.
- Penomoran potongan dimulai dari **1**, bukan 0.
- Jika file output pertama sudah ada, proses dihentikan agar tidak menimpa data.

### 7.5 Pemilihan folder output

**Web — dialog native (server mendukung dialog OS):**

- Pengguna memilih folder lewat dialog sistem.
- Hasil ditulis langsung ke folder tersebut.

**Web — mode browser (deploy cloud / tanpa dialog native):**

- Pengguna memilih folder lokal lewat tombol komponen browser.
- Aplikasi menyimpan nama folder di state UI; path lengkap tidak ditampilkan karena batasan browser.
- Hasil diproses sementara di server, lalu dikirim ke folder lokal pengguna lewat API browser.

**Desktop:**

- Pengguna memilih file input dan folder output lewat dialog desktop.
- Tidak ada unggahan ke server; pemrosesan sepenuhnya lokal.

### 7.6 Umpan balik ke pengguna

- Saat memproses: indikator “Memproses audio…”.
- Setelah sukses (web): ringkasan di bawah tombol **Potong audio** (jumlah file, durasi, format, lokasi relatif).
- Setelah sukses (desktop): ringkasan di label status bawah.
- Setelah sukses (web): widget unggah direset agar input kosong.
- Error validasi dan kegagalan `ffmpeg` ditampilkan tanpa pesan sukses palsu.

### 7.7 SEO web (hanya metadata)

- Teks SEO tidak ditampilkan sebagai blok konten utama di UI.
- Meta tag (description, keywords, Open Graph, Twitter Card) disisipkan ke `<head>` lewat komponen CCv2 (`web_seo.py`).
- Judul tab browser memakai judul halaman SEO.

### 7.8 Kebersihan data sementara di server (web)

- Unggahan web disimpan sementara di `.work/uploads/`.
- Hasil staging mode browser disimpan sementara di `.work/output/`.
- Setelah hasil berhasil ada di folder lokal pengguna, file input dan staging server dihapus (`cleanup_server_staging()`).
- File lama di `.work/` juga dibersihkan berdasarkan umur saat aplikasi dibuka (`cleanup_work_dirs()`).

## 8. Alur pengguna utama

### 8.1 Web

1. Buka aplikasi web.
2. Unggah file audio.
3. Pilih durasi potongan dan format hasil.
4. Pilih folder output.
5. Klik **Potong audio**.
6. Baca ringkasan sukses; cek file di folder lokal.
7. Unggahan form kosong kembali.

### 8.2 Desktop

1. Buka aplikasi desktop.
2. Pilih file audio.
3. Pilih durasi dan format hasil.
4. Pilih folder output.
5. Klik **Potong audio**.
6. Baca status hasil di bagian bawah jendela.

## 9. Aturan bisnis dan validasi

- Wajib ada file input sebelum memproses.
- Wajib ada folder output sebelum memproses.
- Durasi potongan hanya boleh 10, 20, atau 30 menit.
- Folder output harus dapat ditulis.
- File input tidak boleh kosong.
- Konflik nama output (file `_1` sudah ada) menghentikan proses.
- Mode browser folder membutuhkan browser berbasis Chromium untuk pemilihan folder lokal.

## 10. Perilaku teknis yang perlu dipahami pengguna

- Dengan format asal (`-c copy`), titik potong bisa sedikit menyimpang dari durasi target karena batas frame/keyframe.
- Segmen terakhir bisa lebih pendek dari durasi yang dipilih.
- Konversi ke MP3 lebih lambat daripada mempertahankan format asal.
- Pada deploy cloud, file akan melalui disk server sementara selama proses, meskipun tidak disimpan sebagai arsip permanen.

## 11. Privasi dan keamanan data

- Tidak ada modul autentikasi atau database pengguna.
- Tidak ada upload ke layanan pihak ketiga khusus penyimpanan file.
- Hasil akhir berada di folder lokal pengguna.
- Folder `.work/` diabaikan dari git (`.gitignore`) dan dibersihkan otomatis.
- Komponen folder browser memakai IndexedDB untuk mengingat izin folder di sisi klien.

## 12. Arsitektur produk (ringkas)

| Modul | Peran |
| --- | --- |
| `app.py` | UI web Streamlit dan orkestrasi alur |
| `desktop_app.py` | UI desktop |
| `desktop_controller.py` | Logika pemotongan di thread worker desktop |
| `splitter.py` | Validasi, perintah `ffmpeg`, rename segmen |
| `web_workflow.py` | Alur sukses, simpan browser, cleanup staging |
| `web_state.py` | Session state web dan unggahan sementara |
| `output_destination.py` | Strategi output native vs browser |
| `browser_folder.py` + `browser_folder_frontend/` | Komponen CCv2 pemilih folder & simpan lokal |
| `folder_picker.py` | Dialog folder native per OS |
| `work_paths.py` | Path `.work/` dan pembersihan |
| `messages.py` / `ui_options.py` / `web_seo.py` | Teks UI, opsi, metadata SEO |
| `persistence.py` | Payload base64 untuk transfer hasil ke browser |
| `models.py` | Model data hasil proses |

## 13. Persyaratan non-fungsional

- **Kinerja:** format asal diprioritaskan tanpa re-encode; UI web memakai CSS responsif dan toolbar minimal.
- **Kompatibilitas:** Python 3.10+; `ffmpeg` wajib; desktop membutuhkan Tkinter.
- **Reliabilitas:** error `ffmpeg` ditampilkan ke pengguna; tidak ada sukses palsu saat simpan browser gagal.
- **Maintainability:** logika inti terpisah dari UI; ada unit test dan uji integrasi `ffmpeg`.
- **Deployability:** cloud membutuhkan `packages.txt` dan entry point `app.py`.

## 14. Kriteria keberhasilan

- Pengguna dapat memotong file didukung menjadi beberapa segmen bernama `_1`, `_2`, …
- Hasil muncul di folder lokal yang dipilih dengan struktur subfolder stem file.
- Versi web tidak meninggalkan file input/staging di server setelah sukses.
- Pengguna menerima ringkasan hasil yang jelas setelah proses selesai.
- Test suite (`python -m unittest discover -s tests -v`) lulus di lingkungan dengan `ffmpeg`.

## 15. Risiko dan mitigasi

| Risiko | Mitigasi saat ini |
| --- | --- |
| `ffmpeg` tidak ada di server cloud | `packages.txt`, pesan error deploy, fallback `imageio-ffmpeg` |
| Browser tidak mendukung folder picker | Pesan error/hint Chromium; validasi sebelum proses |
| Potongan tidak tepat menit | Dokumentasi perilaku `-c copy` di UI info |
| File besar di cloud | Staging sementara + hapus setelah sukses; tidak ada arsip server |
| Dialog folder tidak terlihat (macOS) | Instruksi penggunaan di README |

## 16. Pengujian yang sudah ada

- Unit test helper, model, destinasi output, payload browser, SEO meta, cleanup `.work/`.
- Integrasi `ffmpeg` untuk file pendek, konversi MP3, dan penolakan output duplikat.
- Integrasi dilewati otomatis bila `ffmpeg` tidak tersedia.

## 17. Dokumen terkait di repo

- `README.md` — cara instalasi dan menjalankan aplikasi.
- `requirements.txt` — dependensi Python.
- `packages.txt` — dependensi sistem untuk Streamlit Community Cloud.

---

**Status dokumen:** mencerminkan codebase per review internal. Perbarui PRD ini bila ada perubahan perilaku produk yang disengaja di rilis berikutnya.
