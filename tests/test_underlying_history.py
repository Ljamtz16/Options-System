from src.options_system import underlying_history as uh

def test_reference_uses_first_observable_open(monkeypatch):
    payload={"bars":{"SPY":[{"t":"2026-01-01T14:30:00Z","o":100.5,"c":101.0},
                            {"t":"2026-01-01T14:31:00Z","o":101.0,"c":999.0}]}}
    monkeypatch.setattr(uh,"stock_bars",lambda *a:(payload,"u"))
    r=uh.spy_reference_at("SPY","s","e")
    assert r["price"]==100.5 and r["field"]=="open"

def test_reference_fails_closed_without_bar(monkeypatch):
    monkeypatch.setattr(uh,"stock_bars",lambda *a:({"bars":{"SPY":[]}},"u"))
    import pytest
    with pytest.raises(RuntimeError): uh.spy_reference_at("SPY","s","e")
