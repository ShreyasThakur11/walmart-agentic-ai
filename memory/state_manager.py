"""
State and Memory manager for the Walmart Multi-Agent Restocking System.
Uses Pydantic to enforce strict data structures for execution state, agent responses, and logs.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class InventoryState(BaseModel):
    status: str = "UNKNOWN"
    current_stock: int = 0
    min_threshold: int = 0
    max_capacity: int = 0
    stock_health: str = "UNKNOWN"
    alerts: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class DemandState(BaseModel):
    forecast_units: int = 0
    trend_type: str = "STABLE"  # STABLE, SPIKE, SEASONAL
    has_promotion: bool = False
    average_daily_sales: float = 0.0
    reorder_quantity: int = 0
    explanation: str = ""

class WarehouseAllocation(BaseModel):
    warehouse_id: str = ""
    location: str = ""
    available_stock: int = 0
    distance_miles: float = 0.0
    transfer_time_days: float = 0.0
    transfer_qty: int = 0
    cost: float = 0.0
    status: str = "SKIPPED" # ALLOCATED, INSUFFICIENT, SKIPPED

class SupplierProposal(BaseModel):
    supplier_id: str = ""
    supplier_name: str = ""
    lead_time_days: int = 0
    reliability_score: float = 0.0
    unit_cost: float = 0.0
    order_qty: int = 0
    total_cost: float = 0.0
    status: str = "SKIPPED" # PROPOSED, SKIPPED

class LogisticsPlan(BaseModel):
    source: str = ""  # WAREHOUSE or SUPPLIER or BOTH
    transport_mode: str = "STANDARD_FREIGHT"  # EXPRESS, STANDARD_FREIGHT, AIR_CARGO
    estimated_delivery_days: float = 0.0
    logistics_cost: float = 0.0
    shipment_schedule: str = ""
    status: str = "SKIPPED"

class FinalRecommendation(BaseModel):
    action: str = "NO_ACTION"
    details: str = ""
    business_impact: str = ""
    confidence_score: float = 0.0
    estimated_savings: float = 0.0
    stockout_reduction_pct: float = 0.0
    risk_score: float = 0.0  # 0 to 100

class AgentLogEntry(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    agent_name: str
    message: str
    action_taken: str
    execution_time_ms: float = 0.0

class WorkflowState(BaseModel):
    store_id: str
    product_id: str
    product_name: str = ""
    scenario_name: str = "Standard Assessment"
    
    # Sub-agent outputs
    inventory: Optional[InventoryState] = None
    demand: Optional[DemandState] = None
    warehouse: Optional[WarehouseAllocation] = None
    supplier: Optional[SupplierProposal] = None
    logistics: Optional[LogisticsPlan] = None
    recommendation: Optional[FinalRecommendation] = None
    
    # Audit log tracking
    execution_history: List[AgentLogEntry] = Field(default_factory=list)
    routing_path: List[str] = Field(default_factory=list)  # Sequence of agents run
    current_step: str = "INITIALIZED"
    is_complete: bool = False
    
    def add_log(self, agent_name: str, message: str, action: str = "CONTINUE", exec_time: float = 0.0):
        """Helper to append log entries and track routing path."""
        entry = AgentLogEntry(
            agent_name=agent_name,
            message=message,
            action_taken=action,
            execution_time_ms=exec_time
        )
        self.execution_history.append(entry)
        if agent_name not in self.routing_path:
            self.routing_path.append(agent_name)
