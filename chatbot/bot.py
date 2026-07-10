"""Issue-driven chatbot for the restocking assistant.

Runs the same multi-agent pipeline as the dashboard, but through GitHub:
open an issue or comment on one, a GitHub Actions job runs this module,
and the answer is posted back as a comment. The pipeline is deterministic
and rule based, so the bot needs no API keys and costs nothing to run.

Local use:
    python -m chatbot.bot "analyze bottled water at store 1001"
    python -m chatbot.bot "run scenario 3"
    python -m chatbot.bot "status of store 1002"
    python -m chatbot.bot "help"

In GitHub Actions the query, repository and issue number arrive through
QUERY_TEXT, GITHUB_REPOSITORY and ISSUE_NUMBER; when GITHUB_TOKEN is set
the reply is posted as an issue comment, otherwise it is printed.
"""

import json
import os
import re
import shutil
import sys
import tempfile
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from agents.supervisor import SupervisorAgent
from tools.db_tools import DatabaseTools

# Scenario catalogue: name (keywords drive the demand agent), store(s), product.
SCENARIOS = {
    1: ("Scenario 1: Pre-Festival Bottled Water Spike", ["Store_1001"], "Prod_002"),
    2: ("Scenario 2: Warehouse Stock Outage", ["Store_1002"], "Prod_006"),
    3: ("Scenario 3: Supplier Lead Time Delay", ["Store_1003"], "Prod_005"),
    4: ("Scenario 4: Post-Promotion Spike", ["Store_1004"], "Prod_004"),
    5: ("Scenario 5: Multi-Store Resource Contention",
        ["Store_1001", "Store_1005"], "Prod_001"),
}

HELP_TEXT = """## Restocking assistant

I run the store's multi-agent restocking analysis (inventory health, demand
forecast, warehouse transfer, supplier bids, logistics) and reply with a
recommendation. Things you can ask me, in plain text:

| Ask | Example |
|---|---|
| Analyze a product at a store | `analyze bottled water at store 1001` |
| Same, by IDs | `restock Prod_003 at Store_1002` |
| Store stock health overview | `status of store 1004` |
| Run a demo scenario | `run scenario 2` |
| What data do I know about | `list products` or `list stores` |
| This message | `help` |

Scenarios: 1 pre-festival water spike, 2 warehouse stock outage,
3 supplier lead-time delay, 4 post-promotion spike, 5 multi-store contention.
"""


# --------------------------------------------------------------------------
# query parsing
# --------------------------------------------------------------------------
def catalog():
    db = DatabaseTools()
    df = db._read_csv(config.INVENTORY_CSV)
    products = (df[["ProductID", "ProductName", "Category"]]
                .drop_duplicates("ProductID").to_dict("records"))
    stores = sorted(df["StoreID"].unique().tolist())
    return stores, products


def match_store(text, stores):
    m = re.search(r"store[_\s#-]*(\d{3,4})", text, re.I)
    if not m:
        m = re.search(r"\b(1\d{3})\b", text)
    if m:
        sid = f"Store_{m.group(1)}"
        if sid in stores:
            return sid
    return None


def match_product(text, products):
    m = re.search(r"prod(?:uct)?[_\s#-]*0*(\d{1,3})", text, re.I)
    if m:
        pid = f"Prod_{int(m.group(1)):03d}"
        for p in products:
            if p["ProductID"] == pid:
                return p
    # fuzzy name match: score by shared words, ignore filler
    stop = {"the", "a", "of", "at", "for", "in", "on", "and", "value", "great",
            "pack", "store", "analyze", "analysis", "restock", "check", "status"}
    words = {w for w in re.findall(r"[a-z]+", text.lower()) if w not in stop}
    best, best_score = None, 0
    for p in products:
        name_words = {w for w in re.findall(r"[a-z]+", p["ProductName"].lower())
                      if w not in stop}
        score = len(words & name_words)
        if score > best_score:
            best, best_score = p, score
    return best if best_score >= 1 else None


def parse(text):
    """Return an intent dict for the incoming question."""
    t = (text or "").strip()
    low = t.lower()
    if not t or "help" in low.split():
        return {"intent": "help"}
    m = re.search(r"scenario\s*#?\s*([1-5])", low)
    if m:
        return {"intent": "scenario", "n": int(m.group(1))}
    stores, products = catalog()
    if re.search(r"\blist\b|\bwhat (products|stores)\b|\bcatalog", low):
        return {"intent": "list", "stores": stores, "products": products}
    store = match_store(low, stores)
    product = match_product(low, products)
    if re.search(r"\bstatus\b|\bhealth\b|\boverview\b", low) and store and not product:
        return {"intent": "status", "store": store}
    if store and product:
        return {"intent": "analyze", "store": store, "product": product}
    if product and not store:
        return {"intent": "analyze", "store": "Store_1001", "product": product,
                "note": "No store given, using Store_1001."}
    if store and not product:
        return {"intent": "status", "store": store}
    return {"intent": "help", "note": "I could not match that to a store or "
                                      "product, so here is what I can do."}


# --------------------------------------------------------------------------
# pipeline execution
# --------------------------------------------------------------------------
def run_pipeline(store_id, product_id, scenario_name="Standard Assessment"):
    supervisor = SupervisorAgent()
    final = None
    for state in supervisor.run_workflow(store_id, product_id, scenario_name):
        final = state
    return final


def apply_scenario_overrides(n):
    """Replicates the dashboard's scenario setup on the local CSV copies."""
    db = DatabaseTools()
    db.update_inventory_stock("Store_1001", "Prod_002", 0)
    if n == 1:
        db.update_inventory_stock("Store_1001", "Prod_002", -100)
    elif n == 2:
        db.update_inventory_stock("Store_1002", "Prod_006", -50)
    elif n == 3:
        db.update_inventory_stock("Store_1003", "Prod_005", -15)
    elif n == 4:
        db.update_inventory_stock("Store_1004", "Prod_004", -8)
    elif n == 5:
        db.update_inventory_stock("Store_1001", "Prod_001", -20)
        db.update_inventory_stock("Store_1005", "Prod_001", -25)


class data_sandbox:
    """Snapshot and restore the CSV data so scenario overrides never leak."""

    def __enter__(self):
        self.tmp = tempfile.mkdtemp(prefix="restock_bot_")
        shutil.copytree(config.DATA_DIR, os.path.join(self.tmp, "data"))
        return self

    def __exit__(self, *exc):
        src = os.path.join(self.tmp, "data")
        for f in os.listdir(src):
            shutil.copy2(os.path.join(src, f), config.DATA_DIR / f)
        shutil.rmtree(self.tmp, ignore_errors=True)
        return False


# --------------------------------------------------------------------------
# reply formatting
# --------------------------------------------------------------------------
def fmt_money(x):
    return f"${x:,.2f}"


def format_analysis(state):
    inv, dem = state.inventory, state.demand
    wh, sup, log, rec = state.warehouse, state.supplier, state.logistics, state.recommendation

    lines = [f"### {state.product_name or state.product_id} at {state.store_id}",
             "", "| Stage | Result |", "|---|---|"]
    if inv:
        lines.append(f"| Stock health | **{inv.status}** "
                     f"({inv.current_stock} on hand, threshold {inv.min_threshold}, "
                     f"capacity {inv.max_capacity}) |")
    if dem:
        lines.append(f"| Demand forecast | {dem.forecast_units} units over 7 days "
                     f"({dem.trend_type}, avg {dem.average_daily_sales}/day), "
                     f"reorder {dem.reorder_quantity} |")
    else:
        lines.append("| Demand forecast | not needed (stock stable) |")
    if wh and wh.status != "SKIPPED":
        if wh.transfer_qty > 0:
            lines.append(f"| Warehouse | {wh.location} ({wh.warehouse_id}): transfer "
                         f"{wh.transfer_qty} units, {wh.distance_miles:,.0f} mi, "
                         f"{wh.transfer_time_days} days, {fmt_money(wh.cost)} |")
        else:
            lines.append("| Warehouse | no distribution center stock available |")
    if sup and sup.status == "PROPOSED":
        lines.append(f"| Supplier | {sup.supplier_name}: {sup.order_qty} units at "
                     f"{fmt_money(sup.unit_cost)}/unit = {fmt_money(sup.total_cost)}, "
                     f"lead {sup.lead_time_days} d, reliability {sup.reliability_score:.2f} |")
    if log and log.status != "SKIPPED":
        lines.append(f"| Logistics | {log.transport_mode}, ETA "
                     f"{log.estimated_delivery_days} days, {fmt_money(log.logistics_cost)} |")
    lines.append("")
    if rec:
        lines += [f"**Recommendation: {rec.action}**", "", rec.details, "",
                  f"{rec.business_impact}", "",
                  f"Confidence {rec.confidence_score:.0f}/100 | "
                  f"risk {rec.risk_score:.0f}/100 | "
                  f"stockout reduction {rec.stockout_reduction_pct:.0f}% | "
                  f"estimated savings {fmt_money(rec.estimated_savings)}"]
    lines += ["", "<details><summary>Agent execution log "
              f"({' > '.join(state.routing_path)})</summary>", ""]
    for e in state.execution_history:
        lines.append(f"- `{e.agent_name}` {e.message}")
    lines += ["", "</details>"]
    return "\n".join(lines)


def do_status(store):
    db = DatabaseTools()
    from tools.rules_engine import RulesEngine
    rows = db.get_store_products(store)
    if not rows:
        return f"No inventory records found for {store}."
    lines = [f"## Stock health at {store}", "",
             "| Product | On hand | Threshold | Capacity | Health |", "|---|---|---|---|---|"]
    for r in rows:
        health = RulesEngine.get_stock_health_label(
            r["CurrentStock"], r["MinimumThreshold"], r["MaximumCapacity"])
        flag = {"CRITICAL_UNDERSTOCK": "**CRITICAL**", "UNDERSTOCK": "LOW",
                "OVERSTOCK": "HIGH", "STABLE": "ok"}[health]
        lines.append(f"| {r['ProductName']} | {r['CurrentStock']} | "
                     f"{r['MinimumThreshold']} | {r['MaximumCapacity']} | {flag} |")
    lines += ["", "Ask `analyze <product> at <store>` for a restocking plan "
              "on any line above."]
    return "\n".join(lines)


def do_list(stores, products):
    lines = ["## Coverage", "", f"**Stores:** {', '.join(stores)}", "",
             "| Product | Name | Category |", "|---|---|---|"]
    for p in products:
        lines.append(f"| {p['ProductID']} | {p['ProductName']} | {p['Category']} |")
    return "\n".join(lines)


def answer(text):
    """Main entry: question text in, markdown reply out."""
    q = parse(text)
    note = f"_{q['note']}_\n\n" if q.get("note") else ""
    if q["intent"] == "help":
        return note + HELP_TEXT
    if q["intent"] == "list":
        return do_list(q["stores"], q["products"])
    if q["intent"] == "status":
        return do_status(q["store"])
    if q["intent"] == "scenario":
        name, stores, product = SCENARIOS[q["n"]]
        with data_sandbox():
            apply_scenario_overrides(q["n"])
            parts = [f"## {name}", ""]
            for s in stores:
                parts.append(format_analysis(run_pipeline(s, product, name)))
                parts.append("")
        return "\n".join(parts)
    # analyze
    scenario = "Standard Assessment"
    low = (text or "").lower()
    for kw in ("spike", "festival", "promotion", "contention", "delay"):
        if kw in low:
            scenario = f"Ad-hoc {kw} assessment"
            break
    state = run_pipeline(q["store"], q["product"]["ProductID"], scenario)
    return note + f"## Restocking analysis\n\n{format_analysis(state)}"


# --------------------------------------------------------------------------
# GitHub plumbing
# --------------------------------------------------------------------------
def post_comment(repo, issue_number, body, token):
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    req = urllib.request.Request(
        url,
        data=json.dumps({"body": body}).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "restocking-assistant-bot"},
        method="POST")
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))["html_url"]


def main():
    text = " ".join(sys.argv[1:]) or os.environ.get("QUERY_TEXT", "")
    reply = answer(text)
    print(reply)
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    issue = os.environ.get("ISSUE_NUMBER")
    if token and repo and issue:
        url = post_comment(repo, issue, reply, token)
        print(f"\nposted: {url}", file=sys.stderr)


if __name__ == "__main__":
    main()
