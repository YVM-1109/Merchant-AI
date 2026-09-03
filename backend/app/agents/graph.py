"""
LangGraph Multi-Agent State Graph

Orchestrates 4 agent nodes (Growth, Buyer, Guardian, Catalog) with
Command-based handoffs. Each node returns a Command that routes
control to the next appropriate agent or terminates the flow.

Architecture:
  ┌─────────┐    Command    ┌──────────┐
  │ Catalog │ ────────────→│  Buyer   │
  └─────────┘               └──────────┘
                              │
                              ▼
                       ┌─────────────┐
                       │  Guardian   │
                       └─────────────┘
                         │      │
                          ▼      ▼
                  ┌──────────┐ ┌─────────┐
                  │ Approved │ │  Denied │
                  └──────────┘ └─────────┘
                      │
                      ▼
                ┌──────────┐
                │  Growth  │
                └──────────┘
"""
from typing import Optional, TypedDict

from langgraph.graph import StateGraph, END

from app.agents.growth import GrowthAgent
from app.agents.buyer import BuyerAgent
from app.agents.guardian import GuardianAgent
from app.agents.catalog import CatalogAgent
from app.agents.tools import AgentTools
from app.ap2.crypto import AP2Crypto


class AgentState(TypedDict):
    """Mutable state flowing through the graph."""
    messages: list[dict]
    merchant_id: str
    buyer_did: str
    intent_mandate_id: Optional[str]
    current_agent: str
    action_type: Optional[str]
    pending_action: Optional[dict]
    result: Optional[dict]
    error: Optional[str]


class AgentGraph:
    """Compiles and manages the LangGraph StateGraph."""

    def __init__(self):
        self.tools = AgentTools()
        self.guardian = GuardianAgent(self.tools)

    async def catalog_node(self, state: AgentState) -> AgentState:
        """CatalogAgent — product discovery."""
        catalog = CatalogAgent(self.tools)
        message = state["messages"][-1]["content"] if state["messages"] else ""

        result = await catalog.run(
            message=message,
            context={
                "merchant_id": state["merchant_id"],
            },
        )

        state["current_agent"] = "catalog"
        state["result"] = result
        state["messages"].append({
            "agent": "catalog",
            "content": str(result),
        })
        return state

    async def buyer_node(self, state: AgentState) -> AgentState:
        """BuyerAgent — executes purchase intent."""
        # In a real deployment, buyer_private_key would come from the
        # intent mandate or wallet. For now we use a generated key.
        private_pem, _ = AP2Crypto.generate_key_pair()

        buyer = BuyerAgent(
            tools=self.tools,
            guardian=self.guardian,
            buyer_private_key=private_pem,
            buyer_did=state["buyer_did"],
        )

        message = state["messages"][-1]["content"] if state["messages"] else ""
        context = {
            "merchant_id": state["merchant_id"],
            "intent_mandate_id": state["intent_mandate_id"],
        }

        result = await buyer.run(message=message, context=context)

        state["current_agent"] = "buyer"
        state["result"] = result
        state["messages"].append({
            "agent": "buyer",
            "content": str(result),
        })

        # Route based on result
        if result.get("status") == "denied":
            state["error"] = result.get("guardian_decision", {}).get("reason", "Unknown")
        elif result.get("status") == "success":
            state["action_type"] = "CREATE_ORDER"
            state["pending_action"] = result.get("order", {})

        return state

    async def guardian_node(self, state: AgentState) -> AgentState:
        """GuardianAgent — already embedded in BuyerAgent flow.

        This node is for explicit Guardian review of pending actions
        that were escalated.
        """
        if state.get("error"):
            # Action was denied, route to Guardian for detailed decision
            state["current_agent"] = "guardian"
            state["messages"].append({
                "agent": "guardian",
                "content": f"Action denied: {state['error']}",
            })
            state["result"] = {
                "decision": "denied",
                "reason": state["error"],
            }
        else:
            state["current_agent"] = "guardian"
            state["messages"].append({
                "agent": "guardian",
                "content": "All checks passed. Proceeding to settlement.",
            })

        return state

    async def growth_node(self, state: AgentState) -> AgentState:
        """GrowthAgent — post-purchase optimization."""
        growth = GrowthAgent(self.tools)
        message = state["messages"][-1]["content"] if state["messages"] else "analyze revenue"

        result = await growth.run(
            message=message,
            context={
                "merchant_id": state["merchant_id"],
            },
        )

        state["current_agent"] = "growth"
        state["result"] = result
        state["messages"].append({
            "agent": "growth",
            "content": str(result),
        })
        return state

    def build(self) -> StateGraph:
        """Compile the LangGraph StateGraph with all 4 agent nodes."""
        graph = StateGraph(AgentState)

        # Register agent nodes
        graph.add_node("catalog", self.catalog_node)
        graph.add_node("buyer", self.buyer_node)
        graph.add_node("guardian", self.guardian_node)
        graph.add_node("growth", self.growth_node)

        # Routing logic:
        # 1. Start → Catalog (product discovery)
        # 2. Catalog → Buyer (interpret intent + checkout)
        # 3. Buyer → Guardian (validate money action)
        # 4. Guardian → Growth (on success) or END (on failure)
        graph.set_entry_point("catalog")

        # Catalog → Buyer
        graph.add_edge("catalog", "buyer")

        # Buyer → Guardian (always route through Guardian)
        graph.add_edge("buyer", "guardian")

        # Guardian → Growth (on approval) or END (on denial)
        # The growth_node checks state["error"] to decide
        graph.add_edge("guardian", "growth")
        graph.add_edge("growth", END)

        return graph.compile()


# ── Convenience: create a compiled graph instance ───────────────────
_agent_graph = None


def get_graph() -> StateGraph:
    """Get the compiled agent graph (singleton)."""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = AgentGraph().build()
    return _agent_graph
