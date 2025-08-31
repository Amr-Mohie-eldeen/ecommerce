from fastapi.testclient import TestClient
from pathlib import Path
import importlib.util
import sys

APP_DIR = Path(__file__).resolve().parents[1]
APP_DIR_STR = str(APP_DIR)
if APP_DIR_STR not in sys.path:
    sys.path.insert(0, APP_DIR_STR)
MAIN_PATH = APP_DIR / "main.py"

# Avoid module name collision with other apps using package name 'app'
sys.modules.pop("app", None)

spec = importlib.util.spec_from_file_location("orders_main", str(MAIN_PATH))
orders_main = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(orders_main)  # type: ignore[attr-defined]
app = orders_main.app

client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_and_get_order():
    payload = {
        "customer_id": "c-1",
        "currency": "USD",
        "items": [
            {"product_id": "p-1", "quantity": 2, "unit_price": 5.0},
            {"product_id": "p-2", "quantity": 1, "unit_price": 10.0},
        ],
    }
    r = client.post("/orders", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["id"] == "o-1"
    assert data["total_amount"] == 20.0
    assert len(data["items"]) == 2

    r2 = client.get(f"/orders/{data['id']}")
    assert r2.status_code == 200
    got = r2.json()
    assert got["id"] == data["id"]
    assert got["total_amount"] == 20.0
