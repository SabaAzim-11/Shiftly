"""
ShiftSync AI – Plotly chart builders (dark theme)
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── Theme tokens ──────────────────────────────────────────────────────────────
BG      = "#0f1117"
BG2     = "#161b27"
BORDER  = "#2a3350"
TEXT    = "#e8eaf0"
TEXT2   = "#9aa3c0"
TEXT3   = "#6b7494"

DEPT_COLORS = {
    "Production": "#4f8ef7",
    "IT":         "#a78bfa",
    "HR":         "#2dd4bf",
    "Finance":    "#fbbf24",
    "Security":   "#f87171",
    "Logistics":  "#4ade80",
}
SHIFT_COLORS = {
    "General": "#4f8ef7",
    "A":       "#fbbf24",
    "B":       "#a78bfa",
    "Morning": "#fbbf24",
    "Evening": "#a78bfa",
    "Night":   "#6b7494",
}
STATUS_COLORS = {
    "Present":    "#4ade80",
    "Absent":     "#f87171",
    "Leave":      "#fbbf24",
    "Weekly Off": "#a78bfa",
    "Holiday":    "#4f8ef7",
}


def _layout(fig, title: str = "", height: int = 320):
    fig.update_layout(
        title=dict(text=title, font=dict(color=TEXT, size=14), x=0),
        paper_bgcolor=BG2,
        plot_bgcolor=BG2,
        font=dict(color=TEXT2, family="Inter, sans-serif", size=12),
        margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        height=height,
        showlegend=True,
        legend=dict(
            bgcolor=BG2, bordercolor=BORDER, borderwidth=1,
            font=dict(color=TEXT2, size=11),
        ),
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER, tickcolor=BORDER, tickfont=dict(color=TEXT3)),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER, tickcolor=BORDER, tickfont=dict(color=TEXT3)),
    )
    return fig


# ── Charts ────────────────────────────────────────────────────────────────────

def dept_bar_chart(df: pd.DataFrame) -> go.Figure:
    colors = [DEPT_COLORS.get(d, "#4f8ef7") for d in df["department"]]
    fig = go.Figure(go.Bar(
        x=df["count"], y=df["department"],
        orientation="h",
        marker_color=colors,
        text=df["count"], textposition="outside",
        textfont=dict(color=TEXT2),
    ))
    fig.update_layout(
        paper_bgcolor=BG2, plot_bgcolor=BG2,
        font=dict(color=TEXT2, family="Inter"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        showlegend=False,
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER, tickfont=dict(color=TEXT3)),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER, tickfont=dict(color=TEXT3)),
    )
    return fig


def shift_donut(df: pd.DataFrame) -> go.Figure:
    colors = [SHIFT_COLORS.get(s, "#4f8ef7") for s in df["shift"]]
    fig = go.Figure(go.Pie(
        labels=df["shift"], values=df["count"],
        hole=0.6,
        marker=dict(colors=colors, line=dict(color=BG2, width=2)),
        textfont=dict(color=TEXT),
        hovertemplate="%{label}: %{value} employees<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=BG2, plot_bgcolor=BG2,
        font=dict(color=TEXT2, family="Inter"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        legend=dict(bgcolor=BG2, bordercolor=BORDER, font=dict(color=TEXT2, size=11)),
        annotations=[dict(
            text=f"{df['count'].sum()}<br><span style='font-size:9px'>Employees</span>",
            x=0.5, y=0.5, font_size=18, font_color=TEXT,
            showarrow=False, xanchor="center"
        )],
    )
    return fig


def attendance_status_donut(summary: dict) -> go.Figure:
    labels = ["Present", "Absent", "On Leave", "Weekly Off"]
    values = [summary["present"], summary["absent"], summary["on_leave"], summary["weekly_off"]]
    colors = ["#4ade80", "#f87171", "#fbbf24", "#a78bfa"]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.6,
        marker=dict(colors=colors, line=dict(color=BG2, width=2)),
        hovertemplate="%{label}: %{value}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=BG2, plot_bgcolor=BG2,
        font=dict(color=TEXT2, family="Inter"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        legend=dict(bgcolor=BG2, bordercolor=BORDER, font=dict(color=TEXT2, size=11)),
        annotations=[dict(
            text=f"{summary['coverage']}%<br><span style='font-size:9px'>Coverage</span>",
            x=0.5, y=0.5, font_size=20, font_color="#4ade80",
            showarrow=False, xanchor="center"
        )],
    )
    return fig


def attendance_trend_line(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    pivoted = df.pivot_table(index="att_date", columns="status", values="count", aggfunc="sum").fillna(0)

    color_map = STATUS_COLORS
    for status in ["Present", "Absent", "Leave", "Weekly Off"]:
        if status in pivoted.columns:
            fig.add_trace(go.Scatter(
                x=pivoted.index, y=pivoted[status],
                name=status,
                line=dict(color=color_map.get(status, "#4f8ef7"), width=2),
                mode="lines+markers",
                marker=dict(size=4),
                fill="tozeroy" if status == "Present" else None,
                fillcolor="rgba(79,142,247,0.07)" if status == "Present" else None,
                hovertemplate=f"{status}: %{{y}}<extra></extra>",
            ))
    _layout(fig, "Attendance Trend", 280)
    fig.update_layout(hovermode="x unified")
    return fig


def monthly_trend_area(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col, color in [("Present","#4ade80"),("Absent","#f87171"),("Leave","#fbbf24")]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df["month"], y=df[col].astype(int),
                name=col,
                line=dict(color=color, width=2),
                mode="lines+markers",
                marker=dict(size=5),
                hovertemplate=f"{col}: %{{y}}<extra></extra>",
            ))
    _layout(fig, "6-Month Workforce Trend", 280)
    return fig


def leave_type_bar(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=df["name"], y=df["allocated"] - df["used"],
        name="Remaining",
        marker_color="#4f8ef7",
        text=(df["allocated"] - df["used"]).astype(int),
        textposition="outside",
        textfont=dict(color=TEXT2),
    ))
    fig.add_trace(go.Bar(
        x=df["name"], y=df["used"],
        name="Used",
        marker_color="#f87171",
    ))
    fig.update_layout(
        barmode="stack",
        paper_bgcolor=BG2, plot_bgcolor=BG2,
        font=dict(color=TEXT2, family="Inter"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        legend=dict(bgcolor=BG2, bordercolor=BORDER, font=dict(color=TEXT2, size=11)),
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER, tickfont=dict(color=TEXT3)),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER, tickfont=dict(color=TEXT3)),
    )
    return fig


def absenteeism_bar(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=df["department"], y=df["rate"],
        marker_color=[DEPT_COLORS.get(d, "#4f8ef7") for d in df["department"]],
        text=[f"{r}%" for r in df["rate"]],
        textposition="outside",
        textfont=dict(color=TEXT2),
    ))
    fig.update_layout(
        paper_bgcolor=BG2, plot_bgcolor=BG2,
        font=dict(color=TEXT2, family="Inter"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        showlegend=False,
        xaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT3)),
        yaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT3), title="Absence Rate %"),
    )
    return fig


def weekly_off_distribution(df: pd.DataFrame) -> go.Figure:
    days_order = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
    df["day"] = pd.Categorical(df["day"], categories=days_order, ordered=True)
    df = df.sort_values("day")
    fig = go.Figure(go.Bar(
        x=df["day"], y=df["count"],
        marker_color="#a78bfa",
        text=df["count"], textposition="outside",
        textfont=dict(color=TEXT2),
    ))
    fig.update_layout(
        paper_bgcolor=BG2, plot_bgcolor=BG2,
        font=dict(color=TEXT2, family="Inter"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=240,
        showlegend=False,
        xaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT3)),
        yaxis=dict(gridcolor=BORDER, tickfont=dict(color=TEXT3)),
    )
    return fig