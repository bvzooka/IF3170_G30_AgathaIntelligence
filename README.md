# IF3170_G30_AgathaIntelligence

Tugas Besar 1 IF3170 Inteligensi Artifisial: optimasi pemuatan paket ke truk peti kemas (3D bin packing) dengan algoritma local search.

## Deskripsi

Program mencari penempatan paket (posisi dan orientasi) di satu atau lebih truk agar nilai objective maksimum, dengan batasan: paket tidak boleh keluar batas truk, tidak boleh overlap, total berat tidak melebihi kapasitas truk, paket tidak boleh melayang, dan paket fragile tidak boleh menopang paket lain. Paket yang tidak dimuat dibiarkan di luar truk.

Algoritma yang diimplementasikan:
- Hill Climbing (steepest ascent, sideways move, stochastic, random restart)
- Simulated Annealing
- Genetic Algorithm

Objective yang tersedia:
- `value`: jumlah value paket yang dimuat
- `eta_weighted`: value dikalikan bonus ETA (`eta_bonus` dapat diatur)

Bonus multi-truck didukung: input dapat memakai `truck` (satu truk) atau `trucks` (daftar truk).

## Struktur Repository

```
src/backend/app/   backend: core (model, validasi, objective, neighbors), algorithms, API FastAPI, CLI
src/frontend/      frontend Streamlit (input, parameter, visualisasi 3D, grafik objective)
data/test_cases/   testcase small, medium, dan large
data/examples/     contoh input
output/            hasil run (JSON), dikelompokkan per algoritma
```

## Setup

Membutuhkan Python 3.11 atau lebih baru.

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows PowerShell
python -m pip install -e ".[test]"
python -m pip install streamlit plotly requests
```

Paket yang terpasang:

| Perintah | Paket |
|---|---|
| `pip install -e .` | `fastapi`, `uvicorn` (backend dan API) |
| `pip install -e ".[test]"` | tambahan `pytest`, `httpx` (untuk test) |
| `pip install streamlit plotly requests` | frontend: `streamlit` (UI), `plotly` (grafik 3D dan objective), `requests` (memanggil backend) |

## Menjalankan Program

### Lewat frontend

Jalankan backend dan frontend di dua terminal berbeda. Backend harus berjalan lebih dulu di port 8000, karena frontend memanggil `http://127.0.0.1:8000`.

1. Backend:

```bash
cd src/backend
uvicorn app.main:app --reload
```

2. Frontend (pilih salah satu):

```bash
# dari root repository
streamlit run src/frontend/app.py

# atau dari folder frontend
cd src/frontend
py -m streamlit run app.py
```

Buka alamat yang ditampilkan Streamlit, upload file JSON dari `data/test_cases/`, pilih algoritma, objective, seed, dan parameter, lalu klik **Run Algorithm**. Setiap run otomatis disimpan sebagai JSON di folder `output/`.

Nama file hasil: `<dataset>_<mode>_<parameter ringkas>_seed<n>.json`, misalnya `medium-2trucks_eta300_pop50_it100_seed1.json`.

### Lewat CLI

Jalankan dari `src/backend` (path input relatif terhadap folder itu):

```bash
cd src/backend
python -m app.cli <file-input.json> <nama-algoritma> [opsi]
```

Contoh:

```bash
python -m app.cli ../../data/test_cases/small-1truck.json hill_climbing --seed 42 --output ../../output/hc-42.json
python -m app.cli ../../data/test_cases/small-1truck.json simulated_annealing --seed 43 --params '{"max_iterations": 1000}' --output ../../output/sa-43.json
python -m app.cli ../../data/test_cases/small-1truck.json genetic_algorithm --seed 44 --params '{"population_size": 50, "max_iterations": 100}' --output ../../output/ga-44.json
```

Opsi lain: `--objective {value,eta_weighted}` dan `--eta-bonus <angka>`.

Parameter per algoritma:

| Algoritma | Parameter |
|---|---|
| Hill Climbing | `variant` (`steepest`, `sideways`, `stochastic`, `random_restart`), `max_iterations`, `max_sideways_moves`, `max_restarts`, `max_iterations_per_restart` |
| Simulated Annealing | `initial_temperature`, `cooling_rate`, `min_temperature`, `max_iterations`, `max_neighbor_attempts`, `stuck_threshold` |
| Genetic Algorithm | `population_size`, `max_iterations` |

### Lewat API

Setelah backend berjalan, buka http://127.0.0.1:8000/docs untuk mencoba `POST /runs`.

## Pembagian Tugas

| Anggota | NIM | Tugas |
|---|---|---|
| Agatha Tatianingseto | 13524008 | Implementasi Hill Climbing Algorithm; implementasi bonus objective function; implementasi bonus seluruh algoritma Hill Climbing; penulisan laporan |
| Reva Natania Sitohang | 13524098 | Implementasi Simulated Annealing Algorithm; implementasi frontend; penulisan laporan |
| Amanda Aurellia Salsabilla | 13524131 | Implementasi Genetic Algorithm; implementasi bonus multi-truck; penulisan laporan |
