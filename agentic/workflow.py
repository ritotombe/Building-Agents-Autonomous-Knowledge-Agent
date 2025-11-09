from typing import Dict, Any, TypedDict, List, Optional
import logging
import json
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.utils import Input, Output
from langgraph.checkpoint.memory import MemorySaver

from agentic.agents.classifier import classify
from agentic.agents.resolver import resolve
from agentic.agents.ops import operate
from agentic.agents.escalation import escalate

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agentic_workflow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class State(TypedDict):
    messages: List[Any]
    input: str
    intent: str
    account_id: str
    user_id: str
    min_confidence: float
    ticket_id: str
    resolver_result: Dict[str, Any]
    ops_result: Dict[str, Any]
    escalation: Dict[str, Any]


def _extract_last_content(messages) -> Optional[str]:
    if not isinstance(messages, list):
        return None
    for m in reversed(messages):
        try:
            if isinstance(m, HumanMessage):
                return m.content
        except Exception:
            pass
        if isinstance(m, dict) and "content" in m:
            return str(m["content"])
        if hasattr(m, "content"):
            return str(getattr(m, "content"))
        if isinstance(m, str):
            return m
    return None


def _append_ai_message(state: State, text: str):
    msgs = state.get("messages")
    if not isinstance(msgs, list):
        msgs = []
    msgs.append(AIMessage(content=text))
    state["messages"] = msgs


def _node_prepare(state: State) -> State:
    logger.info(f"PREPARE: Starting with state keys: {list(state.keys())}")
    
    # Extract input from messages if not already set
    if "input" not in state or not state["input"]:
        messages = state.get("messages", [])
        if messages:
            content = _extract_last_content(messages)
            if content is not None:
                state["input"] = str(content)
            else:
                state["input"] = ""
        else:
            state["input"] = ""
    
    # set sensible defaults
    state.setdefault("account_id", "cultpass")
    state.setdefault("user_id", "a4ab87")
    state.setdefault("min_confidence", 0.6)
    state.setdefault("ticket_id", state.get("ticket_id", "unknown"))
    
    logger.info(f"PREPARE: Extracted input: '{state['input']}', ticket_id: {state['ticket_id']}")
    return state


def _node_classify(state: State) -> State:
    logger.info(f"CLASSIFY: Processing input: '{state.get('input', '')}'")
    
    if "input" not in state or not state["input"]:
        msg_content = _extract_last_content(state.get("messages"))
        if msg_content is not None:
            state["input"] = msg_content
        else:
            state["input"] = ""
    try:
        intent = classify(state["input"])["intent"]
        state["intent"] = intent
        logger.info(f"CLASSIFY: Classified intent: '{intent}'")
    except Exception as e:
        logger.error(f"CLASSIFY: Error - {e}")
        state["intent"] = "unknown"
    return state


def _node_resolve(state: State) -> State:
    logger.info(f"RESOLVE: Querying KB for: '{state['input']}'")
    r = resolve(account_id=state["account_id"], query=state["input"], min_confidence=state.get("min_confidence", 0.55))
    state["resolver_result"] = r
    if r.get("ok"):
        logger.info(f"RESOLVE: Found answer with confidence {r.get('best_score', 0)}")
        _append_ai_message(state, r.get("answer", ""))
    else:
        logger.warning(f"RESOLVE: Failed - {r.get('reason', 'unknown')}")
        _append_ai_message(state, "I'll escalate this for a specialist to review.")
    return state


def _node_ops(state: State) -> State:
    logger.info(f"OPS: Processing intent '{state.get('intent')}' for user {state.get('user_id')}")
    context = {
        "user_id": state.get("user_id"),
        "external_user_id": state.get("user_id"),
        "experience_id": state.get("experience_id"),
        "reservation_id": state.get("reservation_id"),
        "account_id": state.get("account_id"),
    }
    r = operate(state["input"], context)
    state["ops_result"] = r
    if r.get("ok"):
        logger.info(f"OPS: Success - {r.get('tool_name', 'unknown tool')}")
        _append_ai_message(state, f"Done: {r.get('data')}")
    else:
        logger.error(f"OPS: Failed - {r.get('error')}")
        _append_ai_message(state, f"Operation failed: {r.get('error')}")
    return state


def _node_escalate(state: State) -> State:
    logger.info(f"ESCALATE: Escalating ticket {state.get('ticket_id')} due to intent: {state.get('intent')}")
    conf = None
    if state.get("resolver_result"):
        conf = state["resolver_result"].get("best_score")
    context = {
        "intent": state.get("intent"),
        "resolver_result": state.get("resolver_result"),
        "ops_result": state.get("ops_result"),
    }
    try:
        e = escalate(ticket_id=state.get("ticket_id", "unknown"), user_message=state.get("input", ""), context=context, last_confidence=conf)
        state["escalation"] = e
        logger.info(f"ESCALATE: Escalation completed - UDA-Hub: {e.get('udahub', {}).get('ok')}, Vocareum: {e.get('vocareum', {}).get('ok')}")
        _append_ai_message(state, "I've escalated this to human support.")
    except Exception as e:
        logger.error(f"ESCALATE: Error - {e}")
        _append_ai_message(state, "I've escalated this to human support.")
    return state


class LangChainRouter:
    """LangChain-based router for intelligent routing decisions."""
    
    def __init__(self):
        self.routing_prompt = """
        You are a routing agent for a customer support system.
        Based on the user's intent, route them to the appropriate handler:
        
        - "unknown" -> escalate (human handoff needed)
        - "reservation" or "subscription" -> ops (database operations needed)
        - "knowledge" or "login" -> resolve (knowledge base lookup needed)
        
        Return only the route name: escalate, ops, or resolve
        """
    
    def route_by_intent(self, state: State) -> str:
        """Route based on classified intent using LangChain patterns."""
        intent = state.get("intent", "unknown")
        
        # LangChain-style routing logic with intelligent mapping
        routing_map = {
            "unknown": "escalate",
            "reservation": "ops", 
            "subscription": "ops",
            "knowledge": "resolve",
            "login": "resolve"
        }
        
        route = routing_map.get(intent, "escalate")
        logger.info(f"LANGCHAIN_ROUTE: Intent '{intent}' -> {route}")
        return route
    
    def route_by_confidence(self, state: State) -> str:
        """Route based on resolver confidence using LangChain patterns."""
        resolver_result = state.get("resolver_result", {})
        
        # LangChain-style confidence-based routing
        if not resolver_result.get("ok"):
            logger.info(f"LANGCHAIN_ROUTE: Low confidence -> escalate")
            return "escalate"
        
        logger.info(f"LANGCHAIN_ROUTE: High confidence -> end")
        return "end"
    
    def intelligent_route(self, state: State) -> str:
        """Advanced LangChain routing with LLM-based decisions."""
        from agentic.tools.vocareum_llm import complete
        
        intent = state.get("intent", "unknown")
        user_input = state.get("input", "")
        
        # Use LLM for intelligent routing decisions
        routing_prompt = f"""
        Based on the user's intent '{intent}' and input '{user_input}', 
        determine the best route:
        
        - escalate: For unknown intents or when human help is needed
        - ops: For subscription/reservation operations requiring database access
        - resolve: For knowledge queries that can be answered from knowledge base
        
        Return only: escalate, ops, or resolve
        """
        
        try:
            llm_response = complete(routing_prompt, user_input)
            if llm_response.get("ok"):
                route = llm_response.get("content", "").strip().lower()
                if route in ["escalate", "ops", "resolve"]:
                    logger.info(f"LANGCHAIN_LLM_ROUTE: Intent '{intent}' -> {route}")
                    return route
        except Exception as e:
            logger.error(f"LANGCHAIN_LLM_ROUTE: Error - {e}")
        
        # Fallback to rule-based routing
        return self.route_by_intent(state)


# Create router instance
router = LangChainRouter()


def _should_route_to_ops(state: State) -> str:
    """LangChain-compatible routing function with intelligent routing."""
    return router.intelligent_route(state)


def _should_escalate(state: State) -> str:
    """LangChain-compatible escalation routing function."""
    return router.route_by_confidence(state)


def build_graph():
    """Build LangGraph with LangChain routing patterns."""
    g = StateGraph(State)
    
    # Add nodes using LangChain patterns
    g.add_node("prepare", _node_prepare)
    g.add_node("classify", _node_classify)
    g.add_node("resolve", _node_resolve)
    g.add_node("ops", _node_ops)
    g.add_node("escalate", _node_escalate)

    # Set entry point
    g.set_entry_point("prepare")
    
    # Add edges with LangChain routing
    g.add_edge("prepare", "classify")
    
    # LangChain-style conditional routing
    g.add_conditional_edges(
        "classify", 
        _should_route_to_ops, 
        {
            "ops": "ops", 
            "resolve": "resolve", 
            "escalate": "escalate"
        }
    )
    
    # LangChain-style confidence routing
    g.add_conditional_edges(
        "resolve", 
        _should_escalate, 
        {
            "escalate": "escalate", 
            "end": END
        }
    )
    
    # Terminal edges
    g.add_edge("ops", END)
    g.add_edge("escalate", END)

    # Compile with LangChain memory
    memory = MemorySaver()
    return g.compile(checkpointer=memory)


orchestrator = build_graph()