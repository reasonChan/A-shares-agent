from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "web" / "src" / "main.jsx"
API = ROOT / "web" / "src" / "api.js"


def test_premarket_debug_tab_is_available():
    source = MAIN.read_text(encoding="utf-8")

    assert "盘前调试" in source
    assert "PremarketDebugPage" in source
    assert "爬虫/Provider 获取" in source
    assert "落入知识库" in source
    assert "RAG 证据包" in source
    assert "最终结论" in source


def test_premarket_debug_api_client_exists():
    source = API.read_text(encoding="utf-8")

    assert "fetchPremarketDebug" in source
    assert "/api/premarket/debug" in source
