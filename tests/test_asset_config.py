from src.options_system.asset_config import get_asset_config
def test_spy_threshold():assert get_asset_config("SPY").event_threshold==.01
def test_assets_have_independent_thresholds():assert get_asset_config("NVDA").event_threshold!=get_asset_config("SPY").event_threshold
def test_unknown_has_safe_default():assert get_asset_config("MSFT").symbol=="MSFT"
