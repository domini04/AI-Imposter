from app.services import model_catalog


def test_list_models_returns_expected_structure():
    models = model_catalog.list_models()

    assert isinstance(models, list)
    assert models, "Model catalog should not be empty"

    required_keys = {"id", "provider", "display_name", "description"}
    for model in models:
        assert required_keys.issubset(model.keys())


def test_model_catalog_contains_expected_ids():
    model_ids = {model["id"] for model in model_catalog.list_models()}

    assert {"gemini-2.5-pro", "gpt-5", "claude-opus-4.1", "grok-4"}.issubset(model_ids)
from app.services import model_catalog


def test_list_models_returns_expected_structure():
    models = model_catalog.list_models()

    assert isinstance(models, list)
    assert models, "Model catalog should not be empty"

    required_keys = {"id", "provider", "display_name", "description"}
    for model in models:
        assert required_keys.issubset(model.keys())


def test_model_catalog_contains_expected_ids():
    model_ids = {model["id"] for model in model_catalog.list_models()}

    assert {"gemini-2.5-pro", "gpt-5", "claude-opus-4.1", "grok-4"}.issubset(model_ids)

