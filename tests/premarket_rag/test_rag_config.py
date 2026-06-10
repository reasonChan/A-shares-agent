from pathlib import Path

import yaml


def test_rag_config_enables_qdrant_local_mode():
    payload = yaml.safe_load(Path("configs/rag.premarket.yaml").read_text(encoding="utf-8"))

    assert payload["rag"]["enabled"] is True
    assert payload["rag"]["vector_store"]["backend"] == "qdrant"
    assert payload["rag"]["vector_store"]["mode"] == "local"
    assert payload["rag"]["embedding"]["provider"] == "deterministic"
    assert payload["rag"]["embedding"]["dimension"] == 384
