# BPIC Workbench

Aplikasi desktop untuk mengimpor event log XES dengan PM4Py, menjalankan delapan analisis BPIC17, menelusuri evidence per case/event, dan mengekspor hasil ke CSV.

## Prasyarat

- Python 3.13
- Windows, Linux, atau macOS yang didukung dependency terkait
- File XES lokal; dataset asli tidak disimpan di repository

Versi yang diuji pada Windows 11:

- Python 3.13.7
- PM4Py 2.7.23.13
- pandas 3.1.1
- PySide6 6.12.0
- pytest 9.2.0

## Setup

### Windows PowerShell

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Linux/macOS

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Menjalankan aplikasi

```powershell
python manage.py run
```

Alternatif:

```powershell
python -m src.main
```

Navigasi aplikasi menggunakan workspace shell bergaya process-analysis tool:

- Sidebar kiri mengelompokkan Workspace, Analyses, Investigation, Output, dan System.
- Header menampilkan halaman aktif, breadcrumb, Back/Forward, serta dataset context.
- Badge sidebar menunjukkan loading, kesiapan dataset, jumlah hasil, case aktif, dan status export.
- Action bar bawah menyediakan Import XES, Reset, Rerun All, Export, dan About dari halaman mana pun.
- Gunakan `Ctrl+1` sampai `Ctrl+8` untuk berpindah halaman, `Ctrl+O` untuk import, `Ctrl+R` untuk rerun, `Alt+Left/Right` untuk history, dan `F1` untuk About.

Alur penggunaan:

1. Buka `Dataset & Status`, pilih file `.xes` atau `.xes.gz`, lalu tunggu validasi selesai.
2. Periksa metadata, jumlah case/event, atribut, dan peringatan pada Dataset dan Overview.
3. Jalankan analisis Outcome Kasus.
4. Pilih aktivitas fraud yang tepat pada Rework bila kandidat tidak terdeteksi secara tunggal, lalu jalankan 11.15 dan 11.18.
5. Jalankan analisis Urutan Cancel-Accept.
6. Pilih case hasil dan buka Case Explorer untuk melihat trace lengkap serta event yang disorot.
7. Buka Export, pilih direktori, lalu ekspor setelah delapan hasil tersedia.

Tombol `Reset hasil analisis` menghapus hasil turunan tetapi mempertahankan dataset aktif. Tombol `Jalankan ulang semua` memakai `EventStore` yang sudah dimuat dan tidak membaca ulang XES.

## Definisi analisis

- 11.7 A: jumlah seluruh case.
- 11.7 B: mean cycle time seluruh case dari timestamp minimum–maksimum trace utuh.
- 11.7 C: case yang mengandung `O_Accepted`.
- 11.7 D: case yang mengandung `O_Refused`; dapat overlap dengan C.
- 11.7 E: event terakhir menurut `_trace_pos` adalah `O_Cancelled`.
- 11.15: aktivitas target memiliki sedikitnya dua event `complete` dalam satu case.
- 11.18: sedikitnya dua event `complete` dilakukan resource valid yang sama.
- 11.22: terdapat `O_Cancelled` di posisi `i` dan `O_Accepted` di posisi `j`, dengan `i < j`.

Lifecycle atau resource yang tidak cukup untuk membuktikan aturan ditampilkan sebagai `unavailable`, bukan sebagai hasil nol yang valid.

## Export CSV

Export menghasilkan tiga file UTF-8:

- `summary.csv`: delapan hasil, rule, count, denominator, mean, percentage, status, dan notes.
- `selected_cases.csv`: pasangan kode analisis dan case terpilih.
- `evidence.csv`: union kolom evidence, termasuk row ID, posisi, timestamp, lifecycle/resource, atau pasangan cancel–accept sesuai analisis.

Direktori `exports/` diabaikan Git. Periksa sensitivitas data sebelum membagikan hasil export.

## Pengujian

```powershell
python manage.py test -q
```

Atau jalankan lapisan tertentu:

```powershell
python -m pytest tests/test_export.py -q
python -m pytest tests/test_integration.py -q
```

Pengujian sintetis mencakup T01–T15, callback worker pada GUI thread, dataset switching, reset/rerun, Case Explorer, dan pembacaan ulang CSV. Validasi angka BPIC17 asli tetap memerlukan file dataset yang disepakati beserta pencatatan nama, ukuran, SHA-256, dan versi environment.

## Struktur

```text
data/                   XES lokal; tidak masuk Git
docs/                   laporan, QA, kontribusi, dan screenshot
src/core/               kontrak, loader, analitik, dan export
src/gui/common/         komponen GUI reusable
src/gui/panels/         panel Dataset sampai About
tests/                  unit, GUI, integration, dan reliability tests
```

## Aturan domain dan keterbatasan

- Semua hasil dihitung dari dataset aktif; angka referensi materi bukan konstanta program.
- Urutan event memakai `_trace_pos` dari urutan asli trace XES, bukan sorting timestamp.
- Seluruh modul memakai satu `EventStore`; tidak ada panel yang mem-parse XES sendiri.
- Case ID dan row ID dipertahankan sebagai identifier, termasuk leading zero.
- Dataset BPIC17 asli belum tersedia di repository dan hasil numerik asli belum diverifikasi.
- PM4Py dapat menampilkan warning dependency opsional `r4pm`; fallback `rustxes` tetap digunakan.
- Tinjau ketentuan lisensi PM4Py sebelum distribusi aplikasi di luar konteks repository ini.
