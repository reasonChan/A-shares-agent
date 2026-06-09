from __future__ import annotations

import re
import time
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

from trading_agent_system.schemas import MarketQuote


TENCENT_URL = "https://qt.gtimg.cn/q="
CHINA_TZ = timezone(timedelta(hours=8))


class TencentMarketDataProvider:
    def __init__(self, timeout_seconds: int = 8) -> None:
        self.timeout_seconds = timeout_seconds

    def fetch_quotes(self, symbols: list[str]) -> list[MarketQuote]:
        if not symbols:
            return []
        query = ",".join(self._to_query_symbol(symbol) for symbol in symbols)
        request = Request(
            f"{TENCENT_URL}{query}",
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://gu.qq.com/",
                "Accept": "text/plain,*/*",
            },
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            payload = response.read().decode("gbk", errors="ignore")
        quotes: list[MarketQuote] = []
        for match in re.finditer(r'v_([a-z]{2})(\d{6})="([^"]*)"', payload):
            market_code, code, raw = match.groups()
            parts = raw.split("~")
            if len(parts) < 35:
                continue
            quotes.append(self._parts_to_quote(market_code, code, parts))
        return quotes

    def _parts_to_quote(self, market_code: str, code: str, parts: list[str]) -> MarketQuote:
        quote_ts = self._timestamp(parts[30] if len(parts) > 30 else "")
        delay = int(time.time() - quote_ts.timestamp()) if quote_ts else None
        market = "SH" if market_code == "sh" else "SZ" if market_code == "sz" else "UNKNOWN"
        return MarketQuote(
            symbol=f"{code}.{market}" if market != "UNKNOWN" else code,
            name=parts[1] or code,
            market=market,
            kind=self._kind_for_symbol(code),
            price=self._clean(parts[3]),
            change=self._clean(parts[31]),
            change_pct=self._clean(parts[32]),
            open=self._clean(parts[5]),
            previous_close=self._clean(parts[4]),
            high=self._clean(parts[33]),
            low=self._clean(parts[34]),
            volume=self._clean(parts[36]) if len(parts) > 36 else self._clean(parts[6]),
            amount=self._clean(parts[37]) if len(parts) > 37 else None,
            quote_ts=quote_ts,
            source="tencent",
            is_realtime=delay is not None and delay < 90,
            delay_seconds=delay,
        )

    def _to_query_symbol(self, symbol: str) -> str:
        normalized = symbol.strip().lower().replace(".", "")
        if normalized.startswith(("sh", "sz")):
            return normalized
        code = normalized[:6]
        if symbol.upper().endswith(".SH") or code.startswith(("5", "6", "9")) or code in {"000001", "000300"}:
            return f"sh{code}"
        return f"sz{code}"

    def _kind_for_symbol(self, code: str) -> str:
        if code in {"000001", "000300", "399001", "399006"}:
            return "index"
        if code.startswith(("5", "1")):
            return "fund"
        if code.startswith(("0", "3", "6")):
            return "stock"
        return "unknown"

    def _timestamp(self, value: str) -> datetime | None:
        if not value:
            return None
        return datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=CHINA_TZ).astimezone(timezone.utc)

    def _clean(self, value: str) -> float | None:
        if value in ("", "-"):
            return None
        return float(value)
