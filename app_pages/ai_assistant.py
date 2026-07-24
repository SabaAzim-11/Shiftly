"""ShiftSync AI – AI Workforce Assistant page"""

import streamlit as st
import os
import json
from datetime import date
from utils.data import (get_employees, get_workforce_summary,
                         get_leave_requests, get_attendance_today)


def _build_context() -> str:
    """Build a rich context string from live DB data for the AI."""
    s      = get_workforce_summary()
    emps   = get_employees()
    today_att = get_attendance_today()
    pending   = get_leave_requests(status="Pending")

    emp_list = emps[["emp_id","name","department","shift","weekly_off"]].to_dict("records")
    att_list = today_att[["name","department","shift","status"]].to_dict("records")

    ctx = f"""You are ShiftSync AI, an intelligent Workforce Management Assistant.
Today: {date.today().strftime('%A, %d %B %Y')}

LIVE WORKFORCE DATA:
- Total Employees: {s['total']}
- Present Today: {s['present']}
- Absent Today: {s['absent']}
- On Leave Today: {s['on_leave']}
- On Weekly Off: {s['weekly_off']}
- Workforce Coverage: {s['coverage']}%
- Pending Leave Approvals: {s['pending_leaves']}

EMPLOYEE DIRECTORY (summary):
{json.dumps(emp_list, indent=2)}

TODAY'S ATTENDANCE:
{json.dumps(att_list, indent=2)}

PENDING LEAVE REQUESTS:
{json.dumps(pending[['employee','department','leave_type','from_date','to_date','days']].to_dict('records') if not pending.empty else [], indent=2)}

You can answer questions about:
- Individual employee shifts, weekly offs, attendance
- Department-wise headcounts and coverage
- Leave requests and approvals
- Workforce analytics and trends
- Shift rotation recommendations
- HR policy explanations

Keep answers concise, structured, and data-driven. Use bullet points for lists.
Never make up data — only use what is provided above."""
    return ctx


def _call_anthropic(messages: list, system: str) -> str:
    """Call Anthropic API — key read from environment or st.secrets."""
    try:
        import anthropic
    except ImportError:
        return "❌ `anthropic` package not installed. Run: `pip install anthropic`"

    api_key = (
        os.getenv("ANTHROPIC_API_KEY") or
        st.secrets.get("ANTHROPIC_API_KEY", "")
    )
    if not api_key:
        return (
            "⚠️ **API key not configured.**\n\n"
            "Add `ANTHROPIC_API_KEY` to:\n"
            "- `.streamlit/secrets.toml`  →  `ANTHROPIC_API_KEY = 'sk-ant-...'`\n"
            "- Or set it as an environment variable before running Streamlit."
        )

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        return response.content[0].text
    except anthropic.AuthenticationError:
        return "❌ Invalid API key. Check your `ANTHROPIC_API_KEY`."
    except anthropic.RateLimitError:
        return "⚠️ Rate limit reached. Please wait a moment and try again."
    except Exception as e:
        return f"❌ API error: {str(e)}"


SUGGESTIONS = [
    "What is my shift today?",
    "Who is absent today?",
    "Show workforce coverage",
    "How many leaves are pending?",
    "List night shift employees",
    "Which department has most absences?",
    "Who is on leave this week?",
    "Suggest shift rotation improvements",
]


def render():
    st.markdown("### 🤖 AI Workforce Assistant")
    st.caption("Ask anything about employees, shifts, attendance, and leaves in plain English")
    st.markdown("---")

    # ── Init session state ────────────────────────────────────────────────────
    if "ai_messages" not in st.session_state:
        st.session_state["ai_messages"] = []
    if "ai_context" not in st.session_state:
        st.session_state["ai_context"] = _build_context()

    # ── Suggestion chips ──────────────────────────────────────────────────────
    st.markdown("**Quick Questions:**")
    chips = st.columns(4)
    for i, suggestion in enumerate(SUGGESTIONS):
        with chips[i % 4]:
            if st.button(suggestion, key=f"chip_{i}", use_container_width=True):
                st.session_state["pending_message"] = suggestion

    st.markdown("---")

    # ── Chat history ──────────────────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        if not st.session_state["ai_messages"]:
            st.markdown(
                '<div style="background:#1e2435;border-radius:4px 12px 12px 12px;'
                'padding:14px;max-width:75%;margin-bottom:12px;font-size:13px;color:#e8eaf0;line-height:1.6">'
                '👋 <strong>Hello! I\'m ShiftSync AI.</strong><br><br>'
                'I have live access to your workforce data — employees, shifts, attendance, '
                'and leaves. Ask me anything!<br><br>'
                '<em>Try: "Who is absent today?" or "Show night shift employees"</em>'
                '</div>',
                unsafe_allow_html=True
            )

        for msg in st.session_state["ai_messages"]:
            if msg["role"] == "user":
                st.markdown(
                    f'<div style="display:flex;justify-content:flex-end;margin-bottom:10px">'
                    f'<div style="background:#4f8ef7;border-radius:12px 4px 12px 12px;'
                    f'padding:10px 14px;max-width:70%;font-size:13px;color:#fff;line-height:1.5">'
                    f'{msg["content"]}</div></div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div style="background:#1e2435;border-radius:4px 12px 12px 12px;'
                    f'padding:12px 16px;max-width:75%;margin-bottom:12px;'
                    f'font-size:13px;color:#e8eaf0;line-height:1.6">'
                    f'{msg["content"].replace(chr(10), "<br>")}</div>',
                    unsafe_allow_html=True
                )

    # ── Input box ─────────────────────────────────────────────────────────────
    col_input, col_send, col_clear = st.columns([5, 1, 1])
    with col_input:
        user_input = st.text_input(
            "Message",
            value=st.session_state.pop("pending_message", ""),
            placeholder="Ask about shifts, attendance, employees, leaves…",
            label_visibility="collapsed",
            key="ai_input_box",
        )
    with col_send:
        send = st.button("Send ↗", type="primary", use_container_width=True)
    with col_clear:
        if st.button("🗑 Clear", use_container_width=True):
            st.session_state["ai_messages"] = []
            st.rerun()

    # ── Process message ───────────────────────────────────────────────────────
    if send and user_input.strip():
        st.session_state["ai_messages"].append({"role": "user", "content": user_input.strip()})

        with st.spinner("ShiftSync AI is thinking…"):
            # Refresh context on every call so it uses live data
            system_ctx = _build_context()
            api_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state["ai_messages"]
            ]
            reply = _call_anthropic(api_messages, system_ctx)

        st.session_state["ai_messages"].append({"role": "assistant", "content": reply})
        st.rerun()

    # ── Data refresh button ───────────────────────────────────────────────────
    with st.expander("⚙ Settings"):
        st.caption("The AI context refreshes automatically on each message.")
        if st.button("🔄 Manually Refresh Workforce Data"):
            st.session_state["ai_context"] = _build_context()
            st.success("Context refreshed with latest data.")
        st.markdown("**API Key Status:**")
        api_key = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")
        if api_key:
            st.success(f"✅ API key loaded ({api_key[:12]}…)")
        else:
            st.error("❌ No API key found. Add it to `.streamlit/secrets.toml`")