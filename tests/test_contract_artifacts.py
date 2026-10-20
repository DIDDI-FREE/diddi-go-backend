from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit

module_spec = spec_from_file_location(
    "contract_artifacts", Path(__file__).resolve().parents[1] / "tools/contract_artifacts.py"
)
artifacts = module_from_spec(module_spec)
module_spec.loader.exec_module(artifacts)


@pytest.mark.parametrize("body", ["", "END START", "START START END", "START END END"])
def test_invalid_markers_preserve_document(tmp_path, body):
    path = tmp_path / "contract.md"
    original = body.replace("START", "<!-- generated:test:start -->").replace("END", "<!-- generated:test:end -->")
    path.write_text(original, encoding="utf-8")
    with pytest.raises(ValueError):
        artifacts.update_generated_section(path, "test", "replacement")
    assert path.read_text(encoding="utf-8") == original


def test_generation_preserves_manual_content_and_four_file_layout(tmp_path, monkeypatch):
    monkeypatch.setattr(artifacts, "ROOT", tmp_path)
    directory = tmp_path / "docs/api"
    directory.mkdir(parents=True)
    for filename, marker in [("API_CONTRACT.md", "http-inventory"), ("open-questions.md", "operation-gaps")]:
        (directory / filename).write_text(
            f"Décision humaine conservée.\n<!-- generated:{marker}:start -->\n"
            f"obsolete\n<!-- generated:{marker}:end -->\nConclusion manuelle.\n",
            encoding="utf-8",
        )
    raw = {
        "openapi": "3.1.0",
        "info": {"title": "Test", "version": "1"},
        "paths": {"/health": {"get": {"operationId": "health", "responses": {"200": {"description": "OK"}}}}},
    }
    artifacts.write_artifacts(raw)
    first = {path.name: path.read_bytes() for path in directory.iterdir()}
    assert set(first) == {"API_CONTRACT.md", "open-questions.md", "openapi.yaml", "asyncapi.yaml"}
    assert not (tmp_path / "docs/realtime").exists()
    for filename in ("API_CONTRACT.md", "open-questions.md"):
        content = (directory / filename).read_text(encoding="utf-8")
        assert content.startswith("Décision humaine conservée.\n")
        assert content.endswith("Conclusion manuelle.\n")
        assert "obsolete" not in content
    assert "/health" in yaml.safe_load(first["openapi.yaml"])["paths"]
    assert yaml.safe_load(first["asyncapi.yaml"])["asyncapi"] == "3.0.0"
    artifacts.write_artifacts(raw)
    assert first == {path.name: path.read_bytes() for path in directory.iterdir()}


def test_score_contract_routes_have_no_generated_unknowns() -> None:
    raw = {
        "openapi": "3.1.0",
        "info": {"title": "Test", "version": "1"},
        "paths": {
            "/internal/v1/scores/users/{user_id}": {
                "get": {"operationId": "get_user_scores", "responses": {"200": {"description": "OK"}}}
            }
        },
    }

    spec, gaps = artifacts.http_contract(raw)

    assert "UNKNOWN" not in str(spec["paths"]["/internal/v1/scores/users/{user_id}"]["get"]["x-contract"])
    assert gaps == ["| `GET /internal/v1/scores/users/{user_id}` | Aucun UNKNOWN détecté |"]
