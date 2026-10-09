from typing import Optional

def format_trade_opened(order_ticket: int, symbol: str, side: str, lots: float, price: float, sl: Optional[float], tp: Optional[float]) -> str:
    return (
        f"🚀 *NEW TRADE EXECUTED*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"• *Ticket:* `{order_ticket}`\n"
        f"• *Symbol:* `{symbol}`\n"
        f"• *Side:* `{side}`\n"
        f"• *Volume:* `{lots}` Lots\n"
        f"• *Fill Price:* `{price:.2f}`\n"
        f"• *SL:* `{sl if sl else 'None'}` | *TP:* `{tp if tp else 'None'}`"
    )

def format_risk_rejection(symbol: str, reason: str, rule: str) -> str:
    return (
        f"⚠️ *SIGNAL REJECTED BY RISK ENGINE*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"• *Symbol:* `{symbol}`\n"
        f"• *Rule Violated:* `{rule}`\n"
        f"• *Reason:* {reason}"
    )

def format_emergency_stop(reason: str) -> str:
    return (
        f"🚨 *EMERGENCY STOP TRIGGERED*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Trading engine has entered EMERGENCY_STOP state.\n"
        f"• *Reason:* {reason}\n"
        f"• *Action:* New executions blocked. Operator intervention required."
    )
