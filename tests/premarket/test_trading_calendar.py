from datetime import date

from trading_agent_system.agents.premarket_agent.trading_calendar import TradingCalendarService


def test_premarket_window_uses_previous_trading_day_and_auction_end():
    service = TradingCalendarService()

    window = service.build_window(date(2026, 6, 8))

    assert window.previous_trading_day == date(2026, 6, 5)
    assert window.window_start.isoformat() == "2026-06-05T15:00:00+08:00"
    assert window.auction_end.isoformat() == "2026-06-08T09:25:00+08:00"


def test_premarket_window_skips_configured_holiday():
    service = TradingCalendarService(holidays=["2026-06-08"])

    window = service.build_window(date(2026, 6, 9))

    assert window.previous_trading_day == date(2026, 6, 5)


def test_calendar_exposes_spec_named_window_and_next_trading_day():
    service = TradingCalendarService(holidays=["2026-06-10"])

    window = service.build_premarket_window(date(2026, 6, 11))

    assert window.window_start.isoformat() == "2026-06-09T15:00:00+08:00"
    assert service.next_trading_day(date(2026, 6, 9)) == date(2026, 6, 11)
