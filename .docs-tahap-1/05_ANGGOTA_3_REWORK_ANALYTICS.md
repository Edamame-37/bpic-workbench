# Anggota 3 — Rework Analytics: Exercise 11.15 dan 11.18

**Owner:** A3 · **Reviewer silang:** A2 · **Estimasi:** 12 poin · **Fitur:** F04, F05 + panel rework, evidence, unit tests · **Jadwal:** D1–D7.

## 1. Konteks yang harus dikuasai sebelum coding

Baca `01_PANDUAN_KERJA_IDENTIK_PDF.md` bagian 02.1–02.3, 04, 05.3, 06, 08–10 dan `02_DOKUMENTASI_TEKNIS.md` bagian 3.1–3.4, 5.3, 7–10. Soal 11.15/11.18 **tidak** meminta berapa kali aktivitas fraud terlihat, melainkan berapa **case** yang memuat aktivitas fraud yang **selesai (`complete`) minimal dua kali**; 11.18 menambah syarat dua complete oleh **resource teridentifikasi yang sama**.

**Peringatan historis:** sumber latihan menunjukkan 13 kasus (11.15) dan 3 kasus (11.18) pada interpretasi *complete-only*. Disco dalam materi menghasilkan angka 20/8 melalui filter yang tidak ekuivalen. Jangan mengubah definisi agar sama dengan hasil Disco, atau menganggap kedua angka sebagai error program tanpa memeriksa lifecycle.

## 2. Ruang kerja dan file owner

| File | Tanggung jawab |
|---|---|
| `src/core/rework.py` | cari aktivitas aktual, filter complete-only, hitung repeat per case/resource |
| `src/core/ex_11_15_18.py` | implementasi `run_11_15` dan `run_11_18` → `AnalysisResult` |
| `src/gui/panels/rework_panel.py` | panel 11.15 dan 11.18, lifecycle status, resource count, bukti event |
| `tests/test_rework.py` | T04, T05, T06, T09, T10 dan edge cases tambahan |
| `docs/laporan.md` (bagian A3) | definisi complete, hasil rework, bukti case dan keterbatasan |

A3 boleh membantu penyusunan fixture bersama pada D1. A3 **tidak** mengambil alih loader A1 atau Case Explorer A4.

## 3. Definisi filter yang tidak boleh dilanggar

### 3.1. Pemilihan nama aktivitas

Nama aktivitas fraud harus diambil dari `store.events["concept:name"]`. Materi mengenal label `W_Assess potential fraud` dan variasi kapitalisasi; jangan berasumsi string `W_Assess Potential Fraud` pasti persis sama dengan XES.

Aturan yang disarankan:

1. Tampilkan daftar nama aktivitas unik yang memuat frasa fraud untuk pemeriksaan.
2. Tentukan satu nama target nyata (exact string) dan catat di `rule_description`/metadata.
3. Bila kandidat lebih dari satu dan ambigu, minta pemilihan pada panel atau tampilkan status yang jelas. Jangan memilih diam-diam dengan substring jika itu bisa mencampur aktivitas berbeda.
4. Bila target tidak ada, status dapat `unavailable` (sesuai panduan) dengan pesan nama tidak ditemukan; bedakan dari count nol setelah filter dievaluasi dengan atribut memadai.

### 3.2. Lifecycle `complete` harus terverifikasi

- Filter event target **dan** nilai `lifecycle:transition` yang secara sah merepresentasikan `complete`.
- Terapkan normalisasi ringan nilai lifecycle, misalnya `strip().casefold()` untuk string literal; jangan menganggap `start`, `schedule`, `abort`, atau empty sebagai selesai.
- Ketiadaan seluruh kolom lifecycle → **`unavailable`**, bukan `count=0 status=ok` dan bukan semua event dianggap complete.
- Jika sebagian event target tidak punya lifecycle, catat ketidaklengkapan. Jangan menyimpulkan hasil lengkap bila unknown events dapat mengubah apakah case memenuhi kriteria. Hasil parsial harus diberi peringatan atau status tidak tersedia sesuai keputusan D1.
- Bukti harus menunjukkan `lifecycle:transition` aktual untuk event yang dihitung; bukan klaim teks saja.

**Ingat:** argumen `complete_value` pada implementasi nyata harus benar-benar dipakai; jangan membuat parameter yang diabaikan dan tetap memakai string tertanam di dalam helper.

### 3.3. Exercise 11.15 — repeated complete

```text
subset = events WHERE concept:name == fraud_target
                 AND lifecycle:transition == verified_complete
count_complete[case_id] = jumlah baris subset untuk case tersebut
selected_cases = case_id dengan count_complete >= 2
result.count = banyaknya case_id unik dalam selected_cases
```

Evidence: untuk case terpilih, cantumkan **minimal dua baris** complete, `_row_id`, `_trace_pos`, timestamp, lifecycle, jumlah penyelesaian per case. Kegiatan yang hanya scheduled dua kali tetapi complete satu kali **tidak lolos**.

### 3.4. Exercise 11.18 — repeated complete by same resource

```text
subset = hasil filter complete yang sama dengan 11.15
valid_resource = subset WHERE org:resource IS NOT NULL
                          AND strip(resource) != ""
counts[(case_id, resource)] = jumlah complete oleh resource tersebut
selected_cases = UNIQUE case_id dari counts[(case_id, resource)] >= 2
result.count = banyak case_id unik, bukan banyak pasangan (case, resource)
```

Dua complete oleh `U01` dan `U02` berbeda → lolos 11.15, **tidak** lolos 11.18. Dua complete dengan resource kosong bukan *same resource*. Jika resource field tidak ada untuk seluruh log, 11.18 `unavailable` dengan penjelasan; 11.15 tetap boleh dihitung bila lifecycle valid.

Jika satu case memiliki dua resource berbeda yang masing-masing complete >=2, count hasil tetap **satu case** walaupun tabel bukti dapat memuat lebih dari satu grup resource.

## 4. Kontrak API dan `AnalysisResult`

```python
def run_11_15(store, activity_name: str):
    """Returns AnalysisResult for completed fraud activity repeated in a case."""

def run_11_18(store, activity_name: str):
    """Returns AnalysisResult for repeated completed fraud by same resource."""
```

Untuk tiap result sertakan: `exercise_id`, `rule_description` yang menyebut target exact + lifecycle complete + syarat count, `count`, `denominator` seluruh case log aktif, `case_ids`, `evidence`, `status`, `notes`. `mean_days` dan `percentage` tidak diwajibkan untuk soal ini. Evidence sebaiknya memuat `case_id`, `org:resource` bila relevan, `_row_id`, `_trace_pos`, `concept:name`, `lifecycle:transition`, `time:timestamp`, `complete_count`.

**Menjaga kontrak:** A3 tidak memodifikasi `AnalysisResult` tanpa persetujuan; jika ingin field baru untuk `resource_count`, letakkan pada evidence/notes atau diskusikan schema shared.

## 5. UI yang harus dibuat A3 sendiri

Panel rework minimal menyediakan:

- Dua tab/bagian: **11.15 Repeated Complete** dan **11.18 Same Resource Complete**.
- Nama aktivitas yang benar-benar digunakan dan nilai lifecycle yang dipakai, dapat ditinjau pengguna.
- Count case, denominator dan penjelasan satuan (*case*, bukan *event*).
- Tabel case ID + jumlah complete (11.15), tabel case ID/resource + jumlah complete (11.18).
- Pilih case, lihat event pembukti dan tombol ke **Case Explorer A4** dengan highlight `_row_id`.
- Jika lifecycle/resource tidak ada, tampilkan **analisis tidak tersedia** dengan sebab; jangan menampilkan angka 0 yang menyesatkan.
- Rerun tanpa impor ulang.

Gunakan komponen tabel/result yang dibuat A5; jangan menulis UI berbasis data mentah yang mengandung jutaan baris secara langsung.

## 6. Jadwal A3 per hari

| Hari | Pekerjaan | Bukti akhir |
|---|---|---|
| **D1** | Telaah lifecycle dataset, definisikan target fraud, kontrak evidence, siapkan fixture T04–T06/T09/T10 | Aturan complete dan resource tertulis, reviewer A2 setuju |
| **D2** | Implement `complete_events`, `repeated_complete`, `same_resource_complete`, `run_11_15`, `run_11_18` | Core return valid pada fixture sintetis |
| **D3** | Buat rework panel, status unavailable, tabel resource dan tombol case; selesaikan unit tests | Panel menampilkan 11.15/11.18 dan bukti sintetis |
| **D4** | Integrasi dengan A1 EventStore, A4 Explorer, A5 shell/CSV; tulis laporan awal | Alur import → rework → event evidence → export berhasil |
| **D5** | Jalankan BPIC17 asli; inspeksi label/lifecycle/resource; bandingkan dengan rujukan 13 dan 3 | Tabel aktual, evidence case, catatan selisih |
| **D6** | Cross-review A2, regression, screenshot lengkap, pembahasan temuan dan keterbatasan | Tidak ada bug kritis dan laporan bagian A3 siap |
| **D7** | Final QA, demo dua soal beserta evidence resource, peer review laporan gabungan | Handoff final dan pengesahan kontribusi |

## 7. Skenario pengujian wajib A3

| ID | Fixture | 11.15 | 11.18 |
|---|---|---|---|
| **T04** | schedule, schedule, complete (aktivitas fraud sama) | tidak lolos | tidak lolos |
| **T05** | complete U01, complete U02 | lolos | tidak lolos |
| **T06** | complete U01, complete U01 | lolos | lolos |
| **T09** | complete null, complete kosong | lolos | tidak lolos |
| **T10** | lifecycle field hilang | unavailable | unavailable |
| Tambahan | complete U01, start U01, complete U02 | lolos | tidak lolos |
| Tambahan | 4 complete: 2×U01, 2×U02 | satu case | satu case |
| Tambahan | tidak ada aktivitas target | status jelas, bukan hasil dipaksakan | status jelas |
| Tambahan | lifecycle upper/lower berbeda sah | dihitung hanya `complete` tervalidasi | sama |

Untuk T10, test `status == "unavailable"` atau outcome yang disepakati, **bukan** `count == 0` saja.

```bash
python -m pytest tests/test_rework.py -q
python -m pytest -q
```

## 8. Dependensi dan handoff

**Dari A1**: EventStore, nama aktivitas aktual, daftar nilai lifecycle, resource availability, `_trace_pos`, `_row_id`.

**Ke A4**: format evidence yang dapat di-highlight, pasangan event valid dan `case_id` untuk Explorer.

**Ke A5**: `AnalysisResult` 11.15/11.18 yang memuat `evidence` dan informasi status/error untuk tab/CSV.

**Review silang A2**: A2 memeriksa complete-only dan jumlah case tidak mengganda. A3 juga mereview filter 11.7 serta membantu tes non-modul.

**Blocker eskalasi:** lifecycle tidak ada/tidak jelas; target label ganda; resource kosong seluruh dataset; hasil benchmark berbeda besar. Laporkan, sertakan sample event, jangan ganti jawaban/semantik diam-diam.

## 9. Pekerjaan non-program wajib A3

- Menulis bagian **metodologi, hasil 11.15/11.18, interpretasi lifecycle dan resource**, tanpa mengklaim verifikasi BPIC17 sebelum run aktual.
- Screenshot kedua panel, minimal satu trace dengan dua event complete, dan minimal satu trace resource identik.
- Menyiapkan tabel perbandingan hasil program vs referensi (13/3) serta penjelasan bila berbeda.
- Menjelaskan pada demo kenapa dua scheduled bukan dua completed dan kenapa resource kosong tidak sah.
- Menjalankan tes silang A2, meninjau laporan seluruh anggota, ikut menyusun kesimpulan/keterbatasan, dan menyetujui dokumen final.

## 10. Definition of Done A3

- [ ] Target fraud yang dipilih benar-benar cocok dengan label data.
- [ ] 11.15 hanya menghitung minimal dua **complete** per case.
- [ ] 11.18 menambah syarat same valid resource dan menghitung case unik.
- [ ] Missing lifecycle/resource tidak disamarkan sebagai hasil valid nol.
- [ ] Evidence menunjukkan event benar, lifecycle, resource, dan jumlah occurrence.
- [ ] Rework panel terhubung ke Explorer dan export.
- [ ] T04, T05, T06, T09, T10 dan tambahan lulus; reviewer A2 menyetujui.
- [ ] Laporan/screenshot/demo A3 tuntas.

## 11. Prompt untuk coding agent A3

```text
Anda developer Anggota 3 (A3), Rework Analytics BPIC17.
Baca panduan utama, dokumentasi teknis, lalu file A3 ini.
Kerjakan rework.py, ex_11_15_18.py, rework_panel.py, test_rework.py.
Gunakan aktivitas fraud exact dari XES dan hitung HANYA lifecycle complete.
11.15: >=2 event complete per case. 11.18: >=2 event complete oleh
resource valid yang identik pada case yang sama. Case dihitung sekali.
Jika lifecycle atau resource tidak bisa membuktikan kondisi, tampilkan
unavailable atau hasil dengan batasan eksplisit, bukan count=0 palsu.
Sediakan evidence event dengan row_id, posisi, lifecycle, resource.
Jangan mengubah loader, 11.7, atau 11.22 tanpa review.
Jalankan pytest T04/T05/T06/T09/T10 dan laporkan hasil aktual,
case bukti sintetis, API, file berubah, serta blocker.
```
