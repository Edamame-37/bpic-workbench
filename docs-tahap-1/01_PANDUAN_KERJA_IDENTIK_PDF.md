**PANDUAN FINAL  
PROYEK TAHAP 1**

**APLIKASI DESKTOP ANALISIS EVENT LOG BPIC17**

*Python · PM4Py · GUI Desktop*

| **PARAMETER**  | **KEPUTUSAN PROYEK**                                             |
|----------------|------------------------------------------------------------------|
| Durasi         | 7 hari kalender berturut-turut, D1–D7                            |
| Tim            | 5 anggota (menunggu persetujuan bila aturan resmi tetap 4 orang) |
| Ruang lingkup  | 8 butir jawaban latihan; fitur F01–F07; evidence; ekspor CSV     |
| Metode         | Modul independen, integrasi sejak dini, pengujian berlapis       |
| Status dokumen | Revisi komprehensif atas Panduan Proyek Datmin.pdf               |
| Tanggal acuan  | 20 November 2026                                                 |

> **CATATAN KEPATUHAN** Dokumen instruksi dosen versi 16 November 2026 menetapkan kelompok 4 mahasiswa. Panduan ini disusun untuk kondisi nyata tim 5 orang atas permintaan kelompok; konfirmasi izin jumlah anggota kepada dosen tetap harus dilakukan.

Fokus utama: seluruh jawaban dihitung dari berkas XES yang dipilih pengguna, bukan disalin dari angka referensi. Hasil harus dapat diverifikasi melalui daftar case, event pembukti, serta pengujian yang bisa diulang.

# Peta dokumen

01\. Keputusan, sumber acuan, dan cakupan

02\. Delapan soal dan aturan operasional

03\. Fitur F01–F07 dan rancangan UI

04\. Arsitektur, format data, dan kontrak modul

05\. Panduan algoritma dan implementasi

06\. Pembagian kerja 5 anggota dan beban terukur

07\. Pekerjaan non-program dikerjakan bersama

08\. Timeline penyelesaian 7 hari

09\. Kolaborasi Git, dependensi, dan kontrol perubahan

10\. Pengujian, validasi BPIC17, dan kriteria penerimaan

11\. Pengumpulan, demonstrasi, risiko, dan referensi

Lampiran A–D: matriks ketertelusuran, template hasil, checklist, contoh uji

> **CARA MENGGUNAKAN** Hari 1: baca bagian 01–04, sepakati kontrak, pilih pemilik tugas. Selama D2–D6: gunakan bagian 05–10 untuk implementasi dan kontrol mutu. Hari 7: gunakan checklist bagian 11 dan lampiran untuk pemeriksaan final.

# 01. Keputusan proyek dan sumber acuan

## 1.1. Tujuan dan batasan Tahap 1

Mengembangkan aplikasi GUI desktop menggunakan Python dan PM4Py yang mengimpor event log BPIC17 berformat XES, menghitung jawaban soal Bab 11, menjelaskan filter, menampilkan evidence level case/event, serta mengekspor hasil. Aplikasi harus dapat digunakan tanpa membuka notebook atau mengubah source code.

| **Masuk cakupan (wajib)**                      | **Di luar cakupan (Tahap 1)**                             |
|------------------------------------------------|-----------------------------------------------------------|
| Impor XES, validasi, ringkasan log, cycle time | Alpha Miner, Heuristics Miner, Inductive Miner            |
| Exercise 11.7 A–E, 11.15, 11.18, 11.22         | Petri net discovery; replika dashboard Disco/Celonis      |
| Case Explorer, event evidence, ekspor CSV      | Prediksi ML, process enhancement, analisis offer ID wajib |
| Uji sintetis, uji BPIC17, dokumentasi, demo    | Visualisasi DFG / PDF otomatis: hanya opsi bila sempat    |

## 1.2. Urutan otoritas dokumen

> 1\. Instruksi Proyek Tahap 1 – Analisis Soal BPIC17 PM4Py, versi 16 November 2026: acuan tertinggi ruang lingkup dan kriteria penerimaan.
>
> 2\. BPIC-2017.pdf dari dosen: sumber definisi latihan dan angka pembanding historis.
>
> 3\. Panduan Proyek Datmin.pdf (34 halaman): dokumen kerja lama yang dievaluasi dan diperbaiki di sini.
>
> 4\. Dokumentasi resmi PM4Py dan laman dataset 4TU: referensi API dan format data, bukan pengganti ketentuan soal.

## 1.3. Keputusan yang wajib disepakati saat kickoff

| **ID** | **Keputusan**   | **Standar yang dipilih**                                                                                                                            |
|--------|-----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| K01    | Jumlah anggota  | 5 orang dalam rencana kerja; pastikan dosen mengizinkan penyimpangan dari ketentuan 4 orang.                                                        |
| K02    | Durasi          | 7 hari kalender berturut-turut; D7 adalah akhir pengerjaan, tanpa fase tambahan.                                                                    |
| K03    | GUI             | PySide6 (boleh diubah bersama sebelum implementasi).                                                                                                |
| K04    | Format internal | pandas DataFrame hasil pembacaan PM4Py + indeks trace dan metadata.                                                                                 |
| K05    | Urutan event    | Urutan per-trace sebagaimana dibaca dari XES; timestamp dipakai sebagai data waktu. Tie tidak boleh diurutkan sembarang.                            |
| K06    | Lifecycle       | Complete-only memerlukan evidence transition=complete atau aturan ekuivalen yang dibuktikan dari file; jika tidak tersedia, jangan mengarang hasil. |
| K07    | Sumber angka    | Perhitungan dinamis dari dataset aktif. Angka slide hanya untuk validasi.                                                                           |
| K08    | Integrasi       | PR kecil setiap hari; fitur disebut selesai hanya jika kode, panel, bukti, dan tes sudah terintegrasi.                                              |

# 02. Delapan soal wajib dan definisi operasional

## 2.1. Definisi yang tidak boleh tertukar

| **Istilah**         | **Definisi yang digunakan**                                                                                                                                  |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Case / trace        | Satu instance proses; sekumpulan event yang berada dalam satu trace/case ID.                                                                                 |
| Event               | Satu catatan kejadian dengan aktivitas, timestamp, dan atribut relevan.                                                                                      |
| Activity            | Nilai concept:name. Periksa variasi kapitalisasi dan atribut lifecycle:transition.                                                                           |
| Case duration       | max(timestamp) − min(timestamp) seluruh event dalam case; dalam hari = detik / 86.400. Jika log sudah berurutan kronologis, setara event terakhir − pertama. |
| Contains            | Sebuah case lolos bila minimal satu event beraktivitas target muncul. Tiap case dihitung sekali.                                                             |
| Endpoint            | Aktivitas event paling akhir menurut urutan trace asli. Jangan ganti dengan sekadar pernah muncul.                                                           |
| Complete occurrence | Event target dengan lifecycle yang menunjukkan status selesai; schedule/start/abort tidak dihitung.                                                          |
| Same resource       | Minimal dua complete occurrences dalam case oleh resource teridentifikasi yang sama; null / string kosong dikecualikan.                                      |
| Eventually follows  | Ada posisi event i \< j dalam trace; event i beraktivitas A dan event j beraktivitas B, tidak harus bertetangga.                                             |
| Persentase 11.22    | (jumlah case cocok / jumlah seluruh case log aktif) × 100%; denominator tampil jelas.                                                                        |

> **PERHATIAN** Untuk 11.7 C dan 11.7 D, kelompok successful dan unsuccessful tidak harus saling eksklusif. Satu aplikasi dapat memiliki beberapa offer dengan hasil berbeda; jangan memaksa total keduanya menjadi 31.509.

## 2.2. Matriks kebutuhan delapan jawaban

| **Soal** | **Kondisi pemilihan case**                              | **Output minimum**                            | **Owner** |
|----------|---------------------------------------------------------|-----------------------------------------------|-----------|
| 11.7 A   | Seluruh case unik dalam log aktif                       | Total cases; daftar case bila dibuka          | A2        |
| 11.7 B   | Seluruh case; durasi trace utuh                         | Mean cycle time (hari); jumlah case           | A2        |
| 11.7 C   | Contains O_Accepted                                     | Count + mean hari + case IDs + evidence       | A2        |
| 11.7 D   | Contains O_Refused                                      | Count + mean hari + case IDs + evidence       | A2        |
| 11.7 E   | Event terakhir tepat O_Cancelled                        | Count + mean hari + endpoint evidence         | A2        |
| 11.15    | W_Assess potential fraud complete \>= 2 dalam satu case | Count + total complete per case + event bukti | A3        |
| 11.18    | Minimal dua complete target oleh resource sama          | Count + resource ID + event pembukti          | A3        |
| 11.22    | Ada O_Cancelled pada i diikuti O_Accepted pada j\>i     | Count + persen + denominator + pasangan event | A4        |

## 2.3. Angka referensi dari materi dosen (bukan konstanta program)

| **Soal** | **Acuan historis**      | **Catatan**                                                                   |
|----------|-------------------------|-------------------------------------------------------------------------------|
| 11.7 A   | 31.509 cases            | Data asli BPI Challenge 2017.                                                 |
| 11.7 B   | 21,9 hari               | Mean durasi seluruh case.                                                     |
| 11.7 C   | 17.228 cases; 18,1 hari | Contains O_Accepted.                                                          |
| 11.7 D   | 3.720 cases; 16,8 hari  | Contains O_Refused.                                                           |
| 11.7 E   | 4.436 cases; 23 hari    | Endpoint O_Cancelled.                                                         |
| 11.15    | 13 cases                | Complete-only pada solusi Celonis; 20 pada filter Disco yang tidak ekuivalen. |
| 11.18    | 3 cases                 | Complete-only, same resource; 8 pada filter Disco yang tidak ekuivalen.       |
| 11.22    | Tidak diberikan         | Wajib dihitung dari file XES. Jangan mengarang nilai.                         |

Apabila hasil berbeda dari acuan, laporkan dataset, nama aktivitas, lifecycle, urutan trace, rumus metrik, dan 1–3 case pembukti. Selisih tidak boleh diselesaikan dengan hard-code angka atau mengganti definisi diam-diam.

# 03. Fitur F01–F07 dan rancangan antarmuka

| **Fitur**             | **Kewajiban minimum**                                                                                                   | **Bukti di GUI**                                            |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| F01 – Import          | Pilih .xes; parsing PM4Py; validasi case ID, concept:name, time:timestamp; deteksi lifecycle dan resource; pesan error. | Nama berkas, status, jumlah case/event, atribut, log error. |
| F02 – Overview        | Total case/event, frekuensi aktivitas, rentang waktu, mean cycle time, pencarian case.                                  | Kartu KPI, tabel aktivitas dan durasi per case.             |
| F03 – Exercise 11.7   | 5 soal; contains vs endpoint; mean dari trace utuh; daftar case.                                                        | Result cards, rule text, count, mean, tombol bukti.         |
| F04 – Exercise 11.15  | Complete-only, repeated occurrences \>= 2.                                                                              | Case ID, count complete, daftar event terpilih.             |
| F05 – Exercise 11.18  | Repeat complete oleh resource sama; null tidak lolos.                                                                   | Case ID, resource valid, count, pasangan bukti.             |
| F06 – Exercise 11.22  | Eventually follows; count, persen dan denominator.                                                                      | Pasangan event i\<j, timestamp, trace.                      |
| F07 – Explorer/export | Cari case; detail event; rerun/reset; ekspor CSV ringkasan/cases/evidence.                                              | Tabel berpenelusuran; file CSV bisa dibuka.                 |

## 3.1. Alur UX minimum

> **USER JOURNEY** Pilih berkas XES → status & validasi → Overview → pilih latihan → jalankan/lihat hasil → klik case evidence → periksa trace → ekspor CSV. Tombol reset/rerun tidak boleh memaksa impor ulang.

## 3.2. Desain tujuh area aplikasi

| **Area**           | **Komponen**                                               | **Pemilik panel** |
|--------------------|------------------------------------------------------------|-------------------|
| Dataset & Status   | File picker, spinner/progress, error message, metadata log | A1 (shell A5)     |
| Overview           | KPI log, frekuensi activity, daftar durasi case            | A1                |
| Exercise 11.7      | Subtab A–E, rule, count, mean, case table                  | A2                |
| Rework 11.15/11.18 | Lifecycle notice, counts, resource evidence, case table    | A3                |
| Sequence 11.22     | Count, persen, denominator, event pair timeline            | A4                |
| Case Explorer      | Cari case ID, semua event, sorot event pembukti            | A4                |
| Export / About     | Summary/case/evidence CSV, metadata versi, petunjuk        | A5                |

Seluruh tabel besar harus memiliki pencarian, pagination/virtualized loading bila diperlukan. Hindari memuat jutaan baris langsung ke widget tabel.

# 04. Arsitektur, data, dan kontrak modul

## 4.1. Alur sistem

> **PIPELINE** BPIC17 .xes → PM4Py parser → Validated EventStore (DataFrame + trace order + case index) → Analytics Services → AnalysisResult → GUI panels / Case Explorer / CSV export.

## 4.2. Struktur repository final

```text
bpic17-desktop/
├── README.md
├── requirements.txt
├── pyproject.toml              # opsional; standar lint/test
├── .gitignore
├── data/                       # XES asli TIDAK di-commit
├── src/
│   ├── main.py
│   ├── core/
│   │   ├── loader.py           # A1: PM4Py + validasi
│   │   ├── event_store.py      # A1: trace index + metadata
│   │   ├── overview.py         # A1: metrik log
│   │   ├── cycle_time.py       # A2: durasi case
│   │   ├── ex_11_7.py          # A2
│   │   ├── rework.py           # A3: complete-only, resource
│   │   ├── ex_11_15_18.py      # A3
│   │   ├── ordering.py         # A4: event pair i<j
│   │   ├── ex_11_22.py         # A4
│   │   ├── result.py           # kontrak lintas modul
│   │   └── export.py           # A5: CSV
│   └── gui/
│       ├── main_window.py      # A5: shell/navigasi
│       ├── worker.py           # A1 + A5: thread aman
│       ├── common/             # A5: widget reusable
│       └── panels/             # A1–A4: tiap panel pemilik
├── tests/
│   ├── fixtures.py
│   ├── test_loader.py
│   ├── test_11_7.py
│   ├── test_rework.py
│   ├── test_ordering.py
│   └── test_integration.py
└── docs/
    ├── laporan.md
    ├── hasil_validasi.csv
    ├── screenshots/
    └── pembagian_kontribusi.md
```

## 4.3. Kontrak EventStore

Parser melalui pm4py.read_xes(path). Jika hasil berupa EventLog, konversi ke DataFrame; jika sudah DataFrame, gunakan salinannya. Seluruh modul memakai satu skema internal, tidak melakukan parsing ulang sendiri.

| **Kolom / metadata** | **Sifat**      | **Aturan**                                                                     |
|----------------------|----------------|--------------------------------------------------------------------------------|
| case:concept:name    | Wajib          | Identitas case harus non-null; pertahankan string aslinya.                     |
| concept:name         | Wajib          | Nama aktivitas tidak boleh null.                                               |
| time:timestamp       | Wajib          | Datetime aware bila disediakan; jangan ubah zona waktu tanpa catatan.          |
| lifecycle:transition | Opsional       | Jika tak ada, berikan status tidak terverifikasi untuk soal complete-only.     |
| org:resource         | Opsional       | Blank / null tidak valid untuk same-resource.                                  |
| \_trace_pos          | Internal wajib | Posisi event dalam trace dari urutan XES; gunakan untuk endpoint dan ordering. |
| \_row_id             | Internal wajib | ID event stabil untuk evidence dan highlighting.                               |
| case_durations       | Cache          | Tabel 1 baris per case: timestamp_min, timestamp_max, duration_days.           |

PERINGATAN: penetapan \_trace_pos harus dilakukan saat data XES pertama kali dimuat, berdasarkan urutan per trace yang sebenarnya. Tidak boleh mengasumsikan bahwa sorting berdasarkan timestamp secara otomatis mereproduksi urutan log ketika timestamp identik.

## 4.4. Kontrak AnalysisResult

```python
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
    status: str = "ok"             # ok / unavailable / error
    notes: str = ""
```

Kontrak tunggal dipakai oleh setiap modul, panel, Case Explorer, pengujian, dan ekspor. Untuk 11.7 A/B, properti yang tidak relevan boleh bernilai None. Event evidence hanya disimpan untuk case terpilih, bukan salinan seluruh log.

## 4.5. Aturan input dan output

- Satu case yang memenuhi filter dihitung satu kali, berapa pun jumlah event pemicunya.

- Daftar case terpilih selalu merujuk case dalam log aktif; denominator dihitung dari seluruh case log aktif sebelum filter soal.

- Case duration selalu berasal dari trace utuh walaupun evidence hanya sebagian event.

- Persentase 11.22 memakai count / denominator × 100 dengan pembagian nol ditangani secara eksplisit.

- Jika atribut esensial tidak tersedia, sediakan status unavailable beserta alasan; jangan kembalikan angka 0 sebagai hasil seolah valid.

# 05. Rancangan algoritma dan implementasi

## 5.1. Parsing XES dan eksplorasi aktivitas

```python
import pm4py
import pandas as pd

def import_xes(path: str) -> pd.DataFrame:
    obj = pm4py.read_xes(path)
    if isinstance(obj, pd.DataFrame):
        df = obj.copy()
    else:
        df = pm4py.convert_to_dataframe(obj)
    required = {"case:concept:name", "concept:name", "time:timestamp"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Atribut wajib hilang: {missing}")
    if df[list(required)].isna().any().any():
        raise ValueError("Ada nilai kosong pada atribut wajib")
    return df
```

Catatan: contoh ini menjelaskan validasi minimal. Implementasi final A1 juga wajib membuat posisi trace, kebijakan timezone, cache durasi, penanganan file rusak, dan metadata versi. File .xes.gz boleh didukung sebagai bonus jika pembaca PM4Py pada versi terpilih kompatibel.

## 5.2. Exercise 11.7 (A–E)

> 1\. Hitung case durations sekali dari seluruh event per case: timestamp maksimum dikurangi minimum, lalu konversi ke hari.
>
> 2\. 11.7 A: count unique case; 11.7 B: mean duration seluruh case.
>
> 3\. 11.7 C: pilih case dengan minimal satu event O_Accepted; 11.7 D dengan O_Refused. Tidak eksklusif.
>
> 4\. 11.7 E: ambil event terakhir menurut \_trace_pos, lalu pilih case yang berakhir O_Cancelled.
>
> 5\. Untuk setiap subset, mean dihitung dari daftar durasi case utuh, bukan dari event yang difilter.

```python
# sketsa ekspresi, diasumsikan EventStore sudah tervalidasi
all_ids = set(df["case:concept:name"])
accepted_ids = set(df.loc[df["concept:name"] == "O_Accepted",
                          "case:concept:name"])
refused_ids  = set(df.loc[df["concept:name"] == "O_Refused",
                          "case:concept:name"])
sorted_df = df.sort_values(
    ["case:concept:name", "_trace_pos"], kind="stable"
)
ends = sorted_df.groupby("case:concept:name", sort=False).tail(1)
expired_ids = set(ends.loc[ends["concept:name"] == "O_Cancelled",
                           "case:concept:name"])
```

## 5.3. Exercise 11.15 dan 11.18

> 1\. Cari aktivitas target sesuai nama yang benar-benar ada pada dataset; catat label asli, termasuk kapitalisasi.
>
> 2\. Ambil event hanya dengan lifecycle=complete. Apabila atribut tidak ada/tidak tegas, hentikan hasil tersebut sebagai unavailable hingga pemetaan data dibuktikan.
>
> 3\. 11.15: group berdasarkan case ID, hitung complete occurrences target; pilih yang jumlahnya \>= 2.
>
> 4\. 11.18: dari complete events yang sama, buang resource null/blank; group berdasarkan (case ID, resource), pilih pasangan dengan count \>= 2, lalu deduplikasi case ID.
>
> 5\. Simpan baris bukti persis dari kelompok yang memenuhi syarat; 11.18 harus menunjukkan ID resource dan dua event bersangkutan.

```python
# DataFrame sub = event target yang statusnya terverifikasi complete
counts_15 = sub.groupby("case:concept:name").size()
ids_15 = set(counts_15[counts_15 >= 2].index)

valid = sub[sub["org:resource"].notna()].copy()
valid["org:resource"] = valid["org:resource"].astype("string").str.strip()
valid = valid[valid["org:resource"].ne("")]
counts_18 = valid.groupby(["case:concept:name", "org:resource"]).size()
ids_18 = {case_id for case_id, resource in counts_18[counts_18 >= 2].index}
```

## 5.4. Exercise 11.22

> 1\. Per case, tentukan posisi terawal O_Cancelled dan posisi terakhir O_Accepted. Jika min(cancel) \< max(accept), case memenuhi syarat.
>
> 2\. Untuk evidence yang dapat diaudit, ambil satu pasangan aktual dengan \_trace_pos(cancel) \< \_trace_pos(accept); simpan kedua \_row_id dan timestamp.
>
> 3\. Count dihitung per case; persentase adalah count dibagi seluruh case pada log aktif × 100%.
>
> 4\. Jangan mensyaratkan kedua event berdampingan, offer ID sama, atau O_Cancelled sebagai event terakhir.

```python
# Bentuk kondisi per case, bukan pasangan event yang harus berdampingan
first_c = cancels.groupby("case:concept:name")["_trace_pos"].min()
last_a  = accepts.groupby("case:concept:name")["_trace_pos"].max()
pairs = pd.concat([first_c.rename("cancel"),
                   last_a.rename("accept")], axis=1).dropna()
valid_pairs = pairs[pairs["cancel"] < pairs["accept"]]
case_ids = valid_pairs.index.tolist()
```

## 5.5. Penanganan hasil yang tidak tersedia

Jika log yang diimpor berbeda dari BPIC17 resmi, jumlah dan label event bisa berubah. Aplikasi tetap harus menyajikan hasil berdasarkan log aktif dan dengan jelas menandai jika activity target, lifecycle, atau resource tidak tersedia. Kondisi ini dibedakan dari hasil count=0 yang valid.

# 06. Pembagian kerja 5 anggota (seimbang dan independen)

Strategi: setiap anggota memiliki satu workstream yang mencakup fungsi inti, panel UI, unit test, dan dokumentasi teknis modulnya. A5 membangun komponen UI umum dan mengorkestrasi integrasi, bukan menulis seluruh panel. A1–A4 wajib memasang sendiri panelnya mengikuti template yang sama.

## 6.1. Workstream utama dan estimasi poin

| **Anggota**              | **Ruang lingkup utama**                                                                                 | **Poin** | **Reviewer silang** |
|--------------------------|---------------------------------------------------------------------------------------------------------|----------|---------------------|
| A1 – Data Foundation     | Import XES & atribut (4), EventStore/index (3), overview panel (3), worker/status + tes (2)             | 12       | A4                  |
| A2 – Case Analytics      | Case duration (3), 11.7 A–E (5), panel 11.7 (2), evidence + tes (2)                                     | 12       | A3                  |
| A3 – Rework Analytics    | Lifecycle detection (4), 11.15/11.18 (4), evidence resource (2), panel + tes (2)                        | 12       | A2                  |
| A4 – Sequence & Explorer | 11.22 + persentase (3), event pair evidence (2), Case Explorer (4), panel + tes (3)                     | 12       | A1                  |
| A5 – Application & QA    | Shell & navigasi (3), reusable widgets (3), export CSV (2), packaging/README (2), integration tests (2) | 12       | Semua               |

Poin adalah satuan estimasi relatif untuk pemerataan, bukan jam kerja yang dijamin. Tim bisa mengalihkan tugas melalui rapat singkat bila ditemukan beban aktual tidak seimbang.

## 6.2. Definition of Done per anggota

| **Anggota** | **Minimal dinyatakan selesai apabila…**                                                                                                         |
|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| A1          | BPIC17 dapat diimpor dari GUI; kolom wajib tervalidasi; overview benar; navigasi tidak freeze; tes loader lolos; data contract terdokumentasi.  |
| A2          | Lima subsoal 11.7 memberikan count/mean benar dari trace utuh; panel dan case IDs tampil; T1–T3 dan tes tambahan lolos.                         |
| A3          | 11.15/11.18 memakai complete-only; resource null dikecualikan; evidence jelas; T4–T6 serta tes lifecycle hilang lolos.                          |
| A4          | 11.22 count/persen benar; pasangan i\<j ditandai; Case Explorer bisa mencari case dan melihat event lengkap; T7–T8 lolos.                       |
| A5          | GUI utuh, export summary/cases/evidence berjalan, rerun/reset benar, About/versions, README, integrasi serta packaging diuji pada mesin bersih. |

## 6.3. Penjagaan dependensi

- A1 menyediakan schema EventStore dan sample fixtures pada D1–D2; A2–A4 tetap dapat membuat logic melalui fixture sintetis sebelum file BPIC17 lengkap tersedia.

- A5 menyediakan skeleton GUI, shared widget, dan kontrak signal sejak D1; seluruh panel bisa dikerjakan paralel.

- A2 menyediakan fungsi durasi bersama untuk semua analisis, tetapi API sederhananya disepakati pada D1 agar anggota lain tidak menunggu.

- A4 menentukan skema evidence sejak D1 bersama A3; A5 memakai schema yang sama untuk export.

- Jika sebuah modul terlambat, reviewer silang membantu memperbaiki modul tersebut; tidak menunggu hingga D6.

# 07. Pekerjaan non-program: tanggung jawab bersama

> **PRINSIP WAJIB** Pembuatan laporan, validasi hasil, screenshot, penyusunan presentasi/demo, dan evaluasi akhir dikerjakan bersama oleh KELIMA anggota. Tidak ada satu anggota yang menjadi penanggung jawab tunggal seluruh dokumentasi. Koordinator penggabungan hanya mengatur konsistensi, bukan menanggung seluruh isi.

## 7.1. Pembagian kontribusi penulisan laporan

| **Bagian laporan**                                | **Kontributor utama konten**                   | **Reviewer bersama**       |
|---------------------------------------------------|------------------------------------------------|----------------------------|
| Pendahuluan, tujuan, batasan, sumber dataset      | A1 + A5                                        | A2, A3, A4                 |
| Arsitektur, setup, import XES, data preprocessing | A1                                             | A2 + A5                    |
| Metode & hasil Exercise 11.7                      | A2                                             | A1 + A3                    |
| Metode & hasil Exercise 11.15 / 11.18             | A3                                             | A2 + A4                    |
| Metode & hasil Exercise 11.22 dan Case Explorer   | A4                                             | A3 + A5                    |
| Testing, validasi terhadap referensi, kendala     | Semua: masing-masing modul + integrasi A5      | Seluruh anggota            |
| Kesimpulan, pembahasan keterbatasan, saran        | Ditulis bersama dalam review akhir             | Seluruh anggota            |
| Format akhir & daftar gambar                      | A5 menggabungkan dokumen, bukan menulis isinya | Seluruh anggota menyetujui |

## 7.2. Tugas non-program lain

| **Aktivitas bersama**            | **Ketentuan**                                                                                             |
|----------------------------------|-----------------------------------------------------------------------------------------------------------|
| Analisis soal & keputusan teknis | Semua hadir D1; setujui definisi event, lifecycle, trace order, dan kontrak modul.                        |
| Pengujian dataset asli           | Semua memeriksa hasil modul sendiri; silang memeriksa satu modul rekan; A5 menjalankan tes integrasi.     |
| Screenshot bukti                 | A1: import/overview; A2: 11.7; A3: 11.15 & 11.18; A4: 11.22 & explorer; A5: ekspor, About, alur GUI.      |
| Slide/demo singkat               | Outline disusun bersama; setiap anggota menyiapkan 1 segmen penjelasan modul; urutan demo disepakati tim. |
| Rekaman demonstrasi              | A5 menyiapkan alat rekam; A1–A4 menjelaskan hasil masing-masing; semua ikut validasi rekaman.             |
| Penyuntingan akhir               | Seluruh anggota membaca laporan final dan menandai kesalahan sebelum pengumpulan.                         |
| Daftar kontribusi                | Setiap anggota mengisi kontribusi konkret: commit, fitur, tes, screenshot, bagian laporan.                |

## 7.3. Aturan partisipasi minimum di luar coding

> 1\. Setiap anggota menulis dokumentasi modulnya dan menyertakan minimal satu bukti case yang bisa diverifikasi.
>
> 2\. Setiap anggota menulis atau meninjau sedikitnya satu skenario test selain skenario modulnya.
>
> 3\. Setiap anggota membuat screenshot fitur yang dimilikinya beserta keterangan gambar dan hasil.
>
> 4\. Semua anggota melakukan peer review naskah, uji ulang aplikasi, dan menyetujui laporan akhir.
>
> 5\. Setiap anggota dapat menjelaskan arsitektur umum, cara impor XES, alasan filter, dan hasil dari setidaknya dua modul lain.

# 08. Timeline 7 hari kalender (D1–D7)

Durasi dihitung tujuh hari kalender berturut-turut sejak kickoff. Hari ke-7 adalah batas penyelesaian final. Tidak ada “minggu keempat” atau pekerjaan lanjutan sebagai prasyarat kelulusan Tahap 1. Pengembangan, pengujian, dokumentasi, dan UI berjalan paralel.

| **Hari** | **Target / milestone tim**       | **Kegiatan paralel per workstream**                                                                                                       | **Gate akhir hari**                                                |
|----------|----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------|
| D1       | Spesifikasi & fondasi disepakati | Semua: kickoff, baca soal, bagi peran, uji file XES; A1 schema loader; A2–A4 fixtures dan signatures; A5 repo + UI shell.                 | Kontrak data/result disetujui; repo siap; sampel XES dapat dibaca. |
| D2       | Mesin dasar berjalan             | A1 importer, index, overview; A2 duration + 11.7; A3 lifecycle + complete-only; A4 ordering + evidence pair; A5 common UI + CSV skeleton. | Seluruh modul dapat dijalankan dengan log sintetis.                |
| D3       | Semua fungsi 8 soal tersedia     | A1 worker/performa; A2 panel 11.7; A3 11.15/18 + panel; A4 11.22 + explorer; A5 shell navigasi/ekspor.                                    | Unit test inti lulus; hasil dapat dilihat per panel.               |
| D4       | Integrasi end-to-end pertama     | Semua merge PR kecil; jalankan F01–F07 pada log sintetis; benahi schema dan evidence; mulai menulis bagian laporan.                       | Demo sintetis: Import → hasil → evidence → export berhasil.        |
| D5       | Validasi dataset BPIC17 asli     | Semua jalankan soal pada XES asli, cek case dan event, mean duration, benchmark 11.7/11.15/11.18; A5 uji waktu impor & stabilitas.        | Tabel hasil BPIC17 + daftar selisih + log bukti tersedia.          |
| D6       | Stabilisasi dan laporan gabungan | Perbaiki bug prioritas tinggi, regression test, cross-review; semua melengkapi laporan/screenshot; A5 packaging & user guide.             | Semua tes wajib lulus; tidak ada bug kritis; feature freeze.       |
| D7       | Final QA dan pengumpulan         | Tes clean install, cek ulang delapan jawaban dan CSV, finalisasi laporan kolaboratif, rekam demo, checklist dan serahkan.                 | Seluruh deliverables lengkap dan demonstrasi bisa diulang.         |

## 8.1. Fokus harian berdasarkan anggota

| **Anggota** | **D1**     | **D2**     | **D3**   | **D4**    | **D5**   | **D6**    | **D7** |
|-------------|------------|------------|----------|-----------|----------|-----------|--------|
| A1          | Schema     | Loader     | Overview | Integrasi | Validasi | Performa  | QA     |
| A2          | Kontrak    | 11.7 logic | Panel    | Integrasi | Validasi | Laporan   | QA     |
| A3          | Lifecycle  | Rework     | Panel    | Integrasi | Validasi | Laporan   | QA     |
| A4          | Order rule | 11.22      | Explorer | Integrasi | Validasi | Laporan   | QA     |
| A5          | Repo/shell | Widgets    | Ekspor   | Integrasi | E2E      | Packaging | Demo   |

## 8.2. Ritme koordinasi

- Daily sync 15–20 menit: progres, blockers, dependensi, PR yang menunggu reviewer, dan target 24 jam berikutnya.

- Checkpoint D2 sore: seluruh kontrak modul bisa dipanggil dari fixture; D4 sore: aplikasi demo dengan log sintetis; D6 sore: code freeze.

- Masalah pemrosesan BPIC17 yang menghalangi seluruh tim harus dinaikkan pada hari ditemukan, bukan menunggu rapat berikutnya.

- Jika gate terlewat, tunda semua fitur opsional; alihkan 1 reviewer membantu bottleneck; jangan mengorbankan tes evidence atau aturan lifecycle.

# 09. Kolaborasi Git, API, dan kontrol perubahan

## 9.1. Aturan repository

> 1\. Gunakan branch fitur per anggota: feat/loader, feat/ex-11-7, feat/rework, feat/ordering, feat/gui-shell.
>
> 2\. Pisahkan modul core dan gui. Tidak ada perubahan kontrak EventStore atau AnalysisResult tanpa persetujuan tim.
>
> 3\. PR harus menyertakan ringkasan perubahan, cara menjalankan, screenshot jika mengubah GUI, serta hasil pytest.
>
> 4\. Minimal satu reviewer menyetujui setiap PR. Reviewer yang disarankan tercantum pada tabel pembagian kerja.
>
> 5\. Dataset XES asli dan data sensitif tidak di-commit. .gitignore wajib memasukkan data/\*.xes, data/\*.xes.gz, .venv/, \_\_pycache\_\_/, artefak sementara.
>
> 6\. Gunakan git tag v1.0-tahap1 pada versi yang dikumpulkan; catat commit hash, versi package, dan hash file dataset untuk reproduktibilitas.

## 9.2. Kontrak bersama yang harus diuji

| **Komponen**       | **Input**                      | **Output**                            | **Pemilik** |
|--------------------|--------------------------------|---------------------------------------|-------------|
| load_event_log     | File path XES                  | EventStore + metadata / error         | A1          |
| get_case_durations | EventStore                     | DataFrame: case_id, duration_days     | A2          |
| run_11_7           | EventStore                     | 5 × AnalysisResult                    | A2          |
| run_11_15 / 18     | EventStore + nama target valid | 2 × AnalysisResult                    | A3          |
| run_11_22          | EventStore                     | 1 × AnalysisResult + pairs            | A4          |
| get_case_trace     | EventStore + case_id           | Rows event urut + evidence highlights | A4          |
| export_results     | List AnalysisResult + path     | CSV summary, cases, evidence          | A5          |

## 9.3. Standar penanganan error

GUI wajib menampilkan pesan berbeda untuk (a) file tidak dapat dibaca; (b) atribut wajib hilang; (c) event log kosong; (d) lifecycle tidak tersedia untuk 11.15/11.18; (e) resource tidak tersedia untuk 11.18; (f) aktivitas target tidak ditemukan; (g) operasi dibatalkan/gagal. Kesalahan tersebut harus dilog untuk memudahkan reproduksi.

# 10. Pengujian dan validasi

## 10.1. Skenario sintetis wajib

| **ID** | **Skenario**                                       | **Ekspektasi**                                                             |
|--------|----------------------------------------------------|----------------------------------------------------------------------------|
| T01    | O_Accepted muncul dua kali dalam satu case         | 11.7 C menghitung satu case.                                               |
| T02    | O_Cancelled di tengah, event lain setelahnya       | 11.7 E tidak memilih case tersebut.                                        |
| T03    | O_Refused dan O_Accepted keduanya ada              | Case dapat lolos 11.7 C dan 11.7 D.                                        |
| T04    | W_Assess fraud scheduled dua kali, complete satu   | 11.15 tidak memilih case.                                                  |
| T05    | Dua complete oleh dua resource berbeda             | 11.15 lolos; 11.18 tidak.                                                  |
| T06    | Dua complete oleh resource identik                 | 11.15 dan 11.18 lolos.                                                     |
| T07    | O_Cancelled → event lain → O_Accepted              | 11.22 lolos.                                                               |
| T08    | O_Accepted → O_Cancelled tanpa accepted setelahnya | 11.22 tidak lolos.                                                         |
| T09    | Dua complete dengan resource null / blank          | 11.18 tidak lolos.                                                         |
| T10    | Lifecycle tidak tersedia                           | 11.15/11.18 unavailable; bukan angka 0 palsu.                              |
| T11    | Dua event timestamp identik                        | Endpoint dan eventually follows konsisten dengan urutan trace asli.        |
| T12    | Case hanya satu timestamp atau event tunggal       | Durasi 0 hari; mean dan count dihitung benar.                              |
| T13    | File XES rusak / atribut wajib hilang              | Import ditolak dengan pesan jelas; aplikasi tidak crash.                   |
| T14    | Case cocok memuat banyak pasangan cancel→accept    | 11.22 menghitung case sekali dan menunjukkan setidaknya satu pasangan sah. |
| T15    | Dataset kosong / tidak ada case                    | Statistik dan persentase tidak membagi nol; status jelas.                  |

## 10.2. Strategi uji berlapis

| **Lapisan**       | **Pelaksanaan**                                                                                | **Penanggung jawab**                    |
|-------------------|------------------------------------------------------------------------------------------------|-----------------------------------------|
| Unit              | Setiap module owner membuat tes eksplisit untuk semantik filter dan edge cases.                | A1–A4 sesuai modul; A5 test export.     |
| Integrasi         | Impor → Overview → Exercise → Case Explorer → CSV; pengulangan dan reset diuji.                | A5 memimpin, semua anggota menjalankan. |
| Dataset riil      | Jalankan BPIC17 sesuai versi yang disepakati, rekam jumlah case/event, output delapan jawaban. | A1–A4 menghitung dan meninjau silang.   |
| Keandalan GUI     | Uji file rusak, impor ulang, operasi lama, progress, responsivitas, pencarian case.            | A1 + A5, ditinjau semua.                |
| Clean environment | Pasang requirements di environment baru; jalankan aplikasi tanpa modifikasi kode.              | A5 dan satu reviewer dari A1–A4.        |

## 10.3. Template validasi BPIC17

| **Exercise** | **Referensi materi**             | **Hasil aplikasi** | **Status/penjelasan**                              |
|--------------|----------------------------------|--------------------|----------------------------------------------------|
| 11.7 A       | 31.509                           | Diisi hasil run    | Match / jelaskan selisih                           |
| 11.7 B       | 21,9 hari                        | Diisi hasil run    | Toleransi pembulatan harus dicatat                 |
| 11.7 C       | 17.228; 18,1 hari                | Diisi hasil run    | Tampilkan contoh case                              |
| 11.7 D       | 3.720; 16,8 hari                 | Diisi hasil run    | Tampilkan contoh case                              |
| 11.7 E       | 4.436; 23 hari                   | Diisi hasil run    | Pastikan endpoint                                  |
| 11.15        | 13 (complete-only)               | Diisi hasil run    | Pastikan lifecycle                                 |
| 11.18        | 3 (complete-only, resource sama) | Diisi hasil run    | Resource null tidak lolos                          |
| 11.22        | Tidak tercantum                  | Diisi hasil run    | Sertakan count, persen, denominator, pasangan i\<j |

Jangan menyatakan validasi dataset asli telah berhasil sebelum menjalankan file BPIC17 yang disepakati dan menyimpan hasil aktualnya. Angka referensi hanya penuntun review, bukan expected yang dipaksakan untuk semua file.

## 10.4. Acceptance criteria akhir

> 1\. F01–F07 berfungsi melalui GUI desktop pada BPIC17 dan minimal satu log sintetis.
>
> 2\. Delapan jawaban muncul dengan definisi, satuan, angka, dan denominator yang tepat.
>
> 3\. Semua jawaban dihasilkan dinamis dari file XES pilihan pengguna.
>
> 4\. Setiap hasil filter dapat ditelusuri ke case ID dan event pembukti.
>
> 5\. T01–T15 lulus atau kegagalan diberi alasan, tingkat risiko, pemilik, dan status penanganan; delapan skenario asli dosen wajib lulus.
>
> 6\. Re-import dataset yang sama menghasilkan jawaban yang identik; versi dan hash dataset tercatat.
>
> 7\. README, requirements, source modular, laporan, screenshot, demonstrasi, dan kontribusi lima anggota lengkap.

# 11. Hasil akhir, demonstrasi, dan risiko

## 11.1. Paket pengumpulan

| **Artefak**      | **Ketentuan minimal**                                                                                |
|------------------|------------------------------------------------------------------------------------------------------|
| Aplikasi desktop | Bisa dijalankan di komputer lain sesuai instruksi instalasi; GUI dan F01–F07 berfungsi.              |
| Source code      | Repository modular, tanpa dataset besar/credential dalam commit.                                     |
| Environment      | requirements.txt + versi Python dan OS yang diuji.                                                   |
| README           | Instalasi, menjalankan, penggunaan menu, aturan soal, dependensi, batasan.                           |
| Laporan kelompok | Pemetaan soal→fungsi, definisi filter, hasil BPIC17, screenshot evidence, test, kendala, kontribusi. |
| Screenshots      | Setiap menu utama dan setidaknya satu trace evidence untuk 11.15, 11.18, 11.22.                      |
| Demo             | Buka XES → overview → 11.7 → 11.15 → 11.18 → 11.22 → case evidence → export.                         |
| Metadata dataset | Nama/versi/sumber XES, ukuran dan hash; tidak perlu upload ulang XES bila sangat besar.              |

## 11.2. Naskah demonstrasi singkat

> 1\. A1 membuka aplikasi, memilih BPIC17 XES, menjelaskan atribut wajib dan Overview.
>
> 2\. A2 menjalankan 11.7 A–E, menjelaskan perbedaan contains dan endpoint, lalu membuka salah satu case.
>
> 3\. A3 menjalankan 11.15 dan 11.18, menyorot lifecycle=complete dan resource ID pada evidence.
>
> 4\. A4 menjalankan 11.22, menyebut numerator-denominator dan menampilkan pasangan event i\<j beserta trace.
>
> 5\. A5 mengekspor CSV, menunjukkan lokasi berkas, reset/rerun, dan About/versi; semua menjawab pertanyaan penguji.

## 11.3. Risiko dan mitigasi

| **Risiko**                    | **Dampak**                      | **Mitigasi**                                                              |
|-------------------------------|---------------------------------|---------------------------------------------------------------------------|
| 5 anggota vs ketentuan 4      | Aspek administrasi pengumpulan  | Pastikan persetujuan dosen sejak D1; catat keputusan.                     |
| File XES besar / berat        | GUI freeze, terlambat integrasi | A1 uji XES D1; worker, cache, virtualized case view, pantau memori.       |
| Lifecycle berbeda / tidak ada | Soal 11.15–11.18 salah          | Inspect atribut asli; tampilkan unavailable bila tidak terbukti complete. |
| Label aktivitas berbeda       | Hasil 0 salah                   | Gunakan lookup aktivitas aktual; catat exact label.                       |
| Kontrak antar modul berubah   | PR konflik / pipeline rusak     | Freeze contract D1; review perubahan; smoke test D4.                      |
| Dokumentasi tertunda          | Pengumpulan tidak lengkap       | Setiap anggota menulis saat fitur selesai; final review D6–D7.            |
| Hasil acuan tidak cocok       | Validasi dipertanyakan          | Audit dataset/version, case IDs, timestamp, lifecycle, dan evidence.      |
| A5 menjadi bottleneck         | GUI tertunda                    | A1–A4 membuat panel sendiri; A5 hanya shell/shared components/integrasi.  |

## 11.4. Pengembangan opsional setelah tugas wajib beres

Jika seluruh acceptance criteria sudah dipenuhi lebih cepat, tim boleh memilih SATU tambahan: fast cases (\<45 hari) vs slow cases (\>=45 hari) sesuai definisi materi, grafik distribusi durasi, filter builder generik, laporan PDF otomatis, atau DFG sederhana. Jangan memasukkan discovery algorithms yang dikecualikan ke target Tahap 1.

# Lampiran A. Matriks ketertelusuran persyaratan

| **Persyaratan**          | **Modul / bukti**                        | **Owner** | **Verifikasi**                      |
|--------------------------|------------------------------------------|-----------|-------------------------------------|
| F01 XES import + atribut | loader.py, event_store.py, import status | A1        | T13, BPIC17                         |
| F02 overview             | overview.py, overview panel              | A1        | Jumlah case/event, durasi           |
| 11.7 A–E / F03           | cycle_time.py, ex_11_7.py, panel         | A2        | T01–T03, acuan 11.7                 |
| 11.15 / F04              | rework.py, ex_11_15_18.py                | A3        | T04–T06, T10                        |
| 11.18 / F05              | resource evidence, panel rework          | A3        | T05–T06, T09                        |
| 11.22 / F06              | ordering.py, panel sequence              | A4        | T07–T08, T14                        |
| F07 Case Explorer        | case explorer panel                      | A4        | Trace urut dan highlighted evidence |
| F07 ekspor, reset        | export.py, shared GUI                    | A5        | CSV dan E2E                         |
| Responsif & status       | worker.py, status banner                 | A1+A5     | Uji full XES                        |
| Laporan & demo           | docs, screenshots, recording             | Semua     | Checklist D7                        |
| Rubrik 100%              | hasil, bukti, testing, dokumentasi       | Semua     | Review bersama                      |

# Lampiran B. Template output untuk setiap analisis

```json
{
  "exercise_id": "11.22",
  "rule_description": "Case contains O_Cancelled before O_Accepted",
  "count": "<dihitung dari log>",
  "denominator": "<jumlah seluruh case aktif>",
  "percentage": "<count/denominator*100>",
  "case_ids": ["<case ID yang cocok>"],
  "evidence_columns": [
      "case_id", "cancel_row_id", "cancel_position",
      "cancel_timestamp", "accept_row_id", "accept_position",
      "accept_timestamp"
  ],
  "dataset_name": "<file XES aktif>",
  "status": "ok"
}
```

Catatan: placeholder dalam lampiran ini adalah contoh format dokumentasi, tidak boleh menjadi jawaban statis dalam aplikasi. Untuk 11.15 dan 11.18, tambahkan lifecycle, resource, dan jumlah complete occurrence.

# Lampiran C. Checklist operasional D7

- [ ] Anggota berjumlah 5 disetujui dosen / keputusan administrasi tercatat.

- [ ] BPIC17 XES dapat dimuat dari pemilih file; nama, jumlah case/event dan atribut tampil.

- [ ] Exercise 11.7 A–E menampilkan jumlah dan mean sesuai definisi.

- [ ] Exercise 11.15 menampilkan ≥2 complete occurrences dengan bukti event.

- [ ] Exercise 11.18 menampilkan ≥2 complete oleh resource identik (nonblank).

- [ ] Exercise 11.22 menampilkan count, persen, denominator, dan event pair i\<j.

- [ ] Case Explorer bisa mencari case dan memperlihatkan trace lengkap.

- [ ] Summary, selected case list, dan evidence dapat diekspor sebagai CSV.

- [ ] Reset/re-run tidak memerlukan impor ulang; tidak ada nilai hard-coded.

- [ ] T01–T15 telah dijalankan; hasil pengujian disimpan.

- [ ] Hasil BPIC17 dibandingkan dengan referensi; selisih diberi penjelasan.

- [ ] requirements, README, source, metadata versi/hash tersedia.

- [ ] Laporan selesai dan diperiksa oleh seluruh lima anggota.

- [ ] Screenshots semua menu dan evidence soal 11.15, 11.18, 11.22 terlampir.

- [ ] Demonstrasi siap; seluruh anggota memahami bagian sendiri serta alur umum.

# Lampiran D. Referensi dan kontrol versi

Sumber internal (prioritas):

- Instruksi_Proyek_Tahap_1_Analisis_Soal_BPIC17_PM4Py.pdf, versi 16 November 2026, 8 halaman. Rujukan utama persyaratan, rubrik, dan batas cakupan.

- BPIC-2017.pdf, 23 halaman. Rujukan Exercise 11.7, 11.15, 11.18, 11.22 dan angka acuan historis.

- Panduan Proyek Datmin.pdf, 34 halaman. Dokumen yang direvisi: tugas, tutorial, alur kerja, serta contoh kode awal.

Sumber eksternal pendukung teknis:

- BPI Challenge 2017 (4TU.ResearchData): https://data.4tu.nl/articles/dataset/BPI_Challenge_2017/12696884

- PM4Py API read_xes: https://processintelligence.solutions/pm4py/api/2.7.21/api/pm4py.read.html

- PM4Py Getting Started: https://github.com/process-intelligence-solutions/pm4py/blob/release/docs/source/getting_started.rst

- Qt for Python / PySide6: https://doc.qt.io/qtforpython-6/

Kontrol versi proyek saat penyerahan harus mencatat: commit/tag, versi Python, PM4Py, pandas, PySide6, pytest, OS yang diuji, tanggal pengujian, nama file XES, dan SHA-256 dataset. Angka dalam laporan wajib berasal dari eksekusi aktual aplikasi.

> **PENUTUP** Panduan ini menjadi kontrak kerja tujuh hari untuk tim lima anggota. Kriteria keberhasilan adalah hasil numerik yang benar, filter yang dapat dibuktikan, GUI yang bekerja, pengujian yang memadai, serta laporan yang benar-benar dikerjakan bersama.
