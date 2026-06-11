from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IA_SOURCE = ROOT / "web" / "src" / "consoleInformationArchitecture.js"
README = ROOT / "README.md"
BOUNDARIES_DOC = ROOT / "docs" / "architecture" / "agent-boundaries.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_pipeline_order_and_roles_are_explicit():
    source = read(IA_SOURCE)
    expected_order = [
        "premarket",
        "intraday",
        "risk",
        "broker",
        "review",
    ]
    positions = [source.index(f"id: '{item}'") for item in expected_order]

    assert positions == sorted(positions)
    assert "role: 'Agent'" in source
    assert "role: 'Service'" in source
    assert "title: '风控审批'" in source
    assert "title: '模拟执行'" in source
    assert "RiskGateway 不是 Agent" in source
    assert "PaperBroker 不是 Agent" in source


def test_console_has_three_named_sections():
    source = read(IA_SOURCE)

    assert "今日交易流水线" in source
    assert "盘前知识系统" in source
    assert "运维与审计" in source
    assert "信息源覆盖" in source
    assert "RAG 证据包" in source
    assert "规则/历史案例" in source
    assert "Approval Queue" in source


def test_docs_explain_agent_service_capability_boundaries():
    readme = read(README)
    boundaries = read(BOUNDARIES_DOC)

    assert "项目功能边界" in readme
    assert "PremarketAgent -> IntradayAgent -> RiskGateway -> PaperBroker -> ReviewAgent" in readme
    assert "RiskGateway 是确定性风控服务，不是业务 Agent" in readme
    assert "PaperBroker 是模拟执行服务，不是业务 Agent" in readme

    assert "交易流水线" in boundaries
    assert "盘前知识系统" in boundaries
    assert "运维与审计" in boundaries
    assert "RiskGateway 不是 Agent" in boundaries
    assert "RAG、信息源、知识库、PremarketContext 是能力模块" in boundaries
