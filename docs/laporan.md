# Laporan BPIC17 Desktop Event Log Analyzer

> Status: integrasi aplikasi dan QA sintetis selesai. Hasil numerik BPIC17 asli hanya boleh diisi setelah aplikasi dijalankan terhadap dataset yang disepakati.

## 1. Pendahuluan dan Tujuan

Aplikasi ini bertujuan menyediakan alur desktop yang dapat direproduksi untuk mengimpor XES, menghitung delapan jawaban BPIC17 dari dataset aktif, menelusuri event pembukti, dan mengekspor hasil konsisten. Pemisahan `core` dan `gui` menjaga agar aturan analitik tidak dihitung ulang pada widget. Sumber dan versi dataset BPIC17 masih harus dilengkapi A1 bersama A5 setelah file final disepakati, kemudian ditinjau A2–A4.

## 2. Dataset dan Reproduksibilitas

- Nama dan sumber dataset:
- Ukuran file:
- SHA-256:
- Tanggal pengujian integrasi sintetis: 21 November 2026
- Versi: Python 3.13.7; PM4Py 2.7.23.13; pandas 3.1.1; PySide6 6.12.0; Windows 11 build 26300
- Commit dasar sebelum pekerjaan A5: `ff7c420`; commit/tag final menunggu perubahan A5 di-commit

## 3. Arsitektur dan Import XES

Diisi oleh A1. Jelaskan validasi atribut, urutan trace, EventStore, timezone, dan metadata.

## 4. Exercise 11.7 A-E

Diisi oleh A2. Sertakan formula cycle time, contains vs endpoint, hasil aktual, dan evidence case.

## 5. Exercise 11.15 dan 11.18

Diisi oleh A3. Sertakan lifecycle complete, resource valid, hasil aktual, dan evidence event.

## 6. Exercise 11.22 dan Case Explorer

Diisi oleh A4. Sertakan eventually-follows, numerator/denominator, persentase, dan pasangan event `i < j`.

## 7. GUI, Export, dan Integrasi

`MainWindow` menyatukan delapan area: Dataset & Status, Overview, Exercise 11.7, Rework 11.15/11.18, Exercise 11.22, Case Explorer, Export, dan About. Satu `EventStore` aktif didistribusikan ke semua panel. Pergantian atau kegagalan dataset langsung menghapus hasil, evidence, metadata export, dan pilihan case sebelumnya.

Pekerjaan import, analisis, serta export dijalankan oleh `WorkerManager` menggunakan `QObject` dan `QThread`. Callback result/error diteruskan kembali ke GUI thread. Setiap panel memakai generation ID sehingga hasil job lama tidak dapat masuk setelah reset atau dataset switch. Progress yang tidak memiliki ukuran numerik ditampilkan sebagai indikator indeterminate.

Export memakai delapan objek `AnalysisResult` yang sama dengan panel dan tidak menghitung ulang event log. Keluaran UTF-8 terdiri dari `summary.csv`, `selected_cases.csv`, dan `evidence.csv`. Evidence menormalisasi nama case dan menggabungkan union columns agar `_row_id`, posisi, timestamp, lifecycle, resource, serta pasangan cancel–accept tetap dapat ditelusuri. Hasil `unavailable/error` menyimpan status, denominator, dan alasan; kolom answer tidak ditulis sebagai nol valid.

Reset menghapus hasil turunan dan Case Explorer tanpa menghapus `EventStore`. Rerun memanggil kembali analitik A2–A4 dari store yang sama, sehingga parser XES tidak dipanggil ulang. About menampilkan versi aplikasi/dependency/OS dan metadata file aktif, termasuk ukuran, jumlah case/event, serta SHA-256.

## 8. Pengujian

Pada 21 November 2026, seluruh suite terkini berjalan dengan hasil `143 passed, 1 warning`. Integration test memverifikasi import XES sintetis, Overview, delapan hasil, evidence Case Explorer, tiga CSV, reset, rerun tanpa parse ulang, invalid dataset reset, dan penolakan callback dataset lama. Navigation test memverifikasi delapan workspace, history, shortcut, status badge, breadcrumb, dan global action bar. Clean-install baseline A5 sebelum navigation shell pada virtual environment Python 3.13 baru menghasilkan `136 passed, 1 warning` dalam 12,70 detik.

Warning berasal dari dependency opsional PM4Py `r4pm`; fallback `rustxes` tetap dapat membaca XES. Detail perintah dan batas verifikasi dicatat dalam `docs/qa_a5.md`. Pengujian terhadap BPIC17 asli belum dilakukan karena file tidak tersedia di repository.

## 9. Perbandingan dengan Referensi

Angka dari materi dosen dipakai sebagai pembanding, bukan expected value yang di-hard-code.

## 10. Keterbatasan dan Risiko

- Hasil numerik BPIC17 asli, performa terhadap file penuh, dan kecocokan dengan referensi belum dapat diklaim tanpa dataset final.
- 11.15/11.18 bergantung pada lifecycle yang dapat dibuktikan dan resource nonblank; data tidak memadai menghasilkan status `unavailable` atau catatan batas bawah.
- Pemilihan target fraud yang ambigu memerlukan input pengguna sebelum delapan hasil siap diekspor.
- Tabel evidence besar dibatasi atau memakai model view; load test terhadap dataset 1,2 juta event masih perlu dilakukan bersama file asli.
- Export mengandung identifier dan evidence yang mungkin sensitif; lokasi hasil harus dikelola pengguna dan tidak di-commit.
- PM4Py menggunakan lisensi AGPL v3 pada versi yang diuji; ketentuan distribusi perlu ditinjau sebelum penggunaan di luar konteks proyek terbuka ini.

## 11. Kesimpulan

Ditulis dan disetujui seluruh anggota setelah validasi akhir.

