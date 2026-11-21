# QA Anggota 5 — Application Integration dan Export

## Lingkungan uji

- Tanggal: 21 November 2026
- OS: Windows 11 `10.0.26300`
- Python: 3.13.7
- PM4Py: 2.7.23.13
- pandas: 3.1.1
- PySide6: 6.12.0
- pytest: 9.2.0
- Commit dasar: `ff7c420`
- Dataset pengujian: XES sintetis yang dibuat oleh test; BPIC17 asli tidak tersedia

## Hasil yang dijalankan

| Pemeriksaan | Perintah/lingkup | Hasil |
|---|---|---|
| Export core | `python -m pytest tests/test_export.py -q` | 5 passed |
| Export GUI + smoke | export panel, application smoke | 13 passed |
| Integration | import → 8 hasil → evidence → CSV → reset/rerun | 2 passed, 1 warning |
| Regression | `python manage.py test -q` | 136 passed, 1 warning; 7,39 detik |
| Clean install | venv Python 3.13 baru + `pip install -r requirements.txt` + full suite | 136 passed, 1 warning; 12,70 detik |

Warning tunggal berasal dari PM4Py karena `r4pm` tidak dipasang. Pesan PM4Py menyatakan `rustxes` tetap didukung sebagai fallback; import XES pada test berhasil.

## Cakupan reliability

- Callback hasil/error worker kembali ke GUI thread.
- Dataset switch membatalkan pengaruh callback loader lama.
- Reset dan rerun mempertahankan identitas `EventStore` serta tidak memanggil parser ulang.
- Invalid dataset menghapus Overview, hasil A2–A4, Explorer, Export, dan About metadata lama.
- Export ditolak bila delapan hasil belum lengkap atau terdapat exercise duplikat.
- Status `unavailable` mengekspor reason dan denominator tanpa menampilkan count placeholder sebagai jawaban valid.
- Direktori dengan spasi, cancel dialog, path bukan direktori, dan error permission sintetis ditangani.
- Tiga CSV dibaca kembali dengan pandas dan evidence identifier tetap tersedia.

## Batas verifikasi dan handoff

- File BPIC17 asli tidak ada di `data/`; angka delapan exercise, waktu import penuh, konsumsi memori, hash dataset, dan screenshot data asli belum diverifikasi.
- Screenshot A5 menggunakan dataset sintetis dan harus diganti atau dilengkapi saat dataset final tersedia.
- Review silang, rekaman demo, tag final, dan persetujuan jumlah lima anggota tetap memerlukan tindakan tim.
- Sebelum distribusi, tim perlu meninjau kewajiban lisensi AGPL v3 PM4Py.
