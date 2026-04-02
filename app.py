import datetime
import streamlit as st
import plotly.graph_objects as go
from scanner import scan

st.set_page_config(page_title="agentready", page_icon="🤖", layout="wide")

# ── Global styles ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .block-container { padding-top: 2rem; padding-bottom: 2rem; }
  .check-card {
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    border-left: 5px solid;
  }
  .check-pass  { background:#0d2b1e; border-color:#2ecc71; }
  .check-warn  { background:#2b2210; border-color:#f39c12; }
  .check-fail  { background:#2b1010; border-color:#e74c3c; }
  .check-title { font-size:15px; font-weight:600; margin:0 0 4px 0; }
  .check-pts   { font-size:12px; opacity:.7; float:right; margin-top:-22px; }
  .check-detail{ font-size:13px; opacity:.85; margin:4px 0 0 0; }
  .badge {
    display:inline-block; border-radius:12px;
    padding:2px 10px; font-size:12px; font-weight:600; margin-right:6px;
  }
  .badge-easy   { background:#1a4a1a; color:#2ecc71; }
  .badge-medium { background:#4a3500; color:#f39c12; }
  .badge-hard   { background:#4a1010; color:#e74c3c; }
  .fix-card {
    border-radius:8px; padding:12px 16px; margin-bottom:8px;
    background:#1a1a2e; border:1px solid #2a2a4a;
  }
  .fix-title { font-size:14px; font-weight:600; margin:0 0 4px 0; }
  .fix-action{ font-size:13px; opacity:.8; margin:0; }

  /* Sidebar cards */
  .sb-card {
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 12px;
  }
  .sb-card-stat {
    background: #0f1f2e;
    border: 1px solid #1a3a52;
  }
  .sb-card-meth {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
  }
  .sb-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: #4a9eda;
    margin: 0 0 6px 0;
  }
  .sb-stat-num {
    font-size: 28px;
    font-weight: 800;
    color: #fff;
    margin: 0;
    line-height: 1.1;
  }
  .sb-stat-sub {
    font-size: 12px;
    color: #888;
    margin: 4px 0 0 0;
  }
  .sb-body {
    font-size: 13px;
    color: #bbb;
    margin: 0;
    line-height: 1.6;
  }
  .sb-cmp-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 0;
    border-bottom: 1px solid #222;
    font-size: 12px;
  }
  .sb-cmp-row:last-child { border-bottom: none; }
  .sb-cmp-tool  { color: #ccc; font-weight: 500; }
  .sb-cmp-check { color: #888; }
  .sb-cmp-you   { color: #2ecc71; font-weight: 600; }
  .sb-footer {
    font-size: 11px;
    color: #555;
    text-align: center;
    margin-top: 6px;
  }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='padding:8px 0 16px 0;'>"
        "<span style='font-size:20px; font-weight:800; color:#fff;'>🤖 agentready</span><br>"
        "<span style='font-size:12px; color:#666;'>AI purchasing agent readiness scanner</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Why it matters — stat card
    st.markdown(
        "<div class='sb-card sb-card-stat'>"
        "  <p class='sb-label'>Why it matters</p>"
        "  <p class='sb-stat-num'>40%</p>"
        "  <p class='sb-stat-sub'>of enterprise apps will embed AI procurement agents by end of 2026</p>"
        "  <p class='sb-body' style='margin-top:10px;'>"
        "    Sites that score poorly get <strong style='color:#e74c3c;'>filtered out</strong> "
        "    before a human ever reviews them."
        "  </p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # How it's different — comparison rows
    st.markdown(
        "<div class='sb-card sb-card-meth'>"
        "  <p class='sb-label'>How it's different</p>"
        "  <div class='sb-cmp-row'>"
        "    <span class='sb-cmp-tool'>Profound / Peec AI</span>"
        "    <span class='sb-cmp-check'>Brand mentions</span>"
        "  </div>"
        "  <div class='sb-cmp-row'>"
        "    <span class='sb-cmp-tool'>Google Lighthouse</span>"
        "    <span class='sb-cmp-check'>Human UX</span>"
        "  </div>"
        "  <div class='sb-cmp-row'>"
        "    <span class='sb-cmp-tool sb-cmp-you'>agentready ✓</span>"
        "    <span class='sb-cmp-you'>Agent actionability</span>"
        "  </div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Methodology
    st.markdown(
        "<div class='sb-card sb-card-meth'>"
        "  <p class='sb-label'>Methodology</p>"
        "  <p class='sb-body'>"
        "    Fully <strong style='color:#fff;'>deterministic</strong> — no LLM involved. "
        "    Fetches static HTML + robots.txt and runs "
        "    <strong style='color:#fff;'>7 rule-based checks</strong>. "
        "    Every result is reproducible and explainable."
        "  </p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<p class='sb-footer'>by Mohanish &nbsp;·&nbsp; MIT License</p>",
        unsafe_allow_html=True,
    )

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 2rem 0 1.5rem 0;">
  <h1 style="font-size:2.4rem; margin-bottom:0.4rem;">🤖 agentready</h1>
  <p style="font-size:1.1rem; color:#aaa; max-width:560px; margin:0 auto;">
    AI purchasing agents are evaluating your competitors right now.<br>
    Find out if they can even find <em>you</em>.
  </p>
</div>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "url_value" not in st.session_state:
    st.session_state["url_value"] = ""
if "auto_run" not in st.session_state:
    st.session_state["auto_run"] = False

# ── URL input (centred hero) ───────────────────────────────────────────────────
_, col_form, _ = st.columns([1, 3, 1])
with col_form:
    col_input, col_btn = st.columns([5, 1], gap="small")
    with col_input:
        url = st.text_input(
            "Website URL",
            value=st.session_state["url_value"],
            placeholder="https://yourcompany.com",
            label_visibility="collapsed",
        )
        st.session_state["url_value"] = url
    with col_btn:
        run = st.button("Scan →", type="primary", disabled=not bool(url), use_container_width=True)

# ── Example URLs (lower importance) ───────────────────────────────────────────
EXAMPLES = ["https://stripe.com", "https://hubspot.com", "https://salesforce.com"]
_, col_ex, _ = st.columns([1, 3, 1])
with col_ex:
    st.markdown(
        "<p style='font-size:12px; color:#666; margin: 4px 0 6px 0;'>Try an example:</p>",
        unsafe_allow_html=True,
    )
    ex_cols = st.columns(len(EXAMPLES))
    for col, ex in zip(ex_cols, EXAMPLES):
        with col:
            if st.button(ex.replace("https://", ""), key=f"ex_{ex}", use_container_width=True):
                st.session_state["url_value"] = ex
                st.session_state["auto_run"] = True
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ── Trigger scan ───────────────────────────────────────────────────────────────
should_run = run or st.session_state.get("auto_run", False)
if st.session_state.get("auto_run"):
    st.session_state["auto_run"] = False

if should_run and url:
    with st.spinner(f"Scanning {url} …"):
        result = scan(url)

    if "error" in result:
        st.error(f"Scan failed: {result['error']}")
        st.stop()

    score  = result["score"]
    checks = result["checks"]
    recs   = result["recommendations"]

    n_pass = sum(1 for c in checks if c["status"] == "pass")
    n_warn = sum(1 for c in checks if c["status"] == "warning")
    n_fail = sum(1 for c in checks if c["status"] == "fail")

    if score >= 80:
        score_color, label = "#2ecc71", "Agent-Ready"
    elif score >= 60:
        score_color, label = "#27ae60", "Above Average"
    elif score >= 40:
        score_color, label = "#e67e22", "Average"
    elif score >= 20:
        score_color, label = "#e74c3c", "Below Average"
    else:
        score_color, label = "#c0392b", "Not Ready"

    st.divider()

    # ── Score row ──────────────────────────────────────────────────────────────
    col_gauge, col_metrics = st.columns([1, 1], gap="large")

    with col_gauge:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            number={"font": {"size": 52, "color": score_color}, "suffix": ""},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#555",
                         "tickfont": {"color": "#888"}},
                "bar": {"color": score_color, "thickness": 0.25},
                "bgcolor": "#1a1a1a",
                "borderwidth": 0,
                "steps": [
                    {"range": [0,  20], "color": "#2b1010"},
                    {"range": [20, 40], "color": "#2b1a10"},
                    {"range": [40, 60], "color": "#2b2210"},
                    {"range": [60, 80], "color": "#1a2b10"},
                    {"range": [80,100], "color": "#0d2b1e"},
                ],
                "threshold": {
                    "line": {"color": score_color, "width": 3},
                    "thickness": 0.8,
                    "value": score,
                },
            },
            title={"text": f"<b>{label}</b>", "font": {"size": 18, "color": score_color}},
            domain={"x": [0, 1], "y": [0, 1]},
        ))
        fig.update_layout(
            height=240,
            margin=dict(t=40, b=0, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            font={"color": "#ccc"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_metrics:
        st.markdown("<br><br>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("Passed", f"{n_pass}/{len(checks)}", delta=None)
        m2.metric("Warnings", n_warn)
        m3.metric("Failed", n_fail)

        # Mini bar chart — points per check
        bar_colors = [
            "#2ecc71" if c["status"] == "pass"
            else "#f39c12" if c["status"] == "warning"
            else "#e74c3c"
            for c in checks
        ]
        pct = [round(c["points_earned"] / c["points_max"] * 100) for c in checks]
        fig2 = go.Figure(go.Bar(
            x=[c["check"].replace(" (JSON-LD / Schema.org)", "").replace(" Parsability", "") for c in checks],
            y=pct,
            marker_color=bar_colors,
            text=[f"{p}%" for p in pct],
            textposition="outside",
            textfont={"size": 10},
        ))
        fig2.update_layout(
            height=180,
            margin=dict(t=10, b=0, l=0, r=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis={"visible": False, "range": [0, 120]},
            xaxis={"tickfont": {"size": 10, "color": "#aaa"}, "tickangle": -20},
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── Check results ──────────────────────────────────────────────────────────
    st.subheader("Check Results")
    for c in checks:
        if c["status"] == "pass":
            css, icon = "check-pass", "✅"
        elif c["status"] == "warning":
            css, icon = "check-warn", "⚠️"
        else:
            css, icon = "check-fail", "❌"

        pts = f"{c['points_earned']}/{c['points_max']} pts"
        detail_html = f"<p class='check-detail'>{c['detail']}</p>"
        fix_html = (
            f"<p class='check-detail' style='margin-top:6px;'>"
            f"<strong>Fix:</strong> {c['action']}</p>"
            if c["status"] != "pass" else ""
        )
        st.markdown(
            f"<div class='check-card {css}'>"
            f"  <p class='check-pts'>{pts}</p>"
            f"  <p class='check-title'>{icon} {c['check']}</p>"
            f"  {detail_html}{fix_html}"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Prioritised fix list ───────────────────────────────────────────────────
    if recs:
        st.divider()
        st.subheader("Prioritised Fix List")
        st.caption("Sorted by points available — highest ROI first.")

        effort_css = {"Easy": "badge-easy", "Medium": "badge-medium", "Hard": "badge-hard"}

        for i, r in enumerate(recs, 1):
            badge_cls = effort_css.get(r["effort_level"], "badge-medium")
            st.markdown(
                f"<div class='fix-card'>"
                f"  <p class='fix-title'>"
                f"    {i}. {r['check']}"
                f"    &nbsp;<span style='color:#888;font-weight:400;'>+{r['points_lost']} pts</span>"
                f"    &nbsp;<span class='badge {badge_cls}'>{r['effort_level']} · {r['effort_time']}</span>"
                f"  </p>"
                f"  <p class='fix-action'>{r['action']}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.success("All checks passed. Your site is well-positioned for agentic commerce.")

    # ── Download report ────────────────────────────────────────────────────────
    st.divider()
    lines = [
        "agentready Report",
        f"URL:   {result['url']}",
        f"Score: {score}/100  —  {label}",
        f"Date:  {datetime.date.today()}",
        "",
        "CHECK RESULTS",
        "─" * 52,
    ]
    for c in checks:
        s = "PASS" if c["status"] == "pass" else "WARN" if c["status"] == "warning" else "FAIL"
        lines.append(f"\n[{s}] {c['check']} — {c['points_earned']}/{c['points_max']} pts")
        lines.append(f"  Finding: {c['detail']}")
        if c["status"] != "pass":
            lines.append(f"  Fix:     {c['action']}")

    if recs:
        lines += ["", "", "PRIORITISED FIX LIST", "─" * 52]
        for i, r in enumerate(recs, 1):
            lines.append(
                f"\n{i}. {r['check']}  (+{r['points_lost']} pts)"
                f"  |  {r['effort_level']} · {r['effort_time']}"
            )
            lines.append(f"   {r['action']}")

    lines += ["", "─" * 52, "Generated by agentready · github.com/mohanishmhatre/agentready"]

    st.download_button(
        label="Download Report (.txt)",
        data="\n".join(lines),
        file_name=f"agentready_{result['url'].replace('https://', '').replace('/', '_')}.txt",
        mime="text/plain",
    )
