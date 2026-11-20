# Anggota 2 — Case Analytics: Cycle Time dan Exercise 11.7 A–E

**Owner:** A2 · **Reviewer silang:** A3 · **Estimasi:** 12 poin · **Fitur:** F03, fungsi durasi bersama, evidence dan unit test · **Jadwal:** D1–D7 (7 hari kalender).

## 1. Tujuan dan sumber kebenaran

Implementasikan **lima jawaban Exercise 11.7** dari event log aktif serta mean duration yang dihitung dari trace lengkap. Baca `01_PANDUAN_KERJA_IDENTIK_PDF.md` bagian 02, 04–06, 08–10, Lampiran A–D dan `02_DOKUMENTASI_TEKNIS.md` bagian 3–5, 7–10 sebelum menyentuh kode.

**Tidak boleh:** menggunakan angka rujukan sebagai konstanta, memaksa success/refusal eksklusif, menganggap case canceled hanya karena pernah `O_Cancelled`, atau menghitung duration setelah event log dipangkas berdasarkan activity.

## 2. File milik A2

| File | Isi | Handoff |
|---|---|---|
| `src/core/cycle_time.py` | `get_case_durations(store)`; per-case min/max/duration_days | A1 untuk overview; A2 untuk semua subsoal |
| `src/core/ex_11_7.py` | A–E filter case, agregasi, evidence | A5 GUI shell; A4 Explorer |
| `src/gui/panels/exercise_11_7_panel.py` | Lima kartu/subtab hasil, case table, inspect event | A5 integrasi navigasi |
| `tests/test_11_7.py` | Test T01, T02, T03, T12; tambahan mean empty dan duplicate | A5 regression |
| `docs/laporan.md` (bagian milik A2) | Metode, tabel hasil dan pembahasan soal 11.7 | Tim penyunting bersama |

Kontrak `src/core/result.py` adalah **milik bersama**, bukan file untuk dimodifikasi diam-diam. Jika A1 belum membuat EventStore, gunakan fixture bersama yang mengikuti kontrak.

## 3. Definisi tepat untuk tiap soal

| ID | Predicate terhadap **case/trace utuh** | Output wajib |
|---|---|---|
| 11.7 A | Semua case unik dari log aktif | Total case unik dan denominator |
| 11.7 B | Semua case dengan durasi dari seluruh event | Mean case duration dalam hari, jumlah case |
| 11.7 C | Case mengandung **setidaknya satu** `O_Accepted` | Count, mean hari, case IDs, event bukti |
| 11.7 D | Case mengandung **setidaknya satu** `O_Refused` | Count, mean hari, case IDs, event bukti |
| 11.7 E | **Event terakhir** case adalah `O_Cancelled` berdasarkan `_trace_pos` | Count, mean hari, case IDs, bukti endpoint |

**Identitas aktivitas:** string `O_Accepted`, `O_Refused`, dan `O_Cancelled` berbeda dari `A_Accepted`, `A_Cancelled`. Jangan mencampur label application dan offer.

**Overlap:** satu case dengan O_Refused dan O_Accepted harus bisa lolos C dan D sekaligus. Count pada C/D adalah **jumlah case**, bukan banyaknya event, dan tidak dijumlahkan untuk memperoleh total proses.

### 3.1. Cycle time lengkap

Untuk setiap case `c`:

```text
duration_days(c) = (
    MAX(time:timestamp dari seluruh event c)
  - MIN(time:timestamp dari seluruh event c)
).total_seconds() / 86400
```

- Jangan menggunakan `max-min` setelah pemfilteran aktivitas, sebab event pertama/terakhir bisa terpotong.
- Case berisi satu event mempunyai durasi `0` hari.
- Jangan salah menghitung rata-rata **event**; rata-rata ialah `sum(duration_days per case) / jumlah case`.
- Tampilkan satuan **hari** dan presisi; pembulatan hanya pada tampilan, bukan penyimpanan nilai inti.
- Bila tidak ada case terpilih, `mean_days=None` dan tampilkan `N/A`.
- Data timezone-aware harus dibandingkan sebagai instan waktu yang benar; kerjakan bersama kebijakan timestamp A1.

### 3.2. Pseudocode yang harus tercermin dalam implementasi

```python
# Sketsa domain, bukan kode siap pakai; field mengikuti EventStore D1.
events = store.events
case_duration = get_case_durations(store)  # tabel satu baris per case
all_cases = set(events["case:concept:name"].unique())

accepted_cases = set(events.loc[
    events["concept:name"] == "O_Accepted", "case:concept:name"])
refused_cases = set(events.loc[
    events["concept:name"] == "O_Refused", "case:concept:name"])

# Endpoint memakai event terakhir yang sudah diberi _trace_pos oleh A1.
last_events = (
    events.sort_values(["case:concept:name", "_trace_pos"], kind="stable")
          .groupby("case:concept:name", sort=False)
          .tail(1)
)
canceled_cases = set(last_events.loc[
    last_events["concept:name"] == "O_Cancelled", "case:concept:name"])
```

Pseudocode ini **belum** merupakan implementasi lengkap untuk `AnalysisResult` atau evidence. Fungsi nyata harus memvalidasi `EventStore`, menghasilkan result yang disepakati, dan menangani empty log.

## 4. Kontrak hasil dan bukti

Antarmuka yang disepakati D1:

```python
def get_case_durations(store) -> "pandas.DataFrame": ...
def run_11_7(store) -> "list[AnalysisResult]": ...   # 5 hasil berurutan A,B,C,D,E
```

Setiap result harus berisi: `exercise_id`, `rule_description`, `count`, `denominator`, `case_ids`, `mean_days` (jika berlaku), `percentage=None`, `evidence`, `status`, `notes`.

Evidence minimum:

- **C:** satu atau beberapa event `O_Accepted` yang membuktikan case lolos, sertakan `_row_id`/`_trace_pos`.
- **D:** analog untuk `O_Refused`.
- **E:** **satu event paling akhir** dalam trace, bukan sembarang event cancel sebelumnya.
- **A/B:** daftar case dan duration cache cukup; tidak perlu menyalin semua event sebagai evidence.

Buat API untuk tombol “Lihat case”: kirim `case_id` ke `CaseExplorerPanel` milik A4. A2 tidak membuat Case Explorer kedua.

## 5. UI yang wajib dihasilkan sendiri

Panel A2 tidak hanya menampilkan angka. Minimum tampilkan:

1. Subtab/baris untuk A, B, C, D, E yang bisa dijalankan dari dataset aktif tanpa edit kode.
2. Tiap hasil: definisi filter yang mudah dipahami, jumlah case terpilih, mean hari (B–E), denominator, status dan catatan jika tidak valid.
3. Tabel `case_id` dengan pencarian; tombol `Buka kasus` menuju Explorer A4.
4. Rerun atau reset tampilan hasil tanpa impor ulang XES.
5. Setelah ganti dataset, hilangkan hasil lama; jangan mengira old result masih milik file XES baru.

Gunakan template reusable widget dari A5; gunakan worker bila komputasi pada dataset asli memakan waktu. UI dilarang menghitung groupby sendiri.

## 6. Timeline A2 tujuh hari

| Hari | Aktivitas spesifik | Gate yang bisa ditunjukkan |
|---|---|---|
| D1 | Kontrak `get_case_durations`/`run_11_7`, fixture T01/T02/T03, kesepakatan timestamp dengan A1, mock result A5 | Fungsi bisa dipanggil terhadap fixture |
| D2 | Implementasi cycle time, contains, endpoint, semua lima result, evidence awal | Test core 11.7 lulus |
| D3 | Selesaikan panel A–E, tombol case, status, unit test dan review A3 | Demo lima jawaban pada log sintetis |
| D4 | Merge, uji end-to-end: import → 11.7 → Explorer → CSV, tulis metode laporan | Tersambung dengan A1/A4/A5 |
| D5 | Jalankan dataset BPIC17 nyata; simpan mean penuh, count, sample evidence; bandingkan slide | Tabel aktual vs referensi tersedia |
| D6 | Perbaiki bug, cross-review A3, screenshot, penjelasan pembulatan, laporan 11.7 | Test regresi lulus, reviewer setuju |
| D7 | Pemeriksaan re-import, demo A–E, review laporan akhir dan paket serah | Tidak ada hard-coded result |

## 7. Pengujian minimal

| Test | Input | Expected |
|---|---|---|
| **T01** | satu case dengan dua `O_Accepted` | C menghitung 1 case, bukan 2 |
| **T02** | `O_Cancelled` lalu aktivitas lain | E **tidak** memilih case |
| **T03** | satu case memiliki `O_Refused` dan `O_Accepted` | C dan D **sama-sama** boleh memilih |
| **T12** | case berisi satu event | duration = 0 hari |
| Tambahan | C berisi activity target di tengah trace | mean tetap memakai awal–akhir seluruh trace |
| Tambahan | subset contains tidak punya case | count=0, mean=N/A; status jelas |
| Tambahan | timestamp timezone-aware, hasil satuan hari | durasi tidak bergeser karena timezone |
| Tambahan | dua event timestamp sama dengan urutan berbeda | endpoint mengikuti `_trace_pos` A1 |

```bash
python -m pytest tests/test_11_7.py -q
python -m pytest -q
```

**Acuan historis dari materi untuk REVIEW saja:** A 31.509; B 21,9 hari; C 17.228 dan 18,1 hari; D 3.720 dan 16,8 hari; E 4.436 dan 23 hari. Hasil aktual **harus dihitung**, bukan disetel untuk cocok.

## 8. Dependensi dan komunikasi

- **Butuh dari A1:** EventStore valid, `_trace_pos`, timestamp type, per-case grouping, availability file.
- **Butuh dari A5:** template panel, cara status/worker, signature signal, standar result card dan tabel.
- **Butuh dari A4:** endpoint untuk `Buka kasus(case_id)` dan highlight `_row_id`.
- **Diberikan ke A1:** per-case duration service untuk overview/cache.
- **Diberikan ke A5:** daftar lima `AnalysisResult` dan evidence DataFrame untuk tiga jenis CSV.
- **Reviewer A3:** periksa apakah semantik endpoint dan mean benar serta hasil dapat direproduksi.

**Stop & lapor:** format trace tidak konsisten; A1 mengganti `_trace_pos` setelah D1; hasil mean berubah setelah activity filtering; GUI menampilkan count event bukannya case.

## 9. Pekerjaan non-program A2 — bukan diserahkan pada A5

- Menulis bagian laporan **definisi, metode dan hasil 11.7 A–E**, dilengkapi formula, tabel aktual dan contoh case.
- Screenshot panel semua lima subsoal, minimal satu case evidence, dan perbandingan materi BPIC17.
- Menyiapkan narasi demo singkat tentang *contains vs endpoint* dan rata-rata trace utuh.
- Cross-review pekerjaan A3 dan menambah satu pengujian di luar scope A2.
- Mengikuti validasi BPIC17, peer review laporan, dan persetujuan akhir bersama seluruh anggota.

## 10. Definition of Done A2

- [ ] Lima jawaban benar dihitung dari log aktif dan tersedia melalui UI.
- [ ] Fungsi duration memakai seluruh trace, dihitung per case dan tanpa mengubah event store.
- [ ] C/D tidak eksklusif; E menggunakan event paling akhir.
- [ ] Output `AnalysisResult` konsisten dengan kontrak, evidence dan case IDs dapat dibuka.
- [ ] T01–T03, T12 dan tes tambahan lulus; PR direview A3.
- [ ] Hasil BPIC17 dibedakan dari benchmark slide, tanpa angka statis.
- [ ] Screenshot, bagian laporan, dan segmen demo A2 selesai.

## 11. Prompt untuk coding agent A2

```text
Anda berperan sebagai Anggota 2: Case Analytics BPIC17.
Baca 01_PANDUAN_KERJA_IDENTIK_PDF.md, 02_DOKUMENTASI_TEKNIS.md, dan file A2 ini.
Implementasikan cycle_time.py, ex_11_7.py, exercise_11_7_panel.py,
tests/test_11_7.py dengan kontrak EventStore/AnalysisResult yang telah disepakati.
Pastikan: 11.7 A unique cases; B rata-rata durasi semua case;
C contains O_Accepted; D contains O_Refused (boleh overlap);
E event terakhir _trace_pos adalah O_Cancelled.
Gunakan trace UTUH untuk duration meski yang dipilih case berdasarkan event tertentu.
Sediakan evidence dengan _row_id dan tombol membuka Case Explorer A4.
Lakukan unit test nyata (T01/T02/T03/T12), laporkan hasil, file diubah,
API ekspor, dan blocker. Jangan hard-code angka referensi dan jangan ubah modul A3/A4.
```
