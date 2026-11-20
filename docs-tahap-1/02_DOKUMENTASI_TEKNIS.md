# Dokumentasi Teknis — BPIC17 Desktop Event Log Analyzer

> **Peruntukan:** seluruh anggota tim dan coding agent (Codex, Antigravity, atau setara). **Status:** rancangan implementasi operasional, bukan laporan hasil eksekusi. **Durasi:** D1–D7, tujuh hari kalender berturut-turut. **Tim:** A1–A5.

## 0. Hierarki acuan dan cara membaca dokumen

1. **Instruksi dosen versi 16 November 2026** adalah sumber kewajiban paling tinggi: 8 jawaban (11.7 A–E, 11.15, 11.18, 11.22), F01–F07, Python/PM4Py, GUI desktop, evidence, ekspor CSV, pengujian, dan pengumpulan.
2. `01_PANDUAN_KERJA_IDENTIK_PDF.md` adalah transkripsi konten panduan final 7 hari dari PDF tim. Dokumen ini **tidak mengubah** isinya.
3. **Dokumen teknis ini** menjabarkan antarmuka, algoritma, pengujian, dan keputusan praktis agar implementasi antarmodul konsisten. Bila ada penjelasan tambahan di sini yang tidak tertulis di PDF, anggap itu **rekomendasi implementasi**, bukan instruksi dosen baru.
4. `03_ANGGOTA_1_DATA_FOUNDATION.md` s.d. `07_ANGGOTA_5_APPLICATION_QA.md` adalah instruksi operasional masing-masing pemilik fitur.

**Catatan administrasi:** instruksi resmi menyebut 4 mahasiswa; rencana ini untuk 5 anggota sesuai kondisi tim. Izin dosen harus dikonfirmasi dan dicatat; jangan menulis bahwa izin sudah diberikan bila belum ada buktinya.

## 1. Sasaran, batas, dan Definition of Done global

Aplikasi harus menerima `.xes` yang dipilih pengguna; mengimpor/memproses menggunakan **PM4Py**; menghitung semua jawaban dari log aktif, bukan dari konstanta; menyajikan kondisi filter, count, mean cycle time/persentase, daftar case ID, dan event pembukti; serta mengekspor minimal CSV. Pengguna tidak perlu menyunting kode atau menjalankan notebook.

| Wajib | Bukan target Tahap 1 |
|---|---|
| Import dan validasi XES; overview; 8 hasil; Case Explorer; export; status/progress; rerun/reset | Alpha/Heuristics/Inductive Miner; Petri net discovery; klon Disco/Celonis; ML prediction |
| Unit test sintetis, uji BPIC17 asli, perbandingan dengan slide, laporan bersama, demo | DFG, analisis fast/slow, PDF otomatis, generic filter (hanya jika seluruh tugas wajib sudah selesai) |

**Selesai** bila F01–F07 hidup dari GUI, 8 hasil benar secara semantik, tidak ada angka hard-coded, evidence dapat diaudit, T01–T15 diperiksa (T01–T08 wajib lulus), import ulang deterministik, ekspor valid, dan paket pengumpulan lengkap. D6 *feature freeze*; D7 QA dan serah.

## 2. Arsitektur yang disepakati

```text
XES dipilih pengguna
      |
      v
[GUI file dialog / A5] ---> [worker responsif / A1+A5]
      |                                  |
      +----------------> [PM4Py parser / A1]
                                      |
                           [EventStore / A1]
                    rows + trace position + row ID
                  attributes + case index + metadata
                                      |
                     +----------------+-----------------+
                     |                |                 |
              [11.7 / A2]     [11.15/18 / A3]     [11.22 / A4]
                     |                |                 |
                     +------- AnalysisResult -----------+
                                      |
                     +----------------+---------------+
                     |                |               |
                  GUI panels     Case Explorer      CSV export
                  A1-A4               A4                A5
```

**Aturan dependensi:** `src/core/` tidak mengimpor `src/gui/`. Modul analisis tidak mengakses widget. Widget tidak menghitung logika bisnis langsung. Tidak boleh ada modul yang diam-diam membaca XES sendiri; semua memakai `EventStore` aktif yang sama.

### 2.1. Struktur repository kerja

```text
bpic17-desktop/
├── README.md
├── requirements.txt
├── .gitignore
├── pyproject.toml                     # opsional
├── data/                              # XES asli lokal, jangan commit
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── loader.py                   # A1
│   │   ├── event_store.py              # A1
│   │   ├── overview.py                 # A1
│   │   ├── cycle_time.py               # A2
│   │   ├── ex_11_7.py                  # A2
│   │   ├── rework.py                   # A3
│   │   ├── ex_11_15_18.py              # A3
│   │   ├── ordering.py                 # A4
│   │   ├── ex_11_22.py                 # A4
│   │   ├── result.py                   # KONTRAK BERSAMA (disepakati D1)
│   │   └── export.py                   # A5
│   └── gui/
│       ├── __init__.py
│       ├── main_window.py              # A5
│       ├── worker.py                   # A1+A5
│       ├── common/                     # A5 (widget, formatting, table)
│       └── panels/
│           ├── overview_panel.py       # A1
│           ├── exercise_11_7_panel.py  # A2
│           ├── rework_panel.py         # A3
│           ├── sequence_panel.py       # A4
│           ├── case_explorer_panel.py  # A4
│           └── export_panel.py         # A5
├── tests/
│   ├── conftest.py
│   ├── fixtures.py
│   ├── test_loader.py
│   ├── test_11_7.py
│   ├── test_rework.py
│   ├── test_ordering.py
│   ├── test_export.py
│   └── test_integration.py
└── docs/
    ├── laporan.md
    ├── hasil_validasi.csv
    ├── screenshots/
    └── pembagian_kontribusi.md
```

Penamaan panel dan `conftest.py` adalah **penjabaran teknis** dari struktur yang lebih ringkas di panduan. Bila repo sudah punya nama berbeda, pilih salah satu secara bersama D1, jangan membuat folder duplikat.

## 3. Kontrak data lintas modul — harus dibekukan pada D1

### 3.1. Input dan atribut XES

| Atribut | Status | Perilaku wajib |
|---|---|---|
| `case:concept:name` | Wajib | Identitas trace/case; tidak boleh kosong atau ambigu. |
| `concept:name` | Wajib | Label aktivitas asli; pertahankan kapitalisasi. |
| `time:timestamp` | Wajib | Tanggal/waktu valid; jangan hilangkan informasi zona waktu. |
| `lifecycle:transition` | Opsional pada log, **wajib diketahui untuk complete-only** | Jika tak dapat membuktikan `complete`, 11.15 dan 11.18 tidak boleh mengklaim hasil valid. |
| `org:resource` | Opsional pada log, **dibutuhkan untuk 11.18** | Resource `null`, string kosong, atau whitespace tidak dihitung sebagai resource identik. |
| `_trace_pos` | Internal wajib | Urutan `0,1,2,...` pada **masing-masing trace sebagaimana dibaca dari XES**. |
| `_row_id` | Internal wajib | ID event unik dan stabil untuk detail/evidence. |

**Keputusan krusial tentang urutan:** dua event dapat memiliki timestamp sama. Jangan melakukan `sort_values(timestamp)` lalu menyebut hasilnya urutan asli. Rekomendasi: gunakan pembacaan XES sebagai struktur trace dengan `pm4py.read_xes(path, return_legacy_log_object=True)` apabila didukung versi yang dipasang; iterasi trace satu per satu dan berikan `_trace_pos` saat membaca, kemudian bentuk DataFrame. Alternatif DataFrame langsung hanya boleh dipakai jika diverifikasi mempertahankan urutan asli event dalam trace. Simpan hasil verifikasi pada test T11. API PM4Py bersifat version-sensitive; konfirmasi signature di environment tim.

**Kebijakan tanggal:** jika timezone-aware, hitung durasi dari timestamp yang merepresentasikan instan absolut (misalnya setelah normalisasi ke UTC) tanpa mengubah nilai aslinya di tampilan evidence. Jika timestamp naive, tulis keterbatasannya; jangan mencampur naive dengan aware tanpa validasi.

### 3.2. `EventStore` sebagai single source of truth

Contoh *kontrak konseptual* (boleh diimplementasikan sebagai dataclass/properti lain dengan persetujuan tim):

```python
from dataclasses import dataclass
import pandas as pd

@dataclass(frozen=True)
class EventStore:
    events: pd.DataFrame          # 1 baris per event, dengan _trace_pos & _row_id
    case_durations: pd.DataFrame  # 1 baris per case, duration_days
    metadata: dict               # file, hash, columns, counts, versions
    # case index / trace lookup dapat disimpan melalui field/cache tambahan
```

- `events` mencakup **semua event** dari log aktif; tidak diganti oleh subset filter soal.
- `case_durations` berisi case ID, waktu minimum/maksimum, dan `duration_days`; dihitung **satu kali** dari log penuh.
- `metadata` harus dapat memuat nama file, ukuran, SHA-256, jumlah case/event, nama atribut, versi environment.
- Case ID yang diekspor dijadikan teks; jangan secara sembarang mengubah leading zeros atau nilai identifier.
- `case_id` dalam tabel turunan harus dapat dipetakan kembali ke `case:concept:name` yang asli.

### 3.3. `AnalysisResult` — kontrak wajib sesuai panduan

```python
from dataclasses import dataclass
import pandas as pd

@dataclass
class AnalysisResult:
    exercise_id: str
    rule_description: str
    count: int
    denominator: int
    case_ids: list[str]
    mean_days: float | None = None
    percentage: float | None = None
    evidence: pd.DataFrame | None = None
    status: str = "ok"     # ok | unavailable | error
    notes: str = ""
```

**Invariants:**

- Untuk `status="ok"`: `count == len(set(case_ids))`; tidak ada case ID di luar log aktif; `denominator == n_cases(log_aktif)`; `0 <= count <= denominator`.
- Angka nol yang valid hanya berarti filter dievaluasi lengkap dan tidak menemukan kecocokan. `unavailable` berarti data tidak memadai; jangan dipalsukan menjadi `count=0, status=ok`.
- `mean_days` hanya untuk 11.7 B/C/D/E; A boleh `None`, 11.15/11.18/11.22 boleh `None`.
- `percentage` wajib untuk 11.22 jika `denominator > 0`; tampilkan formula dan denominator.
- Seluruh panel dan export memakai **objek hasil yang sama**, bukan menghitung ulang statistik dari tabel tampilan.
- Label `exercise_id` harus disepakati: `11.7 A`, `11.7 B`, ..., `11.15`, `11.18`, `11.22` (8 hasil total).

**Aturan jika tidak tersedia:** untuk representasi `count` yang diwajibkan bertipe `int` tetapi analisis berstatus `unavailable`, `count=0` boleh digunakan sebagai *placeholder struktural saja*, selama GUI/ekspor jelas menampilkan **N/A / unavailable** dan tidak menganggap nol sebagai jawaban. Alternatif perubahan tipe menjadi nullable hanya lewat perubahan kontrak bersama.

### 3.4. Kontrak evidence

Evidence tidak sekadar daftar event dengan nama aktivitas yang sama, tetapi **kejadian yang membuktikan kondisi**.

| Exercise | Minimal evidence per case | Catatan |
|---|---|---|
| 11.7 C/D | `case_id`, `_row_id`, `_trace_pos`, `concept:name`, `time:timestamp` untuk setidaknya satu matching event | Semua event asli tetap bisa dilihat lewat Case Explorer. |
| 11.7 E | `case_id` dan event terakhir aktual | Ambil dari `_trace_pos` terakhir, bukan filter activity saja. |
| 11.15 | Semua/bukti minimal dua event yang benar-benar `complete`, `case_id`, `_row_id`, lifecycle, posisi | Sertakan total complete per case. |
| 11.18 | Setidaknya dua `complete` dengan **resource yang sama**; resource nonblank | Sertakan resource ID dan jumlah pada case/resource itu. |
| 11.22 | `case_id`, `cancel_row_id`, `cancel_position`, `cancel_timestamp`, `accept_row_id`, `accept_position`, `accept_timestamp` | Pasangan harus `cancel_position < accept_position`. |

Prinsip memori: jangan salin seluruh 1,2 juta event ke setiap `AnalysisResult`. Simpan minimal evidence atau index/ID per case, lalu Case Explorer mengambil trace lengkap dari store.

## 4. Fungsi publik yang harus diimplementasikan

> Nama ini adalah **kontrak antarmodul** dari panduan, bukan jaminan fungsi sudah ada. Implementasikan dan uji sebelum modul UI memakainya.

| Pemilik | Fungsi/layanan | Input | Output |
|---|---|---|---|
| A1 | `load_event_log(path)` | path XES | `EventStore` atau error terstruktur |
| A1 | `get_overview(store)` | `EventStore` | KPI, aktivitas, rentang waktu dan metadata |
| A2 | `get_case_durations(store)` | `EventStore` | case ID + `duration_days` dari trace lengkap |
| A2 | `run_11_7(store)` | `EventStore` | 5 `AnalysisResult` |
| A3 | `run_11_15(store, activity_name)` | store + target aktual | 1 `AnalysisResult` |
| A3 | `run_11_18(store, activity_name)` | store + target aktual | 1 `AnalysisResult` |
| A4 | `run_11_22(store)` | `EventStore` | 1 `AnalysisResult` dengan pasangan bukti |
| A4 | `get_case_trace(store, case_id)` | store + case ID | events untuk case, urut `_trace_pos` |
| A5 | `export_results(results, output_dir)` | hasil dan path | CSV summary, cases, evidence |

Jika `run_11_7` dipisah menjadi lima fungsi internal, tetap sediakan satu wrapper agar GUI dan tes mudah melakukan satu panggilan konsisten. Error yang bukan hasil analisis (I/O, XES corrupt) boleh dilempar sebagai exception dan ditangkap GUI untuk pesan pengguna.

## 5. Spesifikasi algoritma yang dapat diuji

### 5.1. Common rules

- Untuk suatu case `c`, `duration_days(c) = (max_timestamp(c) - min_timestamp(c)).total_seconds() / 86400`.
- Filter `contains(A)` adalah `set(case_id)` dari event aktivitas A; bukan jumlah baris event.
- Filter `endpoint(A)` mengambil **event terakhir menurut `_trace_pos`** di masing-masing case, kemudian memeriksa activity A.
- Sebelum rata-rata kelompok, pilih case ID, **bukan** membuang event awal/akhir case.
- Untuk mean kelompok kosong, keluarkan `None/N/A`, bukan `NaN` di GUI atau CSV.
- Setiap operasi yang membutuhkan lifecycle dan resource memperlakukan atribut hilang secara eksplisit.

### 5.2. Exercise 11.7

| Subsoal | Case terpilih | Result |
|---|---|---|
| A | Semua case | `count=n_cases`, `denominator=n_cases`. |
| B | Semua case | `mean_days=mean(duration_days all cases)`; `count=n_cases`. |
| C | `contains("O_Accepted")` | Count unik + mean case lengkap + proof. |
| D | `contains("O_Refused")` | Count unik + mean case lengkap + proof. |
| E | `endpoint("O_Cancelled")` | Count unik + mean case lengkap + event terakhir. |

11.7 C dan D dapat tumpang tindih. 11.7 E bukan sekadar “pernah cancel”. Jangan menyamakan `O_Accepted` dengan `A_Accepted`.

### 5.3. Exercise 11.15 / 11.18

1. Temukan label fraud yang ada secara **aktual** dalam dataset. Contoh dari materi: `W_Assess potential fraud`; jangan menganggap string contoh cocok secara case-sensitive tanpa inspeksi.
2. Ambil `concept:name == activity_name` **dan** lifecycle yang dapat dibuktikan ekuivalen `complete`.
3. Jika lifecycle hilang/tidak dapat dipetakan secara sah, tandai analisis sebagai `unavailable`, bukan menghitung semua event fraud sebagai complete.
4. Untuk 11.15, group complete events per case, ambil `count >= 2`. Jumlah hasil adalah **jumlah case**, bukan jumlah event.
5. Untuk 11.18, buang resource null/blank, group complete events per `(case_id, resource)`; ambil group `count >= 2`; deduplikasi case ID bila ada beberapa resource memenuhi syarat.
6. Untuk 11.18 jika resource field **sama sekali tidak ada**, hasil `unavailable`; jika field ada tetapi resource tertentu null, abaikan null tanpa menganggap semuanya sama.
7. Jangan memasangkan `start` dan `complete` sebagai dua penyelesaian; tiap event `complete` yang sah dihitung sekali.

### 5.4. Exercise 11.22

```text
Untuk tiap case:
    cancel_positions = posisi event O_Cancelled
    accept_positions = posisi event O_Accepted
    match = keduanya tidak kosong DAN min(cancel_positions) < max(accept_positions)
    bila match: pilih SATU pasangan event nyata (i, j) dengan i < j
count = jumlah case unik yang match
percentage = 100 * count / total_case_aktif (jika > 0)
```

`O_Cancelled → X → O_Accepted` **lolos**. `O_Accepted → O_Cancelled` dan tidak ada accepted kemudian **tidak lolos**. Dua kejadian tidak harus offer ID sama. Jangan mengubah jawaban case-level menjadi offer-level.

### 5.5. Angka acuan yang hanya untuk validasi

| Soal | Referensi slide dosen | Catatan |
|---|---|---|
| 11.7 A | 31.509 case | Bukan konstanta jawaban. |
| 11.7 B | 21,9 hari | Perhatikan pembulatan. |
| 11.7 C | 17.228 case, 18,1 hari | Contains. |
| 11.7 D | 3.720 case, 16,8 hari | Contains. |
| 11.7 E | 4.436 case, 23 hari | Endpoint. |
| 11.15 | 13 case | Complete-only, jangan ikut hasil Disco 20 dengan semantik berbeda. |
| 11.18 | 3 case | Complete-only + same resource, bukan hasil Disco 8 dengan semantik berbeda. |
| 11.22 | Tidak tersedia | Wajib dihitung dari dataset aktual. |

Jika hasil tidak cocok, log dataset/hash, definisi label, mapping lifecycle, trace order, dan sample case evidence. Jangan “mengakali” filter supaya angka sama referensi.

## 6. Spesifikasi GUI desktop

**Teknologi pilihan bersama:** Python + PM4Py + pandas + **PySide6** + pytest. `requirements.txt` harus memuat versi yang benar-benar diuji dan dapat diinstal; jangan menebak pin versi sebelum percobaan di environment tim. Dokumen dosen membolehkan alternatif GUI, tetapi perubahan stack harus disetujui semua anggota di D1.

**Alur wajib:** pilih XES → status pemrosesan → overview → pilih latihan → jalankan → ringkasan (aturan, count, mean/persen) → daftar case → buka Case Explorer dengan event tersorot → ekspor CSV.

| Area | Panel | Owner | Komponen wajib |
|---|---|---|---|
| Dataset & status | file picker + status banner | A1 + shell A5 | filename, error, progress, atribut, count |
| Overview | `OverviewPanel` | A1 | KPI, frekuensi activity, cycle time, daftar case |
| Exercise 11.7 | `Exercise117Panel` | A2 | lima hasil, rule, count, mean, daftar, case action |
| Rework | `ReworkPanel` | A3 | status lifecycle, 11.15/18, resource, evidence |
| Ordering | `SequencePanel` | A4 | 11.22 count/percent/denominator, pasangan |
| Case Explorer | `CaseExplorerPanel` | A4 | search case, trace utuh, `_trace_pos`, highlight |
| Export/About | shared controls | A5 | CSV, reset/rerun, versi Python/PM4Py/OS |

Semua tabel besar memakai model data yang bisa mencari/memfilter/paging, tidak membuat jutaan `QTableWidgetItem` sekaligus.

### 6.1. Worker / responsivitas

- Import dan analisis berat berjalan di worker, **bukan** di GUI/main thread.
- Worker mengirim signal status/progress, result, error; UI update hanya dari thread UI.
- Kelola referensi worker dan thread per tugas secara aman; hindari overwriting `self.thread` saat tugas sebelumnya masih aktif.
- Gunakan pola `QObject.moveToThread(QThread)` dan cleanup dengan `quit()/deleteLater()` sesuai dokumentasi Qt.
- Jika progress kuantitatif belum tersedia, tampilkan status **indeterminate** secara jujur, bukan persentase palsu.
- Dataset switch harus menghapus hasil sebelumnya dan memberi `dataset_id`/generation untuk menolak hasil worker lama.

### 6.2. Export CSV

Minimal tiga keluaran **dengan judul kolom dan UTF-8**: `summary.csv` (8 hasil, rule, count, denominator, mean, persentase, status), `selected_cases.csv` (exercise_id, case_id), `evidence.csv` (exercise, case_id, event/posisi/atribut bukti). Untuk hasil `unavailable`, tulis status/notes jelas; jangan isi angka 0 seolah valid. Tawarkan lokasi output pilihan pengguna, tangani permission failure, dan cek bahwa file hasil bisa dibaca ulang.

## 7. Testing: 15 scenario minimum

| ID | Fixture | Kondisi yang harus benar | Owner utama |
|---|---|---|---|
| T01 | `O_Accepted` dua kali pada satu case | 11.7 C = satu case | A2 |
| T02 | `O_Cancelled` di tengah | 11.7 E menolak case | A2 |
| T03 | `O_Refused` dan `O_Accepted` di case sama | 11.7 C dan D sama-sama dapat memilih | A2 |
| T04 | Fraud schedule dua kali, complete sekali | 11.15 tidak lolos | A3 |
| T05 | Fraud complete dua kali oleh dua resource berbeda | 11.15 lolos, 11.18 tidak | A3 |
| T06 | Fraud complete dua kali oleh satu resource | 11.15 dan 11.18 lolos | A3 |
| T07 | Cancel → aktivitas lain → Accept | 11.22 lolos | A4 |
| T08 | Accept → Cancel, tanpa Accept sesudahnya | 11.22 tidak lolos | A4 |
| T09 | Resource null/blank dua complete | 11.18 tidak lolos | A3 |
| T10 | Lifecycle tidak dapat diverifikasi | 11.15/18 unavailable, bukan zero valid | A3 |
| T11 | Dua timestamp identik | endpoint/order sesuai trace asli | A1 + A4 |
| T12 | Case hanya satu event | durasi = 0 hari | A2 |
| T13 | XES corrupt/atribut wajib hilang | pesan error, GUI tidak crash | A1 + A5 |
| T14 | Banyak pasangan cancel→accept dalam satu case | 11.22 menghitung satu case; evidence sah | A4 |
| T15 | Log kosong | tidak divide by zero; status jelas | A1 + A5 |

Tambahan *integration/smoke tests*: load → seluruh panel → evidence → reset/rerun → export; impor ulang menghasilkan hasil sama; dataset invalid tidak menampilkan hasil dataset sebelumnya; `summary.csv` dapat dibaca. `pytest -q` harus lulus **sebelum** merge.

## 8. Jadwal 7 hari dan gate integrasi

| Hari | Gate akhir hari | Semua anggota wajib memverifikasi |
|---|---|---|
| **D1** | Repo dan kontrak `EventStore`/`AnalysisResult` disetujui; contoh XES terbaca | A1 schema, A2–A4 fixture/signature, A5 skeleton/panel API |
| **D2** | Analitik inti hidup pada fixture sintetis | Core tiap modul bisa dipanggil tanpa GUI |
| **D3** | Delapan fungsi dan panel utama tersedia, unit tests inti lulus | PR masing-masing dan demo panel |
| **D4** | Demo sintetis end-to-end: import → result → evidence → export | Tidak boleh menunggu D6 untuk integrasi |
| **D5** | Jalankan BPIC17 asli; simpan hasil dan analisis selisih | Validasi bersama, tidak hard-code |
| **D6** | Perbaiki bug, regression, screenshot, laporan, packaging; *feature freeze* | Tidak ada bug kritis atau failing test wajib |
| **D7** | Clean-install, demo, finalisasi laporan, checklist, pengumpulan | Semua orang hadir dan menguasai alur umum |

Daily sync 15–20 menit dan PR kecil harian. Saat blocker > satu sesi kerja, lapor pada hari yang sama dan minta reviewer silang; semua fitur opsional ditunda.

## 9. Pembagian kerja, antarmuka, dan tugas bersama

| Anggota | Pekerjaan program (owner) | Reviewer silang | Bagian laporan/hasil non-program |
|---|---|---|---|
| A1 | F01–F02; loader; EventStore; overview; worker | A4 | Pendahuluan bersama A5, data & arsitektur, screenshot import/overview |
| A2 | F03; duration; 11.7 A–E; panel | A3 | Metode/hasil 11.7, screenshot jawaban, review A3 |
| A3 | F04–F05; lifecycle; 11.15/11.18; panel | A2 | Metode/hasil rework, evidence lifecycle/resource, review A2 |
| A4 | F06 + Case Explorer; 11.22; timeline; panel | A1 | Metode/hasil ordering, screenshot evidence dan explorer, review A1 |
| A5 | Shell, reusable GUI, CSV, About, integration, packaging | Semua | Pendahuluan bersama A1, penggabungan dokumen, ekspor, demo, reviewer integrasi |

**Wajib semua:** rapat D1, test sintetis + BPIC17, tulis dokumentasi modul dan satu bukti case, screenshot panel sendiri, kontribusi nyata di laporan, peer review naskah, presentasi 1 segmen per orang, evaluasi dan persetujuan final. **Koordinator dokumen tidak bertanggung jawab menulis seluruh laporan.**

## 10. Git, interoperabilitas agent, dan pemisahan berkas

- Branch: `feat/loader`, `feat/ex-11-7`, `feat/rework`, `feat/ordering`, `feat/gui-shell`.
- Setiap PR menjelaskan *apa yang berubah*, *bukti test*, *dampak API*, dan *screenshot jika GUI*.
- Minimal satu reviewer silang; jangan commit langsung ke main tanpa review.
- `.gitignore`: `data/*.xes`, `data/*.xes.gz`, `.venv/`, `__pycache__/`, `.pytest_cache/`, file sementara, credential.
- Jangan commit dataset asli, hasil berisi data sensitif, atau lokasi file privat.
- Rekam Python, PM4Py, pandas, PySide6, pytest, OS, hash dataset, dan commit/tag `v1.0-tahap1` saat final.

### 10.1. Instruksi wajib untuk coding agent

```text
Anda bekerja pada repository aplikasi desktop BPIC17 Tahap 1.
Baca berurutan: 01_PANDUAN_KERJA_IDENTIK_PDF.md, 02_DOKUMENTASI_TEKNIS.md,
lalu file anggota yang menjadi scope tugas.
Jangan mengubah definisi 8 soal/F01–F07, jangan memasukkan discovery algorithms.
Implementasi hanya pada file milik anggota kecuali diminta perubahan API.
Jangan membuat angka jawaban statis, dataset palsu sebagai hasil BPIC17 asli,
atau mengganti hasil unavailable dengan angka nol.
Jangan mengasumsikan urutan timestamp adalah urutan trace XES.
Jangan mengubah kontrak EventStore/AnalysisResult tanpa review tim.
Sebelum coding: tulis rencana file yang disentuh dan pengujian yang disiapkan.
Sesudah coding: jalankan pytest yang relevan; laporkan hasil nyata,
file berubah, potensi risiko, dan langkah integrasi.
Jika file XES asli belum tersedia: pakai log sintetis untuk unit test,
jelaskan bahwa hasil BPIC17 asli BELUM diverifikasi.
```

Jika agent terpisah bekerja paralel, berikan **satu file anggota** sebagai scope dan batasi edit path untuk menghindari konflik. Instruksi dalam dokumen ini ditujukan untuk kerja proyek, bukan izin membaca atau mengubah berkas di luar repository.

## 11. Pembuktian, dokumentasi, dan paket akhir

**Laporan kelompok** minimal berisi: pendahuluan/sumber XES; mapping soal→fungsi; definisi semantik; arsitektur PM4Py/GUI; delapan hasil aktual (jika sudah di-run); evidences per kasus; T01–T15; perbandingan materi; kendala dan limitasi; kontribusi A1–A5. Semua anggota memberi konten, meninjau, dan menyetujui.

**Skenario demo**: A1 impor+overview → A2 11.7 A–E → A3 11.15/18 → A4 11.22+Case Explorer → A5 CSV/reset/About. Screenshot seluruh menu dan minimal satu case nyata untuk 11.15, 11.18, 11.22. Semua anggota harus bisa menjawab pertanyaan lintas modul.

**Paket serah:** aplikasi desktop dapat dijalankan di mesin lain; source modular, `requirements.txt`, `README.md`, bukti validasi dan versi/hash, screenshot, laporan, demo atau rekaman, serta daftar kontribusi. Dataset besar boleh tidak dilampirkan; catat versi dan sumber.

## 12. Checklist review teknis sebelum merge/final

- [ ] PM4Py benar-benar dipakai membaca log.
- [ ] Atribut wajib tervalidasi; error import tidak merusak state aplikasi.
- [ ] Event order XES dan `_trace_pos` dapat dipertanggungjawabkan.
- [ ] Duration dari trace lengkap dan mean benar, tanpa event filter mengubah durasi.
- [ ] 11.7 C/D tidak eksklusif, 11.7 E endpoint benar.
- [ ] 11.15 complete-only; 11.18 complete-only + resource nonblank sama.
- [ ] 11.22 i<j, kasus unik, denominator dan pasangan bukti tampil.
- [ ] Evidence event bisa ditelusuri ke Case Explorer.
- [ ] Worker tidak membekukan GUI; state reset dan dataset switching aman.
- [ ] T01–T15 diperiksa, test integration dan export valid.
- [ ] Tidak ada angka hasil BPIC17 dipaksakan dari slide.
- [ ] Semua anggota telah menyumbang laporan, screenshot, review, dan demo.

## 13. Referensi resmi teknis

- PM4Py: https://processintelligence.solutions/pm4py/api/
- PM4Py membaca event data: https://processintelligence.solutions/pm4py/examples/handling-event-data
- PM4Py source/getting started: https://github.com/process-intelligence-solutions/pm4py/blob/release/docs/source/getting_started.rst
- Qt for Python dan lifecycle threads: https://doc.qt.io/qtforpython-6/overviews/qtdoc-threads-qobject.html
- Dataset BPI Challenge 2017: https://data.4tu.nl/articles/dataset/BPI_Challenge_2017/12696884

> **Batas verifikasi:** dokumen ini merancang metode dan kriteria. Keluaran numerik nyata, kemampuan impor pada mesin tim, serta kecocokan versi dependency **baru dapat dinyatakan berhasil setelah program dan file XES benar-benar dijalankan**.
