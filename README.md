# BPIC Workbench

Aplikasi desktop untuk mengimpor event log XES dengan PM4Py, menganalisis latihan BPIC17, menelusuri evidence per case/event, dan mengekspor hasil ke CSV.

## Status

Repositori berada pada tahap fondasi awal. Kontrak `EventStore` dan `AnalysisResult`, struktur package, shell GUI, fixture sintetis, dan smoke test sudah disiapkan. Loader XES dan modul analitik belum diimplementasikan.

## Prasyarat

- Python 3.13
- Windows, Linux, atau macOS yang didukung oleh dependency terkait
- File XES disimpan secara lokal dan tidak di-commit ke Git

Versi baseline yang diuji pada setup awal:

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

## Menjalankan

```bash
python -m src.main
```

Shell awal menampilkan area Dataset, Overview, Exercise 11.7, Rework, Exercise 11.22, Case Explorer, Export, dan About. Panel masih berupa status implementasi dan belum menghitung hasil BPIC17.

## Pengujian

```bash
python -m pytest -q
```

Test awal memverifikasi kontrak data dan memastikan shell GUI dapat dibuat dalam mode headless.

## Struktur

```text
data/                   XES lokal; tidak masuk Git
docs/                   laporan, kontribusi, dan screenshot
docs-tahap-1/           dokumentasi sumber proyek
src/core/               kontrak dan logika domain
src/gui/                shell serta panel desktop
tests/                  fixture sintetis dan pengujian
```

## Aturan Domain Utama

- Semua hasil harus dihitung dari dataset aktif; angka referensi dosen bukan konstanta program.
- Urutan event menggunakan urutan asli trace XES melalui `_trace_pos`, bukan sorting timestamp.
- `EventStore` adalah sumber data tunggal untuk seluruh modul.
- Hasil yang membutuhkan atribut tidak tersedia harus berstatus `unavailable`, bukan ditampilkan sebagai nol yang valid.
- Dataset BPIC17 asli, credential, virtual environment, dan hasil sensitif tidak boleh di-commit.

## Dokumentasi

Spesifikasi lengkap berada di [`docs-tahap-1`](docs-tahap-1). Urutan baca utama:

1. `01_PANDUAN_KERJA_IDENTIK_PDF.md`
2. `02_DOKUMENTASI_TEKNIS.md`
3. Dokumen anggota sesuai modul yang dikerjakan

