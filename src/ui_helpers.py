import html
import inspect
import streamlit as st


GREEN = "#2E7D32"


# ============================================================
# Formatting helpers
# ============================================================

def esc(value):
    """Safely escape HTML text."""
    return html.escape(str(value))


def fmt_kg(value, decimals=0):
    """Format kg safely."""
    if value is None:
        return "Unavailable"

    try:
        return f"{float(value):,.{decimals}f} kg"
    except (TypeError, ValueError):
        return "Unavailable"


def fmt_tonnes(value, decimals=2):
    """Convert kg to tonnes safely."""
    if value is None:
        return "Unavailable"

    try:
        value = float(value)
    except (TypeError, ValueError):
        return "Unavailable"

    return f"{value / 1000:,.{decimals}f} tCO2e"


def fmt_t(value, decimals=2):
    return fmt_tonnes(value, decimals)


def fmt_pct(value, decimals=1):
    if value is None:
        return "Unavailable"

    try:
        return f"{float(value):,.{decimals}f}%"
    except (TypeError, ValueError):
        return "Unavailable"


def fmt_number(value, decimals=0):
    if value is None:
        return "Unavailable"

    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "Unavailable"


# ============================================================
# Streamlit helpers
# ============================================================

def stretch_kwargs(fn):
    """
    Compatibility helper.
    """

    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return {}

    if "width" in params:
        return {
            "width": "stretch"
        }

    if "use_container_width" in params:
        return {
            "use_container_width": True
        }

    return {}


# ============================================================
# CSS
# ============================================================

CSS = """
<style>

.block-container {
    padding-top: 1.4rem;
    max-width: 1280px;
}


.cw-hero {
    background: linear-gradient(
        135deg,
        #1B5E20,
        #2E7D32,
        #00897B
    );
    color:white;
    padding:22px 28px;
    border-radius:16px;
    margin-bottom:14px;
}


.cw-title {
    font-size:1.9rem;
    font-weight:800;
}


.cw-sub {
    color:#E8F5E9;
}


.cw-kpi {
    background:white;
    border:1px solid #e5e7eb;
    border-radius:12px;
    padding:14px 16px;
    min-height:108px;
}


.cw-kpi-label {
    font-size:.72rem;
    color:#6b7280;
    text-transform:uppercase;
}


.cw-kpi-value {
    font-size:1.6rem;
    font-weight:800;
    color:#111827;
}


.cw-kpi-help {
    font-size:.8rem;
    color:#6b7280;
}


.cw-card {
    background:white;
    border:1px solid #e5e7eb;
    border-radius:12px;
    padding:16px;
    margin:10px 0;
}


.cw-callout {
    padding:12px 16px;
    border-radius:10px;
    margin:8px 0;
}


.cw-callout-info {
    background:#E3F2FD;
}


.cw-callout-warn {
    background:#FFF8E1;
}


.cw-callout-good {
    background:#E8F5E9;
}

</style>
"""


def inject_css():
    st.markdown(
        CSS,
        unsafe_allow_html=True,
    )


# ============================================================
# Basic UI
# ============================================================

def show_chart(fig, key=None):

    if fig is None:
        return

    st.plotly_chart(
        fig,
        key=key,
        **stretch_kwargs(st.plotly_chart)
    )


def hero(title, subtitle=""):

    st.markdown(
        f"""
        <div class="cw-hero">
            <div class="cw-title">
                {esc(title)}
            </div>
            <div class="cw-sub">
                {esc(subtitle)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title, subtitle=""):

    st.markdown(
        f"""
        <h2 style="color:#1B5E20">
        {esc(title)}
        </h2>
        """,
        unsafe_allow_html=True,
    )

    if subtitle:
        st.caption(subtitle)


def callout(text, kind="info"):

    if kind not in (
        "info",
        "warn",
        "good",
    ):
        kind = "info"

    st.markdown(
        f"""
        <div class="cw-callout cw-callout-{kind}">
            {esc(text)}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# KPI
# ============================================================

def kpi_card_html(label, value, help_text=""):

    return f"""
    <div style="
        background:white;
        padding:20px;
        border-radius:10px;
        border:1px solid #ddd;
    ">
        <h4>{label}</h4>
        <h2>{value}</h2>
        <p>{help_text}</p>
    </div>
    """


def kpi_row(cards):

    if not cards:
        return

    columns = st.columns(len(cards))

    for column, card in zip(columns, cards):

        label = card.get("label", "")
        value = card.get("value", "")
        help_text = card.get("help", card.get("sub", ""))

        with column:
            st.markdown(
                kpi_card_html(
                    label,
                    value,
                    help_text
                ),
                unsafe_allow_html=True
            )
        # ============================================================
# Recommendation cards
# ============================================================

def recommendation_card_html(
    rec,
    index=1
):

    if not isinstance(
        rec,
        dict
    ):
        return ""

    title = rec.get(
        "action",
        rec.get(
            "title",
            "Recommendation"
        )
    )

    priority = rec.get(
        "priority",
        "Low"
    )

    category = rec.get(
        "category",
        ""
    )

    timeframe = rec.get(
        "timeframe",
        ""
    )

    investment = rec.get(
        "investment",
        ""
    )

    why = rec.get(
        "why",
        ""
    )

    description = rec.get(
        "description",
        ""
    )

    estimate = rec.get(
        "estimate_text",
        ""
    )

    lever = rec.get(
        "lever_text",
        ""
    )


    return f"""
    <div class="cw-card">

        <h3>
            {index}. {esc(title)}
        </h3>

        <p>
            <b>Priority:</b>
            {esc(priority)}
        </p>

        <p>
            <b>Category:</b>
            {esc(category)}
        </p>

        <p>
            <b>Timeframe:</b>
            {esc(timeframe)}
        </p>

        <p>
            <b>Investment:</b>
            {esc(investment)}
        </p>

        <p>
            <b>Why:</b>
            {esc(why)}
        </p>

        <p>
            <b>Action:</b>
            {esc(description)}
        </p>

        <p>
            <b>Estimated potential:</b>
            {esc(estimate)}
        </p>

        <p>
            <b>Simulator:</b>
            {esc(lever)}
        </p>

    </div>
    """



# ============================================================
# Scenario cards
# ============================================================

def scenario_card_html(
    scenario
):

    if not isinstance(
        scenario,
        dict
    ):
        return ""

    name = scenario.get(
        "name",
        "Scenario"
    )

    description = scenario.get(
        "description",
        ""
    )

    emissions = scenario.get(
        "emissions_kg",
        None
    )

    reduction = scenario.get(
        "reduction_pct",
        0
    )

    actions = scenario.get(
        "actions",
        []
    )


    action_html = ""

    if isinstance(
        actions,
        list
    ):

        for action in actions:

            action_html += (
                f"<li>{esc(action)}</li>"
            )


    return f"""
    <div class="cw-card">

        <h3>
            {esc(name)}
        </h3>

        <p>
            {esc(description)}
        </p>

        <p>
            <b>Emissions:</b>
            {fmt_tonnes(emissions)}
        </p>

        <p>
            <b>Reduction:</b>
            {fmt_pct(reduction)}
        </p>

        <ul>
            {action_html}
        </ul>

    </div>
    """



# ============================================================
# Footer
# ============================================================

def footer():

    st.markdown(
        """
        <hr>

        <div style="
            text-align:center;
            color:#6b7280;
            font-size:0.85rem;
        ">

        CarbonWise AI · ML-Powered Carbon Intelligence
        & Net-Zero Planning

        </div>
        """,
        unsafe_allow_html=True,
    )



# ============================================================
# Exports
# ============================================================

__all__ = [

    "esc",
    "fmt_kg",
    "fmt_tonnes",
    "fmt_t",
    "fmt_pct",
    "fmt_number",

    "stretch_kwargs",
    "inject_css",

    "show_chart",
    "hero",
    "section",
    "callout",

    "kpi_card_html",
    "kpi_row",

    "recommendation_card_html",
    "scenario_card_html",

    "footer",

]
