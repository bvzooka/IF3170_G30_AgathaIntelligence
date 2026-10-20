# IF3170_G30_AgathaIntelligence

## Setup
`bash
python -m venv .venv
`

`bash
.\.venv\Scripts\Activate.ps1
`

`bash
python -m pip install -e ".[test]"
`

Lanjut pilih Python: Select Interpreter

Test : 

`bash
python -c "import fastapi; print(fastapi.__version__)"
`

## Run
For Unit testing or other

`bash
python -m app.cli <file-input.json> <nama-algoritma> [opsi]
`

- contoh hill climbing

`bash
python -m app.cli data/examples/small.json hill_climbing --seed 42 --output output/hc-42.json
`

- contoh simulated annealing

`bash
python -m app.cli data/examples/small.json simulated_annealing --seed 43 --params '{"max_iterations": 1000}' --output output/sa-43.json
`

- contoh GA

`bash
python -m app.cli data/examples/small.json genetic_algorithm --seed 44 --params '{"population_size": 50, "max_iterations": 100}' --output output/ga-44.json
`

Menjelankan API : 

`bash 
uvicorn app.main:app --reload
`

buka http://127.0.0.1:8000/docs untuk mencoba POST /runs
