import requests
API_URL = "http://127.0.0.1:8000"

def run_algorithm(payload: dict) -> dict:
    response = requests.post(
        f"{API_URL}/runs",
        json=payload,
        timeout=300,
    )

    response.raise_for_status()
    return response.json()