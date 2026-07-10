"""Tests for the issue-driven chatbot: parsing, answers and scenario runs."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot import bot


def test_help_intent():
    assert bot.parse("help")["intent"] == "help"
    assert bot.parse("")["intent"] == "help"
    out = bot.answer("help")
    assert "Restocking assistant" in out
    assert "scenario" in out.lower()


def test_scenario_intent():
    q = bot.parse("please run scenario 3")
    assert q == {"intent": "scenario", "n": 3}


def test_store_and_product_matching():
    q = bot.parse("analyze bottled water at store 1001")
    assert q["intent"] == "analyze"
    assert q["store"] == "Store_1001"
    assert q["product"]["ProductID"] == "Prod_002"

    q = bot.parse("restock Prod_003 at Store_1002")
    assert q["intent"] == "analyze"
    assert q["store"] == "Store_1002"
    assert q["product"]["ProductID"] == "Prod_003"


def test_status_intent():
    q = bot.parse("status of store 1004")
    assert q["intent"] == "status"
    assert q["store"] == "Store_1004"
    out = bot.answer("status of store 1004")
    assert "Stock health at Store_1004" in out
    assert "|" in out


def test_analysis_answer_contains_recommendation():
    out = bot.answer("analyze bottled water at store 1001")
    assert "Recommendation:" in out
    assert "Agent execution log" in out


def test_scenario_run_is_sandboxed():
    import config
    import pandas as pd
    before = pd.read_csv(config.INVENTORY_CSV)
    out = bot.answer("run scenario 1")
    after = pd.read_csv(config.INVENTORY_CSV)
    assert "Recommendation:" in out
    # scenario overrides must not leak into the working data
    assert before.equals(after)


def test_list_products():
    out = bot.answer("list products")
    assert "Prod_001" in out
