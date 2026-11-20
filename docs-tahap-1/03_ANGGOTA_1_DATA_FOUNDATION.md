# Anggota 1 — Data Foundation, XES Import, EventStore, dan Overview

**Owner:** A1 · **Reviewer silang:** A4 · **Bobot estimasi panduan:** 12 poin · **Target:** selesai D1–D7 (7 hari kalender) · **Fitur:** F01, F02, bagian worker bersama A5.

## 1. Instruksi baca untuk manusia dan AI

1. Baca `01_PANDUAN_KERJA_IDENTIK_PDF.md` bagian 01–05, 06, 08–10, Lampiran A–D.
2. Baca `02_DOKUMENTASI_TEKNIS.md` bagian 2–4 (terutama `_trace_pos`, `_row_id`, `EventStore`), 6–8, 10–12.
3. Kerjakan hanya area milik A1 kecuali ada perubahan kontrak yang disepakati semua orang.
4. Jangan membuat angka acuan BPIC17 sebagai hasil aplikasi; data asli hanya boleh dihitung saat benar-benar tersedia.

**Tujuan pekerjaan:** data XES yang dipilih pengguna bisa dibaca melalui PM4Py menjadi satu `EventStore` terpercaya, valid, mudah dipakai modul A2–A4, dan ditampilkan melalui overview yang responsif.

## 2. Batas file yang dimiliki

| File | Isi tanggung jawab | Hasil yang diharapkan |
|---|---|---|
| `src/core/loader.py` | PM4Py XES import, validasi dasar, exception, metadata | `load_event_log(path)` |
| `src/core/event_store.py` | `EventStore`, stable `_trace_pos`, `_row_id`, indeks/case lookup | objek data yang dapat dibagi |
| `src/core/overview.py` | jumlah case/event, atribut, activity frequencies, date range, durasi case | `get_overview(store)` |
| `src/gui/panels/overview_panel.py` | KPI dan tabel aktivitas/case | overview panel terhubung |
| `src/gui/worker.py` | **Kolaborasi A5**: backend worker/status untuk impor XES berat | GUI tidak freeze |
| `tests/test_loader.py` | input invalid, urutan trace, metadata, empty dataset | test otomatis |
| `tests/fixtures.py` | **Kolaborasi awal A2–A4**: fixture minimal yang mengikuti schema final | fixture bersama |

**Tidak dimiliki:** perhitungan 11.7 (A2), 11.15/18 (A3), 11.22/Case Explorer (A4), shell/ekspor (A5). A1 boleh membantu review, bukan mengubah modul pemilik lain tanpa koordinasi.

## 3. Spesifikasi fungsional rinci

### F01 — Import & validasi

- Pilih `.xes` dari GUI (file picker dibuat/diintegrasikan bersama A5); path tidak ditanam di source code.
- Memanggil **PM4Py** secara nyata: `pm4py.read_xes(...)` pada versi yang terpasang.
- Periksa atribut wajib: `case:concept:name`, `concept:name`, `time:timestamp` dan tipe datanya.
- Untuk data kosong, tidak terbaca, path tidak ada, atau atribut wajib hilang, tampilkan error yang bisa dipahami. Jangan crash; hasil dataset sebelumnya harus direset saat switch berhasil.
- Catat keberadaan `lifecycle:transition` dan `org:resource`; *ketiadaan keduanya bukan kegagalan impor seluruh log*, tetapi harus diketahui A3.
- Bentuk `_trace_pos` dari **urutan kejadian dalam masing-masing trace XES**, bukan hanya timestamp. Jika `return_legacy_log_object` digunakan, verifikasi pada versi PM4Py aktual sebelum mengandalkannya.
- Bentuk `_row_id` unik (0..N−1 atau identifier stabil lain); pertahankan pemetaan ke case/posisi untuk highlight evidence.
- Hitung metadata: nama file, ukuran, timestamp/rentang, jumlah case/event, nama dan frekuensi aktivitas, columns yang tersedia, hash SHA-256 bila dibutuhkan final.
- Sediakan penanganan timezone dan periksa bahwa tanggal tidak diubah diam-diam.
- Dokumen sumber melarang rerun/import ulang setiap latihan: parser hanya dipanggil saat membuka dataset baru.

### EventStore — format yang menjadi pondasi semua modul

```python
# Kontrak konseptual (bukan klaim source sudah dibuat)
store.events             # DataFrame semua event
store.case_durations     # per case, dihitung dari keseluruhan trace
store.metadata           # dictionary metadata dataset
```

Syarat tambahan: `store.events` mempunyai `case:concept:name`, `concept:name`, `time:timestamp`, `_trace_pos`, `_row_id`. Cara menghitung durasi final dibakukan bersama A2; A1 menyediakan penyimpanan/cache agar A2 tidak perlu parse XES sendiri. `store.events` tetap **utuh** walau analisis sedang terfilter.

### F02 — Overview

Tampilkan (a) total case, (b) total event, (c) jumlah/nama aktivitas dan frekuensinya, (d) rentang timestamp, (e) mean cycle time yang diperoleh dari durasi case lengkap, dan (f) daftar case + durasi dengan pencarian. Hindari menampilkan jutaan event di tabel UI sekaligus.

**Catatan:** mean cycle time adalah fungsi domain A2. A1 berkoordinasi memakai `get_case_durations(store)`; jika A2 belum siap di D2, overview boleh memasang placeholder bertanda sementara, **jangan** menampilkan angka tidak terverifikasi.

## 4. Kontrak API A1 → tim

| API | Signature konseptual | Dibutuhkan oleh |
|---|---|---|
| Loader | `load_event_log(path: str) -> EventStore` | Semua anggota |
| Overview | `get_overview(store: EventStore) -> dict` atau DTO disepakati | A5 GUI shell |
| Case access | `store.events`, case lookup dan `_trace_pos` | A2, A3, A4 |
| Metadata | `store.metadata` | A5 CSV/About, seluruh laporan |

**Kontrak D1 yang harus dibagikan:** nama atribut, tipe `case_id`, base indeks `_trace_pos` (gunakan 0), keunikan `_row_id`, cara mengakses metadata, standar error, dan contoh 2–3 case fixture.

## 5. Urutan pekerjaan D1–D7

| Hari | Pekerjaan A1 | Bukti/gate |
|---|---|---|
| D1 | Inspeksi XES kecil/nyata, struktur EventStore, validasi atribut, pembagian fixture dengan A2–A4; review spesifikasi bersama | Modul dapat di-import, schema ditulis, minimal fixture tersedia |
| D2 | Implementasi loader, trace index, `_row_id`, metadata, import error dan overview service | Loader + overview lolos unit test sintetis |
| D3 | Implementasi overview panel, status import/worker bersama A5; sambungkan mean dari A2 | Panel overview terlihat melalui shell, UI tidak freeze |
| D4 | Integrasi F01/F02 dengan seluruh panel; perbaiki perbedaan schema dari reviewer A4 | Import → Overview → pilih latihan bekerja pada fixture |
| D5 | Import BPIC17 asli (jika tersedia), catat counts, atribut, label, timezone, performa dan dataset hash | Metadata/log validasi asli tertulis, tanpa klaim palsu |
| D6 | Performance audit, regression, screenshot import/overview; tulis bagian arsitektur/data untuk laporan | Review A4 lulus, tidak ada bug kritis |
| D7 | Uji instalasi bersih bersama A5, re-import, presentasi import/overview, cek CSV dan dokumentasi | Bukti demo dan kontribusi A1 tersedia |

## 6. Pengujian wajib A1

- **T11**: buat trace dua event bertimestamp identik; `_trace_pos` tetap mencerminkan urutan XES.
- **T13**: file rusak atau field wajib hilang → ditolak dengan error jelas dan tidak menutup GUI.
- **T15**: log kosong → status dan statistik terkendali (tidak divide-by-zero).
- Field opsional lifecycle/resource tidak ada → tetap dapat diimpor, peringatkan kemampuan analisis.
- `case:concept:name` kosong/duplikat berbeda jenis → validasi tepat, jangan merge case karena konversi tipe yang tidak aman.
- Dataset yang sama diimpor ulang → jumlah case/event dan urutan trace identik.
- Uji worker: GUI responsif ketika membuka XES besar; signal hasil tidak menyentuh widget dari worker thread.

**Perintah dasar (dijalankan dari root repo setelah dependencies terpasang):**

```bash
python -m pytest tests/test_loader.py -q
python -m pytest -q
```

## 7. Handoff ke anggota lain

- **Ke A2**: EventStore, case IDs, timestamp type, cara memperoleh seluruh event tiap case, metadata n_cases.
- **Ke A3**: label fraud aktual, nilai `lifecycle:transition` yang ditemukan, ketersediaan resource, cara mengakses event asli.
- **Ke A4**: trace order + `_row_id`, lookup case, contoh equal-timestamp cases, akses bukti.
- **Ke A5**: `load_event_log`, `get_overview`, status error terstruktur, status/progress worker, format metadata.

**Sinyal blocker langsung:** PM4Py gagal baca XES, `case:concept:name` tidak dapat diidentifikasi, urutan XES ambigu, import sangat lambat/freeze, atau penanganan timezone belum disepakati. Laporkan D1/D2, jangan tunggu D5.

## 8. Kontribusi di luar pemrograman — wajib bersama

- Menulis **pendahuluan dan sumber dataset bersama A5**, serta bagian arsitektur, parsing, validasi, dan overview.
- Mengambil screenshot file picker, metadata dan overview, termasuk caption/nama hasil.
- Membuat satu rekaman/snapshot case yang membuktikan urutan/validasi atribut; jelaskan dataset yang dipakai.
- Membantu uji BPIC17 bersama seluruh tim; melaporkan ukuran dan hash dataset.
- Menguji minimal satu kasus di luar modul sendiri dan mereview modul A4.
- Menyampaikan segmen import dan overview pada demo, peer review laporan final, dan memahami dua modul lain.

## 9. Definition of Done A1

- [ ] BPIC17 atau XES yang dipilih dapat diimpor dari GUI melalui PM4Py.
- [ ] Atribut wajib dan metadata terbaca benar; opsional diidentifikasi.
- [ ] `_trace_pos` benar terhadap urutan trace XES; `_row_id` unik.
- [ ] `EventStore` dan API disepakati seluruh tim tanpa parsing ulang.
- [ ] Overview menampilkan KPI, frekuensi aktivitas, rentang waktu, durasi case dengan pencarian.
- [ ] Worker berjalan tanpa UI freeze; error bukan crash.
- [ ] Test A1 lulus dan reviewer A4 menerima PR.
- [ ] Dokumentasi, screenshot, validasi, dan bagian laporan A1 selesai.

## 10. Prompt untuk coding agent A1

```text
Peran Anda: developer Anggota 1 (A1), Data Foundation BPIC17.
Baca panduan kerja identik PDF + dokumentasi teknis + file A1 ini.
Rancang/implementasikan hanya loader.py, event_store.py, overview.py,
overview_panel.py, tests/test_loader.py, serta worker.py bersama A5.
Buat dahulu kontrak EventStore dan fixture, kemudian uji PM4Py pada versi lokal.
Pertahankan urutan trace XES walau timestamp identik; jangan hanya sort timestamp.
Jangan menafsirkan lifecycle yang hilang sebagai complete.
Lakukan integrasi tanpa menulis algoritma 11.7/11.15/11.18/11.22.
Jalankan pytest, laporkan file yang diubah, hasil uji yang BENAR-BENAR berjalan,
risiko, dan API/handoff untuk anggota lain. Jangan mengarang hasil BPIC17 asli.
```
