import pytest
from src.options_system.path_distribution import path_metrics,barrier_touch
def test_path_metrics():
 r=path_metrics(100,[102,101],[99,98],[101,99]);assert r["mfe"]==pytest.approx(.02) and r["mae"]==pytest.approx(-.02) and r["terminal_return"]==pytest.approx(-.01)
def test_barrier_ambiguous():
 assert barrier_touch(100,[102],[98])["label"]=="AMBIGUOUS_SAME_SESSION"
def test_barrier_order_across_days():
 assert barrier_touch(100,[101.2,100],[99.5,98])["label"]=="UP"
