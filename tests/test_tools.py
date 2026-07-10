"""
Unit tests for Database tools and Rules Engine.
"""

import pytest
from tools.db_tools import DatabaseTools
from tools.rules_engine import RulesEngine

def test_rules_engine_stock_health():
    # Critical Understock: <= 30% of min_threshold
    assert RulesEngine.get_stock_health_label(3, 10, 100) == "CRITICAL_UNDERSTOCK"
    assert RulesEngine.get_stock_health_label(3, 10, 100) == "CRITICAL_UNDERSTOCK"
    
    # Understock: < min_threshold and > 30%
    assert RulesEngine.get_stock_health_label(5, 10, 100) == "UNDERSTOCK"
    
    # Overstock: > 90% of max_capacity
    assert RulesEngine.get_stock_health_label(95, 10, 100) == "OVERSTOCK"
    
    # Stable
    assert RulesEngine.get_stock_health_label(50, 10, 100) == "STABLE"

def test_rules_engine_reorder_qty():
    # Understocked, needs reorder
    qty = RulesEngine.calculate_reorder_quantity(current_stock=5, forecast_demand=50, max_capacity=100)
    assert qty > 0
    assert qty <= 95  # capped by capacity

    # Stable, reorder is 0 or low
    qty_stable = RulesEngine.calculate_reorder_quantity(current_stock=90, forecast_demand=5, max_capacity=100)
    assert qty_stable <= 10

def test_rules_engine_supplier_score():
    score_fast_reliable = RulesEngine.evaluate_supplier_score(lead_time=2, reliability=0.98, unit_cost=5.0)
    score_slow_unreliable = RulesEngine.evaluate_supplier_score(lead_time=10, reliability=0.75, unit_cost=5.0)
    
    # Lower score is better, so fast & reliable should be lower than slow & unreliable
    assert score_fast_reliable < score_slow_unreliable
