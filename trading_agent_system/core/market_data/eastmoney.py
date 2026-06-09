from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.error import URLError
from urllib.request import Request, urlopen

from trading_agent_system.schemas import MarketQuote


EASTMONEY_URL = "https://push2.eastmoney.com/api/qt/ulist.np/get"


class EastMoneyMarketDataProvider:
    def __init__(self, timeout_seconds: int = 8) -> None:
        self.timeout_seconds = timeout_seconds

    def fetch_quotes(self, symbols: list[str]) -> list[MarketQuote]:
        if not symbols:
            return []
        secids = ",".join(self._to_secid(symbol) for symbol in symbols)
        query = urlencode(
            {
                "fltt": "2",
                "secids": secids,
                "fields": "f12,f14,f2,f3,f4,f5,f6,f15,f16,f17,f18,f124",
            }
        )
        url = f"{EASTMONEY_URL}?{query}"
        payload = self._fetch_payload(url)
        data = json.loads(payload)
        rows = data.get("data", {}).get("diff", [])
        return [self._row_to_quote(row) for row in rows]

    def _fetch_payload(self, url: str) -> str:
        last_error: Exception | None = None
        for _ in range(2):
            try:
                return self._fetch_with_urllib(url)
            except (OSError, URLError) as error:
                last_error = error
                time.sleep(0.2)
        try:
            return self._fetch_with_curl(url)
        except OSError as error:
            last_error = error
        raise RuntimeError(f"market quote fetch failed: {last_error}")

    def _fetch_with_urllib(self, url: str) -> str:
        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://quote.eastmoney.com/",
                "Accept": "application/json,text/plain,*/*",
            },
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            return response.read().decode("utf-8")

    def _fetch_with_curl(self, url: str) -> str:
        completed = subprocess.run(
            [
                "curl",
                "-sS",
                "--connect-timeout",
                str(self.timeout_seconds),
                "--max-time",
                str(self.timeout_seconds + 2),
                "-H",
                "User-Agent: Mozilla/5.0",
                "-H",
                "Referer: https://quote.eastmoney.com/",
                url,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0 or not completed.stdout.strip():
            raise OSError(completed.stderr.strip() or f"curl exited {completed.returncode}")
        return completed.stdout

    def _row_to_quote(self, row: dict[str, Any]) -> MarketQuote:
        symbol = str(row.get("f12", ""))
        market = self._market_for_symbol(symbol)
        quote_ts = self._timestamp(row.get("f124"))
        now_ts = int(time.time())
        delay = now_ts - int(row["f124"]) if row.get("f124") else None
        return MarketQuote(
            symbol=f"{symbol}.{market}" if market != "UNKNOWN" else symbol,
            name=str(row.get("f14", symbol)),
            market=market,
            kind=self._kind_for_symbol(symbol),
            price=self._clean(row.get("f2")),
            change=self._clean(row.get("f4")),
            change_pct=self._clean(row.get("f3")),
            open=self._clean(row.get("f17")),
            previous_close=self._clean(row.get("f18")),
            high=self._clean(row.get("f15")),
            low=self._clean(row.get("f16")),
            volume=self._clean(row.get("f5")),
            amount=self._clean(row.get("f6")),
            quote_ts=quote_ts,
            source="eastmoney",
            is_realtime=delay is not None and delay < 90,
            delay_seconds=delay,
        )

    def _to_secid(self, symbol: str) -> str:
        code, market = self._split_symbol(symbol)
        if market == "SH":
            return f"1.{code}"
        if market == "SZ":
            return f"0.{code}"
        if code.startswith(("5", "6", "9")):
            return f"1.{code}"
        return f"0.{code}"

    def _split_symbol(self, symbol: str) -> tuple[str, str]:
        normalized = symbol.strip().upper()
        if "." in normalized:
            code, market = normalized.split(".", 1)
            return code, market
        return normalized, self._market_for_symbol(normalized)

    def _market_for_symbol(self, code: str) -> str:
        if code.startswith(("5", "6", "9")) or code in {"000001", "000300"}:
            return "SH"
        if code.startswith(("0", "1", "2", "3")) or code in {"399001", "399006"}:
            return "SZ"
        return "UNKNOWN"

    def _kind_for_symbol(self, code: str) -> str:
        if code in {"000001", "000300", "399001", "399006"}:
            return "index"
        if code.startswith(("5", "1")):
            return "fund"
        if code.startswith(("0", "3", "6")):
            return "stock"
        return "unknown"

    def _timestamp(self, value: object) -> datetime | None:
        if not value or value == "-":
            return None
        return datetime.fromtimestamp(int(value), timezone.utc)

    def _clean(self, value: object) -> float | None:
        if value in (None, "-", ""):
            return None
        return float(value)
