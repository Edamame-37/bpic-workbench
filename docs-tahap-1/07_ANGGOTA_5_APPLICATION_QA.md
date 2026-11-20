# Anggota 5 — Application Integration, Shared GUI, Export, dan Quality Assurance

**Owner:** A5 · **Reviewer:** seluruh A1–A4 · **Estimasi:** 12 poin · **Fitur:** bagian F07 (export/reset), shell GUI, shared widget, About, integration tests dan packaging · **Jadwal:** D1–D7.

## 1. Peran yang benar — bukan mengerjakan semuanya

A5 adalah penanggung jawab **kerangka aplikasi yang menyatukan modul**, bukan developer seluruh panel dan bukan penulis tunggal laporan kelompok. Pemilik A1–A4 wajib menyiapkan logika, panel, unit tests, screenshot, dan bagian laporan masing-masing.

Sebelum coding baca `01_PANDUAN_KERJA_IDENTIK_PDF.md` bagian 03–04, 06–11, Lampiran A–C serta `02_DOKUMENTASI_TEKNIS.md` bagian 2–4, 6–12. Jika kontrak data belum disepakati D1, koordinasikan dulu agar seluruh anggota tidak membangun antarmuka yang berbeda.

## 2. File yang menjadi tanggung jawab

| File | Tujuan |
|---|---|
| `src/main.py` | titik masuk aplikasi desktop |
| `src/gui/main_window.py` | shell, navigasi antar menu, dataset state, panel registration |
| `src/gui/common/` | result cards, case table, status banner, error dialog, reusable widgets |
| `src/gui/panels/export_panel.py` | pilih direktori ekspor, ringkasan/CSV, About |
| `src/core/export.py` | menulis `summary.csv`, `selected_cases.csv`, `evidence.csv` |
| `src/gui/worker.py` | **kolaborasi A1**: worker lifecycle dan concurrency UI |
| `tests/test_export.py` | CSV schema, status, empty/error export |
| `tests/test_integration.py` | E2E F01–F07, rerun/reset, dataset switching |
| `README.md`, `requirements.txt`, `.gitignore` | instalasi, penggunaan, reproduktibilitas, exclusion data besar |
| `docs/laporan.md` (penggabungan) | menggabungkan **konten yang ditulis semua** anggota, bukan menulis seluruhnya |

**Batas:** A5 tidak boleh menulis ulang logika 11.7, 11.15, 11.18 atau 11.22 di GUI. Jika hasil berbeda, eskalasi ke pemilik modul agar hanya ada satu sumber perhitungan.

## 3. Kontrak antarmuka GUI yang harus disepakati D1

### 3.1. Alur aplikasi

```text
Launch App
  → Dataset/Status tab
  → Pilih XES lewat file dialog
  → PM4Py import di worker (A1)
  → EventStore aktif tersimpan di application controller
  → Overview A1 / 11.7 A2 / Rework A3 / Sequence A4
  → pilih case → Case Explorer A4
  → Export CSV A5
  → Reset hasil/rerun tanpa parse XES ulang
```

A5 menyediakan shell dengan tab/menu `Dataset & Status`, `Overview`, `Exercise 11.7`, `Exercise 11.15 & 11.18`, `Exercise 11.22`, `Case Explorer`, `Export`, `About`. Panel masing-masing anggota dapat terhubung tanpa bergantung pada layout detail shell.

**Kontrak panel disepakati bersama:**

```python
# Salah satu pola antarmuka yang disarankan, bukan API yang sudah tersedia.
panel.set_store(store)                        # data baru atau None
panel.show_result(result)                     # hasil AnalysisResult dari core
panel.open_case_requested(case_id, row_ids)   # signal menuju Explorer A4
```

Jika menggunakan signal/slot Qt, definisikan signature, tipe data, dan siapa pemilik signal. Hindari circular import UI dan core.

### 3.2. Result card dan tabel bersama

Komponen UI A5 sebaiknya memiliki:

- label nomor soal + rule/filter, count **cases**, denominator, mean days (jika ada), persentase (11.22), dan status;
- daftar case yang bisa dicari, diurutkan, dan dibuka lewat Case Explorer;
- tampilan evidence event dengan row ID/posisi/timestamp;
- state `idle`, `loading`, `ok`, `unavailable`, dan `error` yang mudah dibedakan;
- empty state yang jelas tanpa menjadikan angka `0` sebagai jawaban palsu;
- pagination/virtualized model untuk data besar.

**Penggunaan UI bukan sebagai mesin analisis.** `AnalysisResult` dari A2/A3/A4 menjadi sumber data UI dan ekspor yang sama.

## 4. Worker thread dan keselamatan state aplikasi

Pekerjaan berat harus tidak membekukan GUI. Rekomendasi Qt: `QObject` worker + `QThread`, signal progress/finished/error, cleanup aman lewat `quit` dan `deleteLater` serta penyimpanan referensi thread selama berjalan. Desain implementasi harus dicek dengan dokumentasi Qt sesuai versi lokal.

Syarat perilaku:

1. `Load XES` tidak menjalankan `pm4py.read_xes` di GUI thread.
2. Jika masih ada job aktif, cegah action yang bertentangan atau antrikan dengan jelas.
3. Progress yang tidak bisa dihitung numerik memakai *indeterminate indicator*, bukan persentase 0–100 buatan.
4. Worker tidak boleh langsung memanipulasi widget Qt; update dari signal/slot ke GUI thread.
5. Dataset switch harus menghapus hasil/preview lama, dan hasil thread lama tidak boleh masuk ke dataset baru (gunakan job/dataset generation ID atau mekanisme serupa).
6. Error import, export permission failure, atau analisis unavailable tidak boleh membuat aplikasi keluar sendiri.
7. Reset/rerun analisis memakai EventStore aktif yang telah dibaca; tidak membaca ulang XES kecuali pengguna memilih file baru.

**Kerjakan bersama A1:** A1 pemilik fungsi membaca file dan status import; A5 pemilik kontrak worker dengan shell GUI. Sepakati event sukses/gagal dan cleanup pada D1.

## 5. Export CSV — fungsi inti A5

**Minimal keluaran:**

| Nama CSV | Field minimal | Tujuan |
|---|---|---|
| `summary.csv` | `exercise_id`, `rule_description`, `count`, `denominator`, `mean_days`, `percentage`, `status`, `notes` | ringkasan seluruh delapan jawaban |
| `selected_cases.csv` | `exercise_id`, `case_id` | case terpilih per soal |
| `evidence.csv` | `exercise_id`, `case_id`, `evidence_type`, `_row_id`/`cancel_row_id`/`accept_row_id`, posisi, timestamp, lifecycle/resource jika relevan | event pembukti yang dapat ditelusuri |

Meskipun source `AnalysisResult` antarsoal berbeda kolom evidence, ekspor harus menggunakan **skema konsisten**: gabungkan union columns dan isi yang tidak berlaku dengan kosong; jangan membuang data penghubung ke case/event.

**Persyaratan ekspor:** hasil `unavailable` tetap menyertakan `status`/`notes` dan tidak ditampilkan sebagai jawaban nol valid; `denominator` ada; timestamp/identifier tetap terbaca; encoding UTF-8; file bisa dibaca kembali; pilih lokasi output; tangani path tidak bisa ditulis dan cancel save dialog.

### 5.1. Validasi CSV sederhana

```python
# Ini contoh pemeriksaan setelah export, bukan nilai jawaban statis.
import pandas as pd
summary = pd.read_csv("summary.csv")
assert summary["exercise_id"].nunique() == 8
assert {"exercise_id", "count", "denominator", "status"} <= set(summary.columns)
```

Pada aplikasi penuh, hasil `summary.csv` perlu diuji cocok dengan objek result yang terlihat di panel; jangan membuat layer export menghitung ulang event log.

## 6. Integrasi F01–F07 dan About

### Aplikasi minimum yang harus dapat didemonstrasikan

1. Buka aplikasi dari `python -m src.main` (atau command yang dipilih tim dan benar-benar diuji).
2. Pilih XES, indikator proses muncul, metadata/overview tampil.
3. Tab 11.7 menampilkan A–E, count, mean dan tombol case.
4. Tab 11.15/11.18 menampilkan rework + lifecycle/resource evidence.
5. Tab 11.22 menampilkan count, denominator, persentase dan pasangan event.
6. Case Explorer membuka case dan highlights dari tiap soal.
7. Export menghasilkan CSV dan bisa dibuka.
8. Reset/re-run berjalan tanpa import XES ulang; error ditangani.
9. About memuat versi Python, PM4Py, dependency utama, OS, dan identitas proyek.

Jika modul anggota belum ada saat D1–D2, gunakan **mock result bertanda sintetis** untuk desain panel. Jangan membiarkan mock tersebut tampil sebagai hasil dataset asli saat D4/D5.

## 7. Packaging, README dan reproducibility

Gunakan repository modular dan environment yang dapat dipasang ulang. Ini bukan kewajiban membuat installer `.exe` jika instruksi hanya meminta aplikasi desktop dapat dijalankan pada komputer lain beserta langkah instalasi.

Perintah dokumentasi contoh untuk terminal root repo:

```bash
python -m venv .venv
# Aktifkan environment sesuai OS, lalu:
python -m pip install -r requirements.txt
python -m pytest -q
python -m src.main
```

Simpan `requirements.txt` dari versi yang benar-benar dipakai dan diuji, bukan snapshot tak dipilah yang berisi paket pribadi tidak relevan. README wajib menjelaskan syarat Python/OS aktual, cara menjalankan, cara memilih XES, urutan menu, definisi filter, cara membuka case evidence, export, keterbatasan lifecycle dan cara pengujian.

**Jangan commit** dataset BPIC17 asli, `.venv`, password/token, file hasil yang sensitif, atau build cache. Berikan `.gitignore` yang dapat diaudit. Saat final catat commit hash/tag, versi dependency, sumber/hash dataset, dan tanggal uji.

## 8. Timeline A5 tujuh hari

| Hari | Target khusus A5 | Bukti gate |
|---|---|---|
| **D1** | Setup repo + branch dan skeleton; sepakati kontrak panel/result/worker; sediakan placeholder menu semua fitur | App shell terbuka dan fixture/mock result dapat ditampilkan |
| **D2** | Reusable widgets, CSV skeleton, About draft, interface import status bersama A1 | Shared component terpakai dua panel atau fixture |
| **D3** | Navigasi semua panel A1–A4, export core, worker cleanup, integration tests dasar | Semua menu dapat diakses, export uji sintetis |
| **D4** | Merge PR tiap owner; uji E2E Import→8 jawaban→Evidence→CSV; catat isu | Demo sintetik utuh dan bukti integrasi |
| **D5** | Jalankan XES asli bersama tim, pantau responsivitas, integritas CSV, waktu impor dan perbandingan hasil | Log pengujian BPIC17 dan kesalahan terkumpul |
| **D6** | Regression, packaging, README, error/reset, penggabungan laporan dan screenshots tim | Feature freeze: tanpa bug kritis, dokumen hasil tiap orang sudah masuk |
| **D7** | Clean environment, final QA, rekaman demo dengan semua anggota, checklist pengumpulan | Build/instalasi diuji dan paket diserahkan |

## 9. Integration & reliability tests A5

- E2E import XES → Overview → delapan hasil → Case Explorer → CSV sukses.
- T13: file rusak/missing attributes tidak menutup aplikasi.
- T15: data kosong tidak menimbulkan divide by zero.
- Uji `unavailable`: UI dan CSV menyebut alasan, bukan count nol yang dianggap valid.
- Uji dataset A lalu B saat result A belum selesai: jangan tampilkan hasil A di tampilan dataset B.
- Uji rerun: hasil sama tanpa pemanggilan ulang parser.
- Uji summary CSV: tepat delapan row hasil; status/denominator lengkap; export cases/evidence bisa dibaca ulang.
- Uji save destination read-only, dialog cancel, dan nama file dengan spasi.
- Uji GUI tabel besar: tidak membuat jutaan item widget sekaligus, tetap responsif.
- Uji clean install pada komputer/environment yang belum memakai repo tersebut.

```bash
python -m pytest tests/test_export.py -q
python -m pytest tests/test_integration.py -q
python -m pytest -q
```

Catat hasil yang benar-benar dieksekusi; jika test tidak berjalan karena dataset/dependency belum siap, tulis blocker, jangan mengklaim lulus.

## 10. Koordinasi tim dan pekerjaan luar program

A5 **mengatur penggabungan**, tetapi kontribusi laporan dan presentasi dibagi:

| Kegiatan | Tanggung jawab |
|---|---|
| Pendahuluan/sumber XES | **A1 + A5 menulis**, A2–A4 meninjau |
| Metodologi hasil 11.7 | **A2 menulis**, tim mengulas |
| Metodologi hasil 11.15/11.18 | **A3 menulis**, tim mengulas |
| Metodologi hasil 11.22/Explorer | **A4 menulis**, tim mengulas |
| Testing/kendala | **Semua** menulis hasil modulnya; A5 menulis integration/packaging |
| Kesimpulan, keterbatasan, revisi | **Semua** berkontribusi dan menyetujui |
| Screenshot/segmen demo | **A1–A5** sesuai modul masing-masing |
| Formatting akhir/penyatuan lampiran | A5 mengoordinasi, **bukan** menanggung semua isi |

A5 menyiapkan alat rekam/demo tetapi **semua anggota berbicara** dalam segmen fitur miliknya. A5 juga menyiapkan daftar kontribusi berdasar PR/test/screenshot/section laporan nyata, bukan perkiraan.

## 11. Risiko integrasi yang harus dipantau harian

| Risiko | Indikator awal | Mitigasi |
|---|---|---|
| API `EventStore` berubah | panel gagal membaca dataset | kontrak dibekukan D1, PR review bersama |
| Result tidak konsisten | ekspor berbeda dari panel | satu `AnalysisResult` dipakai UI dan export |
| Semua panel bergantung A5 | anggota menunggu UI | berikan reusable template dan panel ownership A1–A4 |
| Worker freeze/crash | progress tidak berubah, window unresponsive | worker thread dan cleanup; load test D3/D5 |
| Screenshot/laporan terlambat | D5 belum ada evidence | owner fitur menulis/mengambil screenshot sejak D4 |
| Benchmark berbeda | hasil BPIC17 tak cocok slide | audit data+semantik; jangan hard-code |

## 12. Definition of Done A5

- [ ] Aplikasi terbuka di environment bersih dan memiliki seluruh area GUI wajib.
- [ ] Semua panel A1–A4 tersambung; tidak ada analitik bisnis ganda di UI.
- [ ] Proses berat tidak membekukan GUI; thread lifecycle dan error aman.
- [ ] CSV summary, selected cases dan evidence benar serta bisa dibaca lagi.
- [ ] Rerun/reset tanpa parse ulang berfungsi; dataset state konsisten.
- [ ] About, README, requirements, .gitignore, dokumentasi versi/hash tersedia.
- [ ] Integration, export, reliability tests dicatat; minimal satu reviewer menerima setiap PR.
- [ ] Laporan digabung dari konten seluruh anggota, bukan ditulis A5 sendiri.
- [ ] Demo final melibatkan A1–A5 dan checklist D7 telah diperiksa.

## 13. Prompt untuk coding agent A5

```text
Anda developer Anggota 5 (A5), Application Integration & QA BPIC17.
Baca 01_PANDUAN_KERJA_IDENTIK_PDF.md, 02_DOKUMENTASI_TEKNIS.md,
dan file A5 ini. Kerjakan shell/main.py/main_window.py, shared widgets,
export.py, export_panel.py, worker.py bersama A1, tests export/integration,
README, requirements, dan packaging.
Jangan menghitung ulang soal 11.7/11.15/11.18/11.22 di GUI.
Sediakan kontrak panel dan widget reusable supaya A1–A4 membuat panel sendiri.
Tampilkan status unavailable bila lifecycle/resource tidak cukup, jangan
menyulapnya menjadi nol yang valid.
Pastikan worker Qt tidak membekukan UI, hasil job lama tidak mengotori
state dataset baru, export tepat 8 hasil plus selected_cases/evidence.
Jalankan test yang benar-benar dapat dieksekusi dan laporkan output,
file berubah, blocker, serta daftar PR/handoff kepada A1–A4.
Koordinasikan laporan bersama; jangan menulis bagian semua anggota sendiri.
```
