from fastapi.testclient import TestClient
from pathlib import Path
import importlib.util
import sys

APP_DIR = Path(__file__).resolve().parents[1]
# Ensure app dir is importable for local imports (e.g., events.py)
APP_DIR_STR = str(APP_DIR)
if APP_DIR_STR not in sys.path:
    sys.path.insert(0, APP_DIR_STR)
MAIN_PATH = APP_DIR / "main.py"

spec = importlib.util.spec_from_file_location("catalog_main", str(MAIN_PATH))
catalog_main = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(catalog_main)  # type: ignore[attr-defined]
app = catalog_main.app


client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_and_get_product():
    payload = {"name": "Widget", "price": 9.99}
    r = client.post("/products", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["id"] == "p-1"
    assert data["name"] == payload["name"]

    r2 = client.get(f"/products/{data['id']}")
    assert r2.status_code == 200
    got = r2.json()
    assert got["id"] == data["id"]


def test_update_product():
    # Create first
    r = client.post("/products", json={"name": "A", "price": 1.0})
    assert r.status_code == 201
    pid = r.json()["id"]

    # Update name and price
    r2 = client.put(f"/products/{pid}", json={"name": "B", "price": 2.5})
    assert r2.status_code == 200
    body = r2.json()
    assert body["name"] == "B"
    assert body["price"] == 2.5

    # Get should reflect updated values (may be cached)
    r3 = client.get(f"/products/{pid}")
    assert r3.status_code == 200
    assert r3.json()["name"] == "B"


def test_search_empty_results():
    r = client.get("/search", params={"q": "foo"})
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == "foo"
    assert body["results"] == []
