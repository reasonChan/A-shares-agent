from scripts.run_premarket_agent import build_providers, resolve_limit_per_source


def test_build_providers_registers_social_platform_sources():
    providers = build_providers({"premarket": {"providers": ["kaipanla", "xueqiu"]}})

    assert [provider.source for provider in providers] == ["开盘啦最新资讯", "雪球热议"]


def test_build_providers_registers_sina_channel_sources():
    providers = build_providers({"premarket": {"providers": ["sina_finance", "sina_stock", "sina_global"]}})

    assert [provider.source for provider in providers] == ["新浪财经滚动", "新浪股票滚动", "新浪全球财经"]
    assert [provider.lid for provider in providers] == ["2516", "2517", "2518"]


def test_build_providers_registers_tonghuashun_source():
    providers = build_providers({"premarket": {"providers": ["tonghuashun"]}})

    assert [provider.source for provider in providers] == ["同花顺7x24"]


def test_resolve_limit_per_source_prefers_cli_then_config_then_default():
    assert resolve_limit_per_source({"premarket": {"limit_per_source": 80}}, cli_limit=120) == 120
    assert resolve_limit_per_source({"premarket": {"limit_per_source": 80}}, cli_limit=None) == 80
    assert resolve_limit_per_source({"premarket": {}}, cli_limit=None) == 30
