from __future__ import annotations
import uuid
import datetime
import time
from typing import Optional, Callable, Any, Dict, List
from pydantic import BaseModel

# -----------------------------
# Simple SDK-like decorators / stubs
# -----------------------------

def function_tool(func=None, *, name: Optional[str] = None):
    """Decorator to mark a function as a tool. In a real SDK this exposes metadata.
    Here it's only used for clarity.
    """
    def wrapper(f):
        f._is_tool = True
        f._tool_name = name or f.__name__
        return f
    if func:
        return wrapper(func)
    return wrapper

# -----------------------------
# Context model
# -----------------------------
class UserContext(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    is_premium_user: bool = False
    issue_type: Optional[str] = None  # e.g., 'billing', 'technical', 'general'
    last_ticket_id: Optional[str] = None

# -----------------------------
# Simple in-memory tickets DB
# -----------------------------
TICKETS: List[Dict[str, Any]] = []

def create_ticket_record(title: str, description: str, user: UserContext, category: str) -> Dict[str, Any]:
    ticket = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "user": {"name": user.name, "email": user.email},
        "category": category,
        "status": "open",
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
    }
    TICKETS.append(ticket)
    user.last_ticket_id = ticket["id"]
    return ticket

# -----------------------------
# Utility: Intent analysis (very simple)
# -----------------------------

def analyze_intent(message: str) -> str:
    m = message.lower()
    if any(w in m for w in ["refund", "charge", "billing", "invoice", "payment"]):
        return "billing"
    if any(w in m for w in ["error", "bug", "not working", "crash", "restart", "slow", "timeout"]):
        return "technical"
    return "general"

# -----------------------------
# Output guardrail (optional bonus)
# -----------------------------
class OutputGuardrail:
    def __init__(self, banned_phrases: Optional[List[str]] = None):
        self.banned_phrases = banned_phrases or ["sorry", "apologize"]

    def enforce(self, text: str) -> str:
        lowered = text.lower()
        for b in self.banned_phrases:
            if b in lowered:
                # remove banned phrase occurrences (simple approach)
                text = text.replace(b, "[redacted]")
        return text

# -----------------------------
# Tools with dynamic is_enabled logic
# -----------------------------
class Tool:
    def __init__(self, func: Callable, name: Optional[str] = None, is_enabled: Optional[Callable[[UserContext], bool]] = None):
        self.func = func
        self.name = name or func.__name__
        self.is_enabled = is_enabled or (lambda ctx: True)

    def run(self, *args, stream: bool = False, **kwargs):
        # stream_events simulation
        if stream:
            print(f"[stream] starting tool {self.name}...")
            time.sleep(0.15)
        res = self.func(*args, **kwargs)
        if stream:
            print(f"[stream] finished tool {self.name} — result: {str(res)[:120]}")
        return res

# Tools definitions
@function_tool
def create_ticket_tool(title: str, description: str, context: UserContext) -> dict:
    ticket = create_ticket_record(title, description, context, category=context.issue_type or "general")
    return {"ok": True, "ticket": ticket}

@function_tool
def refund_tool(ticket_id: str, context: UserContext) -> dict:
    # refund only allowed if is_premium_user == True (enforced by is_enabled)
    # Simulate refund
    for t in TICKETS:
        if t["id"] == ticket_id:
            t["status"] = "refunded"
            return {"ok": True, "ticket": t, "message": "Refund processed."}
    return {"ok": False, "reason": "ticket_not_found"}

@function_tool
def restart_service_tool(service_name: str, context: UserContext) -> dict:
    # Simulate a service restart
    if context.issue_type != "technical":
        return {"ok": False, "reason": "wrong_issue_type"}
    # pretend restart
    time.sleep(0.2)
    return {"ok": True, "message": f"Service '{service_name}' restarted successfully."}

@function_tool
def check_subscription_tool(email: str, context: UserContext) -> dict:
    # Simple simulation: premium if email contains 'pro' or context flag set
    is_premium = context.is_premium_user or (email and "pro" in (email.lower() if email else ""))
    return {"email": email, "is_premium": bool(is_premium)}

# Wrap tools with dynamic gating
CREATE_TICKET = Tool(create_ticket_tool, name="create_ticket", is_enabled=lambda ctx: True)
REFUND = Tool(refund_tool, name="refund", is_enabled=lambda ctx: ctx.is_premium_user is True)
RESTART = Tool(restart_service_tool, name="restart_service", is_enabled=lambda ctx: ctx.issue_type == "technical")
CHECK_SUB = Tool(check_subscription_tool, name="check_subscription", is_enabled=lambda ctx: True)

# -----------------------------
# Agents
# -----------------------------
class BaseAgent:
    def __init__(self, name: str, tools: Optional[List[Tool]] = None, guardrail: Optional[OutputGuardrail] = None):
        self.name = name
        self.tools = {t.name: t for t in (tools or [])}
        self.guardrail = guardrail

    def can_use(self, tool_name: str, context: UserContext) -> bool:
        t = self.tools.get(tool_name)
        return bool(t and t.is_enabled(context))

    def call_tool(self, tool_name: str, *args, stream: bool = False, **kwargs):
        t = self.tools.get(tool_name)
        if not t:
            return {"ok": False, "reason": "tool_not_found"}
        return t.run(*args, **kwargs, stream=stream)

    def respond(self, message: str, context: UserContext) -> str:
        # default echo -- specialized agents override
        out = f"{self.name} received: {message}"
        if self.guardrail:
            out = self.guardrail.enforce(out)
        return out

class TriageAgent(BaseAgent):
    def __init__(self, name: str, agents: Dict[str, 'BaseAgent'], guardrail: Optional[OutputGuardrail] = None):
        super().__init__(name=name, tools=[], guardrail=guardrail)
        self.agents = agents

    def handle(self, message: str, context: UserContext) -> dict:
        # Analyze intent and decide handoff
        intent = analyze_intent(message)
        context.issue_type = intent
        # simple scoring for premium detection
        if not context.is_premium_user and context.email and "pro" in context.email.lower():
            context.is_premium_user = True

        print(f"[ 🧭 Triage] intent detected: {intent} | is_premium: {context.is_premium_user}")

        # handoff mapping
        if intent == "billing":
            target = self.agents.get("billing")
        elif intent == "technical":
            target = self.agents.get("technical")
        else:
            target = self.agents.get("general")

        print(f"[ 🧭 Triage] handing off to: {target.name}")
        return {"handoff_to": target, "context": context}

class BillingAgent(BaseAgent):
    def __init__(self, name: str, tools: List[Tool], guardrail: Optional[OutputGuardrail] = None):
        super().__init__(name=name, tools=tools, guardrail=guardrail)

    def respond(self, message: str, context: UserContext) -> str:
        # Simple logic: if user asks for refund, try refund tool (requires premium)
        m = message.lower()
        if "refund" in m or "charge" in m:
            # Need a ticket first
            if not context.last_ticket_id:
                t_res = self.call_tool("create_ticket", title="Billing issue", description=message, context=context)
                if t_res.get("ok"):
                    tid = t_res["ticket"]["id"]
                    print(f"[Billing] created ticket {tid}")
            # Attempt refund if tool enabled
            if self.can_use("refund", context):
                res = self.call_tool("refund", context.last_ticket_id or tid, context=context)
                out = f" 💰 Refund result: {res}"
            else:
                out = " ⚠️ Refunds are available only to premium users. Please upgrade or contact billing."
        else:
            out = "BillingAgent: I can help with refunds, charges, and invoices."
        if self.guardrail:
            out = self.guardrail.enforce(out)
        return out

class TechnicalAgent(BaseAgent):
    def __init__(self, name: str, tools: List[Tool], guardrail: Optional[OutputGuardrail] = None):
        super().__init__(name=name, tools=tools, guardrail=guardrail)

    def respond(self, message: str, context: UserContext) -> str:
        m = message.lower()
        if "restart" in m or "not working" in m or "error" in m:
            if not context.issue_type:
                context.issue_type = "technical"
            if self.can_use("restart_service", context):
                svc = "main-service"
                res = self.call_tool("restart_service", svc, context=context, stream=True)
                out = f" 🔧 TechnicalAgent: {res.get('message')}"
            else:
                out = "Restart is not permitted for your issue type or the agent cannot perform it."
        else:
            out = "TechnicalAgent: I can attempt to restart services or create a ticket for engineering."
        if self.guardrail:
            out = self.guardrail.enforce(out)
        return out

class GeneralAgent(BaseAgent):
    def __init__(self, name: str, tools: List[Tool], guardrail: Optional[OutputGuardrail] = None):
        super().__init__(name=name, tools=tools, guardrail=guardrail)

    def respond(self, message: str, context: UserContext) -> str:
        # generic help: create ticket
        t_res = self.call_tool("create_ticket", title="General inquiry", description=message, context=context)
        if t_res.get("ok"):
            out = f" 📩 GeneralAgent: Created ticket {t_res['ticket']['id']} for your request."
        else:
            out = " 📩 GeneralAgent: Could not create a ticket right now."
        if self.guardrail:
            out = self.guardrail.enforce(out)
        return out

# -----------------------------
# Build agents and wire them
# -----------------------------
guardrail = OutputGuardrail(banned_phrases=["sorry", "apologize"])  # optional bonus

billing_agent = BillingAgent("BillingAgent", tools=[CREATE_TICKET, REFUND, CHECK_SUB], guardrail=guardrail)
technical_agent = TechnicalAgent("TechnicalAgent", tools=[CREATE_TICKET, RESTART], guardrail=guardrail)
general_agent = GeneralAgent("GeneralAgent", tools=[CREATE_TICKET], guardrail=guardrail)

agents_map = {
    "billing": billing_agent,
    "technical": technical_agent,
    "general": general_agent,
}

triage_agent = TriageAgent("TriageAgent", agents=agents_map, guardrail=guardrail)

# -----------------------------
# Console CLI
# -----------------------------

def print_help():
   print("Commands:")
print("  🪪 identify <Name> <email>   - set user identity and premium detection")
print("  💬 ask <message>             - ask the system (triage + handoff)")
print("  👤 show_context              - show current user context")
print("  🎟️ tickets                   - list tickets (in-memory)")
print("  ❓ help                      - show this help")
print("  🚪 quit                      - exit")



def cli_loop():
    ctx = UserContext()
    print("🤖 Multi-Agent Console Support System — Assignment")

    print_help()

    while True:
        try:
            raw = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye")
            break
        if not raw:
            continue
        if raw.lower() in ("quit", "exit"):
            print("Bye 👋")
            break
        if raw.lower() == "help":
            print_help()
            continue
        if raw.lower() == "show_context":
            print(ctx.json(indent=2))
            continue
        if raw.lower() == "tickets":
            if not TICKETS:
                print("No tickets yet")
            else:
                for t in TICKETS:
                    print(f"-   🎫 {t['id']} | {t['title']} | {t['status']} | {t['category']}")
            continue
        if raw.startswith("identify "):
            parts = raw.split(maxsplit=2)
            if len(parts) < 3:
                print("Usage: identify <Name> <email>")
                continue
            name, email = parts[1], parts[2]
            ctx.name = name
            ctx.email = email
            # simple premium detection
            if "pro" in email.lower():
                ctx.is_premium_user = True
            print(f" ✅ Identified {ctx.name} <{ctx.email}> | premium: {ctx.is_premium_user}")
            continue
        if raw.startswith("ask "):
            msg = raw[4:]
            # Triage handles intent and chooses agent
            triage_res = triage_agent.handle(msg, ctx)
            target_agent: BaseAgent = triage_res["handoff_to"]
            print(f"[System] Handing off to {target_agent.name} with context: issue_type={ctx.issue_type}, premium={ctx.is_premium_user}")
            # Let the target agent respond
            response = target_agent.respond(msg, ctx)
            print(f"[{target_agent.name}] {response}")
            continue

        print("Unknown command. Type 'help' for commands.")


if __name__ == "__main__":
    cli_loop()










