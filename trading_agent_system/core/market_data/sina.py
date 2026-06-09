from __future__ import annotations

import json
from typing import Literal
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from trading_agent_system.schemas import StockQuote


SINA_STOCK_URL = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"
SORT_FIELDS = {"symbol", "trade", "changepercent", "volume", "amount", "turnoverratio"}


class SinaMarketDataProvider:
    def __init__(self, timeout_seconds: int = 10) -> None:
        self.timeout_seconds = timeout_seconds

    def fetch_stock_page(
        self,
        page: int = 1,
        page_size: int = 50,
        sort: Literal["symbol", "trade", "changepercent", "volume", "amount", "turnoverratio"] = "changepercent",
        asc: bool = False,
    ) -> dict[str, object]:
        safe_page = max(1, page)
        safe_page_size = min(max(10, page_size), 100)
        safe_sort = sort if sort in SORT_FIELDS else "changepercent"
        params = {
            "page": safe_page,
            "num": safe_page_size,
            "sort": safe_sort,
            "asc": 1 if asc else 0,
            "node": "hs_a",
            "_s_r_a": "page",
        }
        request = Request(
            f"{SINA_STOCK_URL}?{urlencode(params)}",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://finance.sina.com.cn/",
                "Accept": "application/json,text/plain,*/*",
            },
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            payload = response.read().decode("utf-8", errors="ignore")
        rows = json.loads(payload)
        quotes = [self._row_to_quote(row) for row in rows if isinstance(row, dict)]
        return {
            "page": safe_page,
            "page_size": safe_page_size,
            "sort": safe_sort,
            "asc": asc,
            "has_next": len(quotes) == safe_page_size,
            "quotes": quotes,
            "source": "sina",
        }

    def _row_to_quote(self, row: dict[str, object]) -> StockQuote:
        symbol = str(row.get("symbol") or "")
        code = str(row.get("code") or symbol[-6:] or "")
        return StockQuote(
            symbol=self._display_symbol(symbol, code),
            code=code,
            name=str(row.get("name") or code),
            market=self._market(symbol),
            price=self._clean(row.get("trade")),
            change=self._clean(row.get("pricechange")),
            change_pct=self._clean(row.get("changepercent")),
            open=self._clean(row.get("open")),
            previous_close=self._clean(row.get("settlement")),
            high=self._clean(row.get("high")),
            low=self._clean(row.get("low")),
            volume=self._clean(row.get("volume")),
            amount=self._clean(row.get("amount")),
            turnover_ratio=self._clean(row.get("turnoverratio")),
            pe=self._clean(row.get("per")),
            pb=self._clean(row.get("pb")),
            market_cap=self._clean(row.get("mktcap")),
            float_market_cap=self._clean(row.get("nmc")),
            tick_time=str(row.get("ticktime") or ""),
            source="sina",
        )

    def _display_symbol(self, symbol: str, code: str) -> str:
        market = self._market(symbol)
        return f"{code}.{market}" if market != "UNKNOWN" else code

    def _market(self, symbol: str) -> str:
        if symbol.startswith("sh"):
            return "SH"
        if symbol.startswith("sz"):
            return "SZ"
        if symbol.startswith("bj"):
            return "BJ"
        return "UNKNOWN"

    def _clean(self, value: object) -> float | None:
        if value in (None, "", "-"):
            return None
        return float(value)
