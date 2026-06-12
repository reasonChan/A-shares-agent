import json
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from trading_agent_system.agents.premarket_agent.news_provider import (
    FetchWindow,
    KaipanlaNewsProvider,
    SinaFinanceRollProvider,
    TonghuashunNewsProvider,
    XueqiuHotProvider,
)


def test_kaipanla_provider_parses_latest_news_from_nuxt_payload():
    html = """
    <script type="application/json" data-nuxt-data="nuxt-app">
    [
      ["ShallowReactive", 1],
      {
        "articleData": "{\\"Latest\\":[{\\"ID\\":41455,\\"Title\\":\\"SK海力士设备供应商提出涨价要求\\",\\"CreateTime\\":\\"1781223369\\",\\"ZhaiYao\\":\\"全球存储业资本开支有望迅速突破万亿\\",\\"Sign\\":\\"3\\"}],\\"Flash\\":[{\\"ID\\":41069,\\"Title\\":\\"指数再创新高\\",\\"CreateTime\\":\\"1778496437\\",\\"ZhaiYao\\":\\"\\",\\"Sign\\":\\"1\\"}]}"
      }
    ]
    </script>
    """
    provider = KaipanlaNewsProvider()
    provider._get = lambda url: html

    result = provider.fetch(limit=2)

    assert result.status == "ok"
    assert result.source == "开盘啦最新资讯"
    assert [item.title for item in result.items] == ["SK海力士设备供应商提出涨价要求", "指数再创新高"]
    assert result.items[0].source_tier == "sentiment"
    assert result.items[0].category == "platform_news"
    assert result.items[0].url == "https://www.kaipanla.com/article/41455"
    assert result.items[0].summary == "全球存储业资本开支有望迅速突破万亿"
    assert result.items[0].published_at == datetime.fromtimestamp(1781223369, tz=timezone.utc)
    assert "third_party_platform" in result.items[0].risk_flags


def test_kaipanla_provider_filters_items_to_fetch_window():
    html = """
    <script type="application/json" data-nuxt-data="nuxt-app">
    [
      {
        "articleData": "{\\"Latest\\":[{\\"ID\\":1,\\"Title\\":\\"收盘后题材消息\\",\\"CreateTime\\":\\"1780992000\\",\\"ZhaiYao\\":\\"收盘后\\"},{\\"ID\\":2,\\"Title\\":\\"盘中题材消息\\",\\"CreateTime\\":\\"1781055600\\",\\"ZhaiYao\\":\\"盘中\\"}]}"
      }
    ]
    </script>
    """
    provider = KaipanlaNewsProvider()
    provider._get = lambda url: html
    china_tz = ZoneInfo("Asia/Shanghai")
    window = FetchWindow(
        mode="premarket",
        trading_day=date(2026, 6, 10),
        previous_trading_day=date(2026, 6, 9),
        timezone="Asia/Shanghai",
        window_start=datetime(2026, 6, 9, 15, 0, tzinfo=china_tz),
        window_end=datetime(2026, 6, 10, 9, 30, tzinfo=china_tz),
    )

    result = provider.fetch(limit=10, window=window)

    assert [item.title for item in result.items] == ["收盘后题材消息"]


def test_sina_provider_paginates_until_fetch_window(monkeypatch):
    china_tz = ZoneInfo("Asia/Shanghai")
    window = FetchWindow(
        mode="premarket",
        trading_day=date(2026, 6, 12),
        previous_trading_day=date(2026, 6, 11),
        timezone="Asia/Shanghai",
        window_start=datetime(2026, 6, 11, 15, 0, tzinfo=china_tz),
        window_end=datetime(2026, 6, 12, 9, 30, tzinfo=china_tz),
    )
    pages = {
        "1": [
            {"title": "盘中消息", "intro": "应被过滤", "url": "https://sina.test/1", "ctime": 1781228400},
        ],
        "2": [
            {"title": "开盘前财经消息", "intro": "应进入", "url": "https://sina.test/2", "ctime": 1781227200},
            {"title": "收盘后财经消息", "intro": "应进入", "url": "https://sina.test/3", "ctime": 1781164800},
        ],
        "3": [
            {"title": "过早消息", "intro": "应停止回溯", "url": "https://sina.test/4", "ctime": 1781157600},
        ],
    }
    requested_pages: list[str] = []

    class FakeResponse:
        def __init__(self, payload: str) -> None:
            self.payload = payload

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return self.payload.encode("utf-8")

    def fake_urlopen(request: object, timeout: int) -> FakeResponse:
        url = request.full_url
        page = url.split("page=")[1].split("&")[0]
        requested_pages.append(page)
        payload = {"result": {"status": {"code": 0}, "data": pages[page]}}
        return FakeResponse(json.dumps(payload))

    monkeypatch.setattr("trading_agent_system.agents.premarket_agent.news_provider.urlopen", fake_urlopen)
    provider = SinaFinanceRollProvider(source="新浪财经滚动", lid="2516", category="sina_finance", max_pages=5)

    result = provider.fetch(limit=10, window=window)

    assert requested_pages == ["1", "2", "3"]
    assert [item.title for item in result.items] == ["开盘前财经消息", "收盘后财经消息"]
    assert {item.category for item in result.items} == {"sina_finance"}


def test_tonghuashun_provider_parses_7x24_news_and_filters_window(monkeypatch):
    china_tz = ZoneInfo("Asia/Shanghai")
    window = FetchWindow(
        mode="premarket",
        trading_day=date(2026, 6, 13),
        previous_trading_day=date(2026, 6, 12),
        timezone="Asia/Shanghai",
        window_start=datetime(2026, 6, 12, 15, 0, tzinfo=china_tz),
        window_end=datetime(2026, 6, 13, 9, 30, tzinfo=china_tz),
    )
    pages = {
        "1": [
            {
                "title": "盘中同花顺消息",
                "digest": "09:30 后应过滤",
                "url": "https://news.10jqka.com.cn/after.shtml",
                "ctime": int(datetime(2026, 6, 13, 9, 40, tzinfo=china_tz).timestamp()),
                "tags": [{"name": "A股"}],
                "stock": [{"code": "300750", "name": "宁德时代"}],
            },
        ],
        "2": [
            {
                "title": "窗口内同花顺消息",
                "digest": "15:00 后应进入",
                "url": "https://news.10jqka.com.cn/in-window.shtml",
                "ctime": int(datetime(2026, 6, 12, 16, 0, tzinfo=china_tz).timestamp()),
                "tags": [{"name": "A股"}, {"name": "新能源"}],
                "stock": [{"code": "300750", "name": "宁德时代"}],
            },
        ],
        "3": [
            {
                "title": "过早同花顺消息",
                "digest": "15:00 前应停止回溯",
                "url": "https://news.10jqka.com.cn/too-old.shtml",
                "ctime": int(datetime(2026, 6, 12, 14, 0, tzinfo=china_tz).timestamp()),
                "tags": [{"name": "A股"}],
            },
        ],
    }
    requested_pages: list[str] = []

    class FakeResponse:
        def __init__(self, payload: str) -> None:
            self.payload = payload

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return self.payload.encode("utf-8")

    def fake_urlopen(request: object, timeout: int) -> FakeResponse:
        url = request.full_url
        page = url.split("page=")[1].split("&")[0]
        requested_pages.append(page)
        payload = {"code": "200", "data": {"list": pages[page]}}
        return FakeResponse(json.dumps(payload))

    monkeypatch.setattr("trading_agent_system.agents.premarket_agent.news_provider.urlopen", fake_urlopen)
    provider = TonghuashunNewsProvider(max_pages=5)

    result = provider.fetch(limit=10, window=window)

    assert requested_pages == ["1", "2", "3"]
    assert result.status == "ok"
    assert [item.title for item in result.items] == ["窗口内同花顺消息"]
    assert result.items[0].source == "同花顺7x24"
    assert result.items[0].category == "ths_7x24"
    assert result.items[0].symbols == ["300750"]
    assert "新能源" in result.items[0].sectors


def test_xueqiu_provider_parses_hot_discussions():
    payload = {
        "items": [
            {
                "id": 123,
                "text": "<p>机器人板块盘前讨论升温，资金关注减速器方向。</p>",
                "created_at": 1781223369000,
                "user": {"screen_name": "趋势观察"},
                "target": "https://xueqiu.com/123/456",
            }
        ]
    }
    provider = XueqiuHotProvider()
    provider._get_json = lambda url: payload

    result = provider.fetch(limit=5)

    assert result.status == "ok"
    assert result.source == "雪球热议"
    assert len(result.items) == 1
    assert result.items[0].source == "雪球热议"
    assert result.items[0].source_tier == "sentiment"
    assert result.items[0].title == "机器人板块盘前讨论升温，资金关注减速器方向。"
    assert result.items[0].summary == "趋势观察: 机器人板块盘前讨论升温，资金关注减速器方向。"
    assert result.items[0].url == "https://xueqiu.com/123/456"
    assert result.items[0].published_at == datetime.fromtimestamp(1781223369, tz=timezone.utc)
    assert "sentiment_only" in result.items[0].risk_flags


def test_xueqiu_provider_reports_login_or_waf_error_without_breaking_chain():
    provider = XueqiuHotProvider()
    provider._get_json = lambda url: {
        "error_code": "400016",
        "error_description": "遇到错误，请刷新页面或者重新登录帐号后再试",
    }

    result = provider.fetch(limit=5)

    assert result.status == "failed"
    assert result.items == []
    assert "400016" in result.error
