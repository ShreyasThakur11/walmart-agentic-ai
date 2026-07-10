"""
Walmart Smart Inventory & Restocking Assistant.
High-fidelity Streamlit operations dashboard showcasing Multi-Agent collaboration using the Supervisor Pattern.
"""

import streamlit as st
import pandas as pd
import time
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Set Page Config
st.set_page_config(
    page_title="Walmart Restocking Assistant",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Walmart Dark Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Space+Mono&display=swap');
    
    /* Global Styles */
    .stApp {
        background-color: #0A0E1A;
        color: #F8FAFC;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Header styling */
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 2rem;
        background: linear-gradient(90deg, #0071CE 0%, #161F38 100%);
        border-bottom: 3px solid #FFC220;
        border-radius: 8px;
        margin-bottom: 2rem;
    }
    .header-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: white;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .header-subtitle {
        color: #FFC220;
        font-size: 0.9rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin: 0;
        font-weight: 600;
    }
    
    /* Custom Card Style */
    .metric-card {
        background-color: #161F38;
        border: 1px solid #2D3748;
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #0071CE;
    }
    .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #A0AEC0;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #48BB78;
        margin-top: 0.2rem;
    }
    .metric-sub-warning {
        font-size: 0.8rem;
        color: #F6AD55;
        margin-top: 0.2rem;
    }
    .metric-sub-critical {
        font-size: 0.8rem;
        color: #FC8181;
        margin-top: 0.2rem;
    }
    
    /* Agent Execution Terminal */
    .terminal-container {
        background-color: #05070F;
        border: 2px solid #0071CE;
        border-radius: 8px;
        padding: 1.5rem;
        font-family: 'Space Mono', monospace;
        color: #38BDF8;
        height: 350px;
        overflow-y: auto;
        box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.8);
        margin-bottom: 2rem;
    }
    .terminal-line {
        margin-bottom: 0.6rem;
        line-height: 1.4;
        font-size: 0.85rem;
    }
    .terminal-timestamp {
        color: #64748B;
    }
    .terminal-agent {
        color: #FFC220;
        font-weight: bold;
    }
    .terminal-action {
        color: #34D399;
    }
    .terminal-error {
        color: #F87171;
    }
    
    /* Flowchart Node */
    .flow-container {
        display: flex;
        justify-content: space-around;
        align-items: center;
        flex-wrap: wrap;
        background-color: #111827;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #1F2937;
        margin-bottom: 2rem;
    }
    .flow-node {
        padding: 0.75rem 1.25rem;
        border-radius: 6px;
        background-color: #1F2937;
        border: 1.5px solid #4B5563;
        font-weight: 600;
        font-size: 0.85rem;
        text-align: center;
        min-width: 120px;
        color: #9CA3AF;
        transition: all 0.3s;
    }
    .flow-node.active {
        background-color: #0071CE;
        border-color: #38BDF8;
        color: white;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
    }
    .flow-node.completed {
        background-color: #064E3B;
        border-color: #059669;
        color: #A7F3D0;
    }
    .flow-node.skipped {
        background-color: #374151;
        border-color: #4B5563;
        color: #6B7280;
        text-decoration: line-through;
    }
    .flow-arrow {
        color: #4B5563;
        font-size: 1.5rem;
        font-weight: bold;
    }
    
    /* Recommendation Card Styling */
    .rec-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border-left: 6px solid #FFC220;
        border-radius: 8px;
        padding: 2rem;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
        margin-bottom: 2rem;
    }
    .rec-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 0.5rem;
    }
    .rec-text {
        font-size: 1rem;
        color: #E2E8F0;
        line-height: 1.6;
        margin-bottom: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Add Base project imports (wrapped in try-catch in case venv dependencies aren't loaded yet)
try:
    from tools.db_tools import DatabaseTools
    from agents.supervisor import SupervisorAgent
    from memory.state_manager import WorkflowState
    db_ready = True
except ImportError:
    db_ready = False

# Sidebar Config
st.sidebar.markdown(
    """
    <div style='text-align: center; margin-bottom: 1rem;'>
        <h2 style='color:#FFC220; margin:0;'>WALMART WGT</h2>
        <span style='color:#A0AEC0; font-size:0.8rem; letter-spacing:1px;'>GLOBAL RETAIL TECH</span>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.header("Restock Simulation Panel")

if not db_ready:
    st.error("Application environment is initializing. Please wait a few seconds and refresh...")
    st.stop()

db = DatabaseTools()
supervisor = SupervisorAgent()

# Dynamic options from Database
stores = db.get_all_stores()
products = db.get_store_products(stores[0])
product_options = {p["ProductID"]: p["ProductName"] for p in products}

# Sidebar inputs
selected_store = st.sidebar.selectbox("Target Retail Store", stores)

# Refresh product list for store
store_products = db.get_store_products(selected_store)
product_options = {p["ProductID"]: f"{p['ProductName']} ({p['ProductID']})" for p in store_products}
selected_product_id = st.sidebar.selectbox("Target Product", list(product_options.keys()), format_func=lambda x: product_options[x])

st.sidebar.subheader("Simulation Configuration")

# Demonstration Scenarios
scenarios = {
    "Standard Assessment": "Default database levels will be analyzed.",
    "Scenario 1: Pre-Festival Bottled Water Spike": "High sales velocity predicted for water. Warehouses have stock.",
    "Scenario 2: Warehouse Stock Outage": "Pharmacy item is out of stock in all regional DCs. Supplier order required.",
    "Scenario 3: Supplier Lead Time Delay": "Electronics item with long lead time from primary supplier. Logistics must escalate transport.",
    "Scenario 4: Post-Promotion Spike": "Patio furniture item low stock after marketing promo. Dual sourcing recommended.",
    "Scenario 5: Multi-Store Resource Contention": "Two stores request Organic Milk. Warehouse has limited supply. Allocation split."
}

selected_scenario = st.sidebar.selectbox("Active Scenario Mode", list(scenarios.keys()))
st.sidebar.caption(scenarios[selected_scenario])

simulation_speed = st.sidebar.slider("Step-by-step Delay (Seconds)", min_value=0.1, max_value=2.0, value=0.5, step=0.1)

# Actions
col_side_1, col_side_2 = st.sidebar.columns(2)
with col_side_1:
    run_btn = st.button("🚀 Run Analysis", use_container_width=True)
with col_side_2:
    reset_btn = st.button("🔄 Reset UI", use_container_width=True)

# Session State Initialization
if "terminal_logs" not in st.session_state or reset_btn:
    st.session_state.terminal_logs = []
    st.session_state.active_agent = "Supervisor"
    st.session_state.workflow_state = None
    st.session_state.executing = False

# Layout Header
st.markdown(
    """
    <div class="header-container">
        <div>
            <h1 class="header-title">🛒 Walmart Smart Inventory Restocking Assistant</h1>
            <p style="color: #E2E8F0; margin: 5px 0 0 0; font-size: 0.95rem;">
                Multi-Agent Restocking Assistant • Version 1.0
            </p>
        </div>
        <div style="text-align: right;">
            <p class="header-subtitle">Status: Operational</p>
            <p style="color: #FFC220; margin: 0; font-size: 0.8rem; font-weight: bold;">WGT Arkansas Lab</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Apply Scenario Database Overrides before executing analysis
def apply_scenario_overrides(store_id, product_id, scenario):
    # Standard resets
    db.update_inventory_stock("Store_1001", "Prod_002", 0)  # Reset water
    
    if "Scenario 1" in scenario:
        # High demand for Bottled Water at Store_1001. Make sure current stock is low.
        db.update_inventory_stock("Store_1001", "Prod_002", -100) # force stock low
    elif "Scenario 2" in scenario:
        # Allergy Medicine stock low. Warehouse stock 0 (this is hardcoded in data generator)
        db.update_inventory_stock("Store_1002", "Prod_006", -50)
    elif "Scenario 3" in scenario:
        # TV low. Supplier has long lead time.
        db.update_inventory_stock("Store_1003", "Prod_005", -15)
    elif "Scenario 4" in scenario:
        # Patio set low. Promotion active.
        db.update_inventory_stock("Store_1004", "Prod_004", -8)
    elif "Scenario 5" in scenario:
        # Two stores request milk. Warehouse has limited supply.
        db.update_inventory_stock("Store_1001", "Prod_001", -20)
        db.update_inventory_stock("Store_1005", "Prod_001", -25)

# Run Analysis Pipeline
if run_btn:
    st.session_state.executing = True
    st.session_state.terminal_logs = []
    
    # Force apply database overrides for chosen scenario
    apply_scenario_overrides(selected_store, selected_product_id, selected_scenario)
    
    # Run the generator
    workflow_gen = supervisor.run_workflow(
        store_id=selected_store,
        product_id=selected_product_id,
        scenario_name=selected_scenario
    )
    
    # Dynamic display placeholder
    progress_bar = st.progress(0.0)
    
    for step_state in workflow_gen:
        st.session_state.workflow_state = step_state
        st.session_state.active_agent = step_state.current_step
        
        # Build logs
        logs = []
        for log in step_state.execution_history:
            logs.append(
                f"<span class='terminal-timestamp'>[{log.timestamp}]</span> "
                f"<span class='terminal-agent'>[{log.agent_name}]</span>: "
                f"{log.message} (Action: <span class='terminal-action'>{log.action_taken}</span>)"
            )
        st.session_state.terminal_logs = logs
        
        # Dynamic progress percentage
        steps = ["SUPERVISOR_DECIDING", "INVENTORY_MONITORING", "DEMAND_FORECASTING", 
                 "WAREHOUSE_ALLOCATION", "SUPPLIER_INTELLIGENCE", "LOGISTICS_PLANNING", 
                 "RECOMMENDATION_GENERATION", "COMPLETE"]
        idx = steps.index(step_state.current_step) if step_state.current_step in steps else 0
        progress_bar.progress(float(idx + 1) / len(steps))
        
        # UI sleep delay
        time.sleep(simulation_speed)
        
    st.session_state.executing = False
    st.success("Analysis complete!")

# Fetch loaded state
state = st.session_state.workflow_state

# GRID LAYOUT FOR METRIC CARDS
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)

with col_m1:
    val = state.inventory.current_stock if (state and state.inventory) else "N/A"
    sub_text = "Stable"
    sub_class = "metric-sub"
    if state and state.inventory:
        status = state.inventory.status
        if status == "CRITICAL_UNDERSTOCK":
            sub_text = "Severe Outage"
            sub_class = "metric-sub-critical"
        elif status == "UNDERSTOCK":
            sub_text = "Below Safety Limit"
            sub_class = "metric-sub-warning"
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Current Stock</div>
            <div class="metric-value">{val}</div>
            <div class="{sub_class}">{sub_text}</div>
        </div>
    """, unsafe_allow_html=True)

with col_m2:
    val = state.demand.forecast_units if (state and state.demand) else "N/A"
    sub_text = "Restock target"
    if state and state.demand:
        sub_text = f"Qty Reorder: {state.demand.reorder_quantity}"
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Demand Forecast</div>
            <div class="metric-value">{val}</div>
            <div class="metric-sub">{sub_text}</div>
        </div>
    """, unsafe_allow_html=True)

with col_m3:
    val = state.warehouse.transfer_qty if (state and state.warehouse and state.warehouse.status == "ALLOCATED") else "0"
    if state and state.warehouse and state.warehouse.status == "INSUFFICIENT":
        val = f"{state.warehouse.transfer_qty} (Partial)"
    sub_text = "Distribution center supply"
    if state and state.warehouse and state.warehouse.warehouse_id:
        sub_text = f"Source: {state.warehouse.warehouse_id}"
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Warehouse Transfer</div>
            <div class="metric-value">{val}</div>
            <div class="metric-sub">{sub_text}</div>
        </div>
    """, unsafe_allow_html=True)

with col_m4:
    val = state.supplier.order_qty if (state and state.supplier and state.supplier.status == "PROPOSED") else "0"
    sub_text = "Vendor supply"
    if state and state.supplier and state.supplier.supplier_name:
        sub_text = f"Vendor: {state.supplier.supplier_name}"
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Supplier Order</div>
            <div class="metric-value">{val}</div>
            <div class="metric-sub">{sub_text}</div>
        </div>
    """, unsafe_allow_html=True)

with col_m5:
    val = "N/A"
    sub_text = "Risk index"
    sub_class = "metric-sub"
    if state and state.recommendation:
        val = f"{state.recommendation.risk_score}"
        risk = state.recommendation.risk_score
        if risk > 70:
            sub_text = "HIGH STOCKOUT RISK"
            sub_class = "metric-sub-critical"
        elif risk > 40:
            sub_text = "MEDIUM RISK"
            sub_class = "metric-sub-warning"
        else:
            sub_text = "LOW RISK"
            sub_class = "metric-sub"
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Outage Risk Score</div>
            <div class="metric-value">{val}</div>
            <div class="{sub_class}">{sub_text}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# LIVE EXECUTION & FLOW PANEL
col_l1, col_l2 = st.columns([1, 1])

with col_l1:
    st.subheader("Live Multi-Agent Routing Flow")
    
    # Render custom CSS diagram showing the supervisor routing
    curr_step = st.session_state.active_agent
    
    s_active = "active" if curr_step == "SUPERVISOR_DECIDING" else "completed" if state else ""
    i_active = "active" if curr_step == "INVENTORY_MONITORING" else "completed" if (state and state.inventory) else ""
    d_active = "active" if curr_step == "DEMAND_FORECASTING" else "completed" if (state and state.demand) else ""
    w_active = "active" if curr_step == "WAREHOUSE_ALLOCATION" else "completed" if (state and state.warehouse and state.warehouse.status != "SKIPPED") else "skipped" if (state and state.warehouse and state.warehouse.status == "SKIPPED") else ""
    su_active = "active" if curr_step == "SUPPLIER_INTELLIGENCE" else "completed" if (state and state.supplier and state.supplier.status != "SKIPPED") else "skipped" if (state and state.supplier and state.supplier.status == "SKIPPED") else ""
    l_active = "active" if curr_step == "LOGISTICS_PLANNING" else "completed" if (state and state.logistics and state.logistics.status != "SKIPPED") else "skipped" if (state and state.logistics and state.logistics.status == "SKIPPED") else ""
    r_active = "active" if curr_step == "RECOMMENDATION_GENERATION" else "completed" if (state and state.recommendation) else ""

    st.markdown(f"""
        <div class="flow-container">
            <div class="flow-node {s_active}">Supervisor</div>
            <div class="flow-arrow">➔</div>
            <div class="flow-node {i_active}">Inventory Agent</div>
            <div class="flow-arrow">➔</div>
            <div class="flow-node {d_active}">Demand Agent</div>
        </div>
        <div class="flow-container" style="margin-top: -1rem;">
            <div class="flow-node {w_active}">Warehouse Agent</div>
            <div class="flow-arrow">➔</div>
            <div class="flow-node {su_active}">Supplier Agent</div>
            <div class="flow-arrow">➔</div>
            <div class="flow-node {l_active}">Logistics Agent</div>
            <div class="flow-arrow">➔</div>
            <div class="flow-node {r_active}">Rec Agent</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Plotly Visualizations (Conditional based on available state)
    if state and state.inventory:
        inv_data = pd.DataFrame({
            "Metric": ["Current Stock", "Min Threshold", "Max Capacity"],
            "Units": [state.inventory.current_stock, state.inventory.min_threshold, state.inventory.max_capacity],
            "Color": ["#38BDF8", "#FFC220", "#4B5563"]
        })
        fig_inv = px.bar(
            inv_data, x="Metric", y="Units", color="Metric",
            color_discrete_map={"Current Stock": "#0071CE", "Min Threshold": "#FFC220", "Max Capacity": "#4B5563"},
            title="Store Stock Level vs Operational Safety Thresholds"
        )
        fig_inv.update_layout(
            paper_bgcolor="#161F38", plot_bgcolor="#161F38",
            font_color="#F8FAFC", showlegend=False, margin=dict(l=20, r=20, t=40, b=20), height=220
        )
        st.plotly_chart(fig_inv, use_container_width=True)

with col_l2:
    st.subheader("Live Agent Decision Terminal")
    
    terminal_html = ""
    for line in st.session_state.terminal_logs:
        terminal_html += f"<div class='terminal-line'>{line}</div>"
        
    if not terminal_html:
        terminal_html = "<div class='terminal-line'><span class='terminal-timestamp'>[System Ready]</span> Click 'Run Analysis' to initialize Multi-Agent restocking decision engine.</div>"
        
    st.markdown(f"""
        <div class="terminal-container">
            {terminal_html}
        </div>
    """, unsafe_allow_html=True)

# RECOMMENDATION & FORECAST VISUALS
if state and state.recommendation:
    st.markdown("---")
    col_r1, col_r2 = st.columns([3, 2])
    
    with col_r1:
        st.subheader("Consolidated Restocking Recommendation")
        
        # Color match based on recommendation action
        border_color = "#FFC220"
        action = state.recommendation.action
        if action == "TRANSFER":
            border_color = "#34D399" # Green
        elif action == "DUAL_SOURCE":
            border_color = "#38BDF8" # Blue
        elif action == "PROCURE":
            border_color = "#FB923C" # Orange
            
        st.markdown(f"""
            <div class="rec-card" style="border-left-color: {border_color};">
                <div class="rec-title">Action Action Plan: {state.recommendation.action}</div>
                <div class="rec-text"><strong>Details:</strong> {state.recommendation.details}</div>
                <div class="rec-text"><strong>Business Operations Impact:</strong> {state.recommendation.business_impact}</div>
                <div class="rec-text"><strong>Shipment Status:</strong> {state.logistics.shipment_schedule if state.logistics else 'N/A'}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Mini column stats
        col_sub_1, col_sub_2, col_sub_3 = st.columns(3)
        col_sub_1.metric("Financial Cost Savings", f"${state.recommendation.estimated_savings}", delta="Cost Avoidance")
        col_sub_2.metric("Stockout Risk Reduction", f"{state.recommendation.stockout_reduction_pct}%", delta="Confidence Delta")
        col_sub_3.metric("Supervisor Confidence", f"{state.recommendation.confidence_score}%")

    with col_r2:
        st.subheader("Operations Demand & Sourcing Analysis")
        
        # Historical sales plot if available
        sales_hist = db.get_sales_history(state.store_id, state.product_id)
        if sales_hist:
            df_sales = pd.DataFrame(sales_hist)
            df_sales["Date"] = pd.to_datetime(df_sales["Date"])
            df_sales = df_sales.sort_values("Date")
            
            fig_sales = px.line(
                df_sales, x="Date", y="UnitsSold", title="30-Day Store Sales Volume Trend",
                color_discrete_sequence=["#FFC220"]
            )
            # Add a vertical dotted line for today and a shaded forecast block
            fig_sales.add_vline(x=df_sales["Date"].max(), line_width=2, line_dash="dash", line_color="#E2E8F0")
            
            fig_sales.update_layout(
                paper_bgcolor="#161F38", plot_bgcolor="#161F38",
                font_color="#F8FAFC", margin=dict(l=20, r=20, t=40, b=20), height=230
            )
            st.plotly_chart(fig_sales, use_container_width=True)
            st.caption("Dashed line marks analysis trigger date. Sourcing is optimized for forecasted demand.")
            
# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #64748B; font-size: 0.8rem; padding: 10px 0;">
        Walmart Global Tech Restocking Orchestrator • Authorized Personnel Only • Confidential Systems &copy; 2026 Walmart Inc.
    </div>
    """,
    unsafe_allow_html=True
)
