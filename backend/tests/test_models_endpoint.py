from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_list_models_endpoint_returns_catalog():
    response = client.get("/api/v1/models/")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload, "Models endpoint should return at least one model"

    first = payload[0]
    for key in ("id", "provider", "display_name", "description"):
        assert key in first

    model_ids = {model["id"] for model in payload}
    assert {"gemini-2.5-pro", "gpt-5", "claude-opus-4.1", "grok-4"}.issubset(model_ids)

