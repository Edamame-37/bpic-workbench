# Anggota 4 — Sequence Analytics 11.22 dan Case Explorer

**Owner:** A4 · **Reviewer silang:** A1 · **Estimasi panduan:** 12 poin · **Fitur:** F06, bagian F07 berupa Case Explorer · **Target:** D1–D7, tujuh hari kalender.

## 1. Misi dan konteks

Bangun analisis **Exercise 11.22**: apakah suatu case mempunyai `O_Cancelled` yang **kemudian** diikuti `O_Accepted` di posisi trace lebih akhir? Berapa jumlah dan persentase case? Selain itu, buat **Case Explorer lintas latihan** agar pengguna dapat menelusuri seluruh event dalam case dan melihat event yang dijadikan bukti oleh A2/A3/A4.

Baca `01_PANDUAN_KERJA_IDENTIK_PDF.md` bagian 02, 03, 04, 05.4, 06–10, Lampiran A–D; lalu `02_DOKUMENTASI_TEKNIS.md` bagian 3.1–3.4, 4, 5.4, 6–10.

**Jangan menyamakan:** `eventually follows` dengan `directly follows`; urutan event dengan urutan waktu yang diurut ulang; case-level dengan offer-level; atau `O_Cancelled` sebelum `O_Accepted` dengan case yang berakhir `O_Cancelled`.

## 2. Batas modul milik A4

| File | Tanggung jawab |
|---|---|
| `src/core/ordering.py` | deteksi `i < j` pada urutan trace, penentuan pasangan event pembukti |
| `src/core/ex_11_22.py` | count/persentase/denominator 11.22, `AnalysisResult` |
| `src/gui/panels/sequence_panel.py` | panel 11.22, timeline cancellation–acceptance, case list |
| `src/gui/panels/case_explorer_panel.py` | pencarian case, tabel trace lengkap, highlight evidence lintas modul |
| `tests/test_ordering.py` | T07, T08, T11, T14 + edge cases |
| `docs/laporan.md` (bagian A4) | definisi eventually follows, hasil 11.22, case evidence, keterbatasan |

A4 berkoordinasi dengan A3 mengenai format event evidence, A2 tentang aksi buka case, dan A5 tentang navigasi UI. Jangan mengubah implementasi perhitungan 11.7 atau rework dari dalam Case Explorer.

## 3. Semantik Exercise 11.22

Untuk setiap case:

- Ambil posisi semua event `O_Cancelled` dan posisi semua event `O_Accepted` yang berasal dari `_trace_pos` A1.
- Case **lolos jika** ada pasangan posisi `(i, j)` dengan `i < j`, event pada `i` adalah `O_Cancelled`, event pada `j` adalah `O_Accepted`.
- `O_Cancelled → aktivitas lain → O_Accepted` lolos.
- `O_Accepted → O_Cancelled` tanpa accepted lagi setelahnya tidak lolos.
- `O_Cancelled` berulang dan `O_Accepted` berulang pada satu case tetap dihitung **sekali**.
- Event tidak harus berada pada **offer ID sama**, sesuai definisi soal case-level di instruksi.

**Penyaringan cepat:** untuk setiap case, kondisi `min(cancel_positions) < max(accept_positions)` cukup untuk menentukan existence. Namun itu **belum** menentukan pasangan bukti eksplisit. Setelah lolos, ambil misalnya cancel valid terawal dan **accept pertama yang berada setelah cancel tersebut**; simpan `_row_id` dan timestamp keduanya.

```python
# Pseudocode konsep (bukan implementasi lengkap)
for case_id, trace in cases_in_original_trace_order:
    earlier_cancel = None
    for event in trace:
        if event.activity == "O_Cancelled" and earlier_cancel is None:
            earlier_cancel = event
        if event.activity == "O_Accepted" and earlier_cancel is not None:
            matched_cases.add(case_id)
            evidence[case_id] = (earlier_cancel, event)
            break
# count=len(matched_cases)
# denominator=jumlah SEMUA case log aktif
# percentage=100*count/denominator jika denominator > 0
```

Algoritma dapat dioptimalkan memakai pandas, tetapi test dengan beberapa event dalam satu case harus menghasilkan pasangan yang **benar-benar ada**.

## 4. Kontrak hasil 11.22 dan evidence

```python
def run_11_22(store) -> AnalysisResult: ...
def get_case_trace(store, case_id: str) -> "pandas.DataFrame": ...
```

`run_11_22` berisi:

- `exercise_id="11.22"`
- `rule_description`: keberadaan O_Cancelled di i dan O_Accepted di j dengan i < j; tanpa adjacency requirement.
- `count` sebagai banyak case unik lolos.
- `denominator` = semua case log aktif sebelum filtering.
- `percentage` = `100 * count / denominator` untuk denominator positif.
- `case_ids`, `status`, `notes`, dan `evidence`.

Skema evidence minimum yang **wajib dapat dipakai A5 untuk ekspor**:

| Field | Arti |
|---|---|
| `case_id` | ID case aktif |
| `cancel_row_id` | `_row_id` event cancel yang dipilih |
| `cancel_position` | `_trace_pos` cancellation |
| `cancel_timestamp` | waktu cancellation |
| `accept_row_id` | `_row_id` event acceptance yang dipilih |
| `accept_position` | `_trace_pos` acceptance |
| `accept_timestamp` | waktu acceptance |

Invariant: `cancel_position < accept_position` dan kedua row ID harus berasal dari **case yang sama**. Dalam laporan, sebut satu case bisa mempunyai beberapa offer; hasil ini **bukan** analisis per offer.

## 5. Desain dan perilaku Case Explorer

Case Explorer merupakan komponen **bersama untuk seluruh soal** (bukan hanya 11.22). Tampilan minimal:

1. Search `case_id` dan daftar case aktif/terpilih; pencarian menangani identifier string yang mungkin memiliki leading zeros.
2. Saat case dipilih, tampilkan **semua event dalam case**, berurut `_trace_pos`, dengan minimal aktivitas, timestamp, lifecycle jika ada, resource jika ada, dan ID event.
3. Tampilkan durasi case dan metadata dasar; data berasal dari EventStore dan perhitungan A2.
4. Terima `highlight_row_ids` opsional dari panel A2/A3/A4 untuk menyorot event yang merupakan evidence.
5. Pada 11.22, tampilkan timeline yang memperjelas pasangan cancel dan accept serta posisi i/j. Jangan tampilkan hanya daftar nama event tanpa urutan.
6. Tetap nyaman digunakan pada case panjang: model tabel/pagination/virtualization daripada mengisi jutaan baris widget.
7. Jika case tidak ditemukan atau dataset berganti, berikan pesan jelas dan hapus highlight lama.

**Kontrak UI yang perlu disetujui D1 dengan A5:** `open_case(case_id: str, highlight_row_ids: list[int] | None)` dapat berupa signal/slot atau method; pilih salah satu dan jangan mengubah signature sepihak.

## 6. Timeline A4 tujuh hari

| Hari | Pekerjaan A4 | Gate |
|---|---|---|
| **D1** | Tentukan kontrak evidence + `open_case`, fixture T07/T08/T11/T14, diskusi trace order dengan A1 dan schema dengan A3/A5 | API/pasangan bukti disetujui |
| **D2** | Implement `eventually_follows`, `run_11_22`, pasangan evidence, cache/search trace | 11.22 lolos unit test sintetis |
| **D3** | Implement sequence panel, pencarian Explorer, tabel trace dan highlights | Demo case sintetis penuh via GUI |
| **D4** | Integrasi tombol case A2/A3, export evidence A5, loader A1; tulis outline metode | End-to-end import→11.22→Explorer→export |
| **D5** | Jalankan BPIC17 asli, simpan count/percent/denominator, screenshot pasangan event aktual | Validasi kasus dari XES dengan trace bisa dicek |
| **D6** | Perbaiki bug ordering, UI performance, reviewer A1, laporan/screenshot | T07/T08/T11/T14 lulus dan panel stabil |
| **D7** | Bersama tim uji clean install/demo; presentasikan count/persentase dan timeline | F06/Explorer siap penyerahan |

## 7. Rencana pengujian yang penting

| ID | Trace | Expected |
|---|---|---|
| **T07** | Cancel → X → Accept | lolos meskipun tidak bersebelahan |
| **T08** | Accept → Cancel, tanpa Accept setelahnya | tidak lolos |
| **T11** | timestamp identik pada Cancel dan Accept | urutan menurut XES yang asli, bukan tie-sort tak tentu |
| **T14** | Cancel→Accept→Cancel→Accept pada case sama | count tetap 1; pasangan valid disimpan |
| Tambahan | Accept→Cancel→Accept | lolos karena pasangan event kedua–ketiga |
| Tambahan | hanya Cancel tanpa Accept | tidak lolos |
| Tambahan | banyak case, sebagian tanpa target | denominator seluruh log aktif |
| Tambahan | log kosong | percentage tidak dibagi nol |
| Tambahan | Case Explorer membuka case dari panel A2/A3 | trace dan event sorotan cocok dengan evidence |

```bash
python -m pytest tests/test_ordering.py -q
python -m pytest tests/test_integration.py -q
```

Khusus 11.22 tidak ada angka jawaban rujukan pada PDF dosen. Angka baru boleh dimasukkan laporan setelah benar-benar menjalankan dataset BPIC17 pilihan tim.

## 8. Dependensi & serah terima

| Pihak | Perlu dari mereka | A4 memberikan |
|---|---|---|
| **A1** | `_trace_pos` yang benar, `_row_id`, case lookup, timestamps | laporan masalah trace order; test T11 |
| **A2** | cache duration untuk Explorer, case IDs, `_row_id` selected | API `open_case` dan highlights |
| **A3** | evidence 11.15/11.18 (row IDs, resource, lifecycle) | satu Case Explorer untuk rework |
| **A5** | panel shell, navigasi, reusable table, export contract | SequencePanel, CaseExplorerPanel, evidence 11.22 |

**Reviewer silang A1** harus mengecek ordering dari data XES, bukan dari urutan diagram atau sorted timestamp. A4 mereview import dan T11 buatan A1.

**Blockers segera:** source event order hilang, `_trace_pos` dibuat berdasarkan sorting timestamp, evidence `O_Cancelled/O_Accepted` berasal dari dua case berbeda, atau direct-follow salah diterapkan. Eskalasi pada hari ditemukan.

## 9. Kontribusi non-program A4

- Menulis bagian **metode/penghitungan 11.22, numerator/denominator, interpretasi case-level**, serta cara validasi evidence di Explorer.
- Membuat screenshot panel count/persen dan minimal satu timeline pair sah yang tampak jelas.
- Menyediakan dokumentasi cara melakukan pencarian case dan cara memeriksa `_trace_pos`/highlight.
- Membantu desain alur demo, mereview A1, menguji kasus edge di luar modul A4, dan meninjau laporan seluruh tim.
- Menjelaskan 11.22 dan demonstrasi Case Explorer saat presentasi; hindari menyebut angka hasil yang belum dijalankan.

## 10. Definition of Done A4

- [ ] 11.22 membedakan eventually follows dari adjacency/endpoint.
- [ ] Count menghitung case unik; persentase memakai seluruh case sebagai denominator.
- [ ] Pasangan i<j adalah event nyata dan dapat ditunjukkan di Explorer.
- [ ] Explorer menampilkan trace penuh dalam urutan aslinya, bukan event subset saja.
- [ ] Explorer bisa dipanggil oleh A2/A3/A4 dan menyorot `_row_id` yang benar.
- [ ] T07/T08/T11/T14 dan tambahan lulus; reviewer A1 menyetujui.
- [ ] Screenshot, laporan, dan segmen demo A4 lengkap.

## 11. Prompt untuk coding agent A4

```text
Anda developer Anggota 4 (A4) untuk proyek BPIC17.
Baca panduan kerja PDF yang sudah diubah menjadi Markdown, dokumen teknis,
dan file A4 ini. Kerjakan ordering.py, ex_11_22.py, sequence_panel.py,
case_explorer_panel.py, tests/test_ordering.py.
11.22: case lolos jika O_Cancelled muncul sebelum O_Accepted
pada posisi event asli (i<j) dalam trace yang sama, tidak harus bersebelahan.
Hitung satu kali per case, persentase dari seluruh case aktif.
Buat bukti pasangan event aktual lengkap dengan row IDs, posisi, timestamps.
Case Explorer harus membuka semua event case, dengan highlight row IDs,
dan bisa dipanggil panel A2/A3.
Jangan membangun analisis berdasarkan offer ID, jangan sort timestamp
untuk menggantikan urutan trace asli.
Jalankan test T07/T08/T11/T14 dan laporkan hasil yang benar-benar berjalan,
file berubah, kontrak dengan A1/A2/A3/A5, serta masalah tersisa.
```
