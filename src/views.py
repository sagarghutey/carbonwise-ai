"""Streamlit tab renderers for CarbonWise AI v2.
Every renderer receives a ``ctx`` dict built in app.py from the persisted
analysis (st.session_state) plus the current widget values.
"""
import pandas as pd
import streamlit as st
import charts
from hotspots import accounting_table, build_insights, hotspot_insight, safe_div, top_hotspots
from net_zero import TARGET_YEARS
from reporting import DISCLAIMER, build_legacy_summary_df, build_report_df
from ui_helpers import (
    callout, fmt_t, kpi_row, recommendation_card_html, scenario_card_html,
    section, show_chart, stretch_kwargs,
)

WIDGET_DEFAULTS = {
    "in_industry": "Manufacturing", "in_elec": 0.0, "in_fuel_type": "Diesel", "in_fuel": 0.0,
    "in_transport": 0.0, "in_emp": 1, "in_prod": 0.0,
    "wi_elec": 30, "wi_fuel": 15, "wi_transport": 15, "wi_prod": 0,
    "fc_growth": 2.0, "nz_target": 2050, "nz_growth": 2.0, "nz_residual": 0,
}

LEVER_STATE_KEYS = ("wi_elec", "wi_fuel", "wi_transport", "wi_prod")

RED, ORANGE, BLUE, PURPLE, TEAL, GREY = (
    "#EF5350", "#FFA726", "#42A5F5",
    "#7E57C2", "#26A69A", "#90A4AE"
)


def _reset_levers():
    for key in LEVER_STATE_KEYS:
        st.session_state[key] = WIDGET_DEFAULTS[key]


# --------------------------------------------------------------------------- welcome
def render_welcome(on_sample):
    callout(
        "Enter your monthly activity data in the sidebar and press Calculate Emissions, "
        "or run the sample analysis to explore every feature in one click.",
        "info",
    )

    st.button(
        "🚀 Run sample analysis",
        type="primary",
        on_click=on_sample,
        key="welcome_sample",
        **stretch_kwargs(st.button),
    )

    c1, c2, c3 = st.columns(3)

    c1.markdown(
        "### 🧮 Carbon accounting\n"
        "- Scope 1, 2 and 3 totals\n"
        "- Hotspot ranking\n"
        "- Carbon intensity"
    )

    c2.markdown(
        "### 🤖 ML + simulation\n"
        "- Gradient Boosting prediction\n"
        "- 12-month projection\n"
        "- What-if decarbonization"
    )

    c3.markdown(
        "### 🎯 Net-zero planning\n"
        "- Pathway to 2030 / 2040 / 2050\n"
        "- Net-zero gap\n"
        "- Smart recommendations"
    )


# --------------------------------------------------------------------------- dashboard
def render_dashboard(ctx):
    a = ctx["analysis"]

    em = a["emissions"]
    bd = a["breakdown"]
    sources = a["sources"]
    intensity = a["intensity"]

    total = em["total_kg"]

    for warning in a["warnings"]:
        callout(warning, "warn")

    section(
        "Key indicators",
        "Monthly emissions from your inputs, shown in tCO2e",
    )

    kpi_row([
        {
            "label": "Total emissions",
            "value": f"{fmt_t(total)} tCO2e",
            "sub": f"per month | {fmt_t(total * 12, 1)} t/year annualised",
        },
        {
            "label": "Scope 1 - direct fuel",
            "value": f"{fmt_t(em['scope1_kg'])} tCO2e",
            "sub": f"{bd['scope1_pct']:.1f}% of total",
            "accent": RED,
        },
        {
            "label": "Scope 2 - electricity",
            "value": f"{fmt_t(em['scope2_kg'])} tCO2e",
            "sub": f"{bd['scope2_pct']:.1f}% of total",
            "accent": ORANGE,
        },
        {
            "label": "Scope 3 - indirect",
            "value": f"{fmt_t(em['scope3_kg'])} tCO2e",
            "sub": f"{bd['scope3_pct']:.1f}% of total",
            "accent": BLUE,
        },
    ])

    ml = a.get("ml_prediction_kg")

    if ml is not None:
        diff = safe_div(
            ml - total,
            total,
        ) * 100 if total > 0 else 0.0

        ml_card = {
            "label": "ML predicted emissions",
            "value": f"{fmt_t(ml)} tCO2e",
            "sub": f"{diff:+.1f}% vs rule-based | per month",
            "accent": PURPLE,
        }
    else:
        ml_card = {
            "label": "ML predicted emissions",
            "value": "Unavailable",
            "sub": "Model not loaded; rule-based results still valid",
            "accent": GREY,
        }

    top = (
        sources[0]
        if sources and sources[0]["kg"] > 0
        else None
    )

    per_emp = intensity["per_employee_kg"]
    per_unit = intensity["per_unit_kg"]

    kpi_row([
        ml_card,
        {
            "label": "Top emission source",
            "value": top["source"] if top else "-",
            "sub": f"{top['pct']:.1f}% of total" if top else "No emissions",
            "accent": TEAL,
        },
        {
            "label": "Intensity per employee",
            "value": f"{per_emp:,.1f} kg" if per_emp is not None else "n/a",
            "sub": "CO2e / employee / month",
            "accent": GREY,
        },
        {
            "label": "Intensity per production unit",
            "value": f"{per_unit:,.2f} kg" if per_unit is not None else "n/a",
            "sub": (
                "CO2e / unit"
                if per_unit is not None
                else "Enter production volume"
            ),
            "accent": GREY,
        },
    ])

    left, right = st.columns(2)

    with left:
        show_chart(
            charts.scope_donut(em),
            key="dash_donut",
        )

    with right:
        show_chart(
            charts.sources_bar(sources),
            key="dash_sources",
        )

    section("Insights")

    for text in build_insights(
        sources,
        em,
        bd,
        intensity,
        ml,
    ):
        st.markdown(f"- {text}")


# --------------------------------------------------------------------------- accounting
def render_accounting(ctx):
    a = ctx["analysis"]
    em = a["emissions"]

    section(
        "Carbon accounting",
        "Activity data x emission factor = emissions (monthly, kg CO2)",
    )

    table = pd.DataFrame(
        accounting_table(
            a["input_data"],
            ctx["calc"],
        )
    )

    table["Emissions (t)"] = (
        table["Emissions (kg)"] / 1000
    )

    st.dataframe(
        table,
        hide_index=True,
    )

    kpi_row([
        {
            "label": "Scope 1",
            "value": f"{em['scope1_kg']:,.0f} kg",
            "sub": f"{fmt_t(em['scope1_kg'])} t",
            "accent": RED,
        },
        {
            "label": "Scope 2",
            "value": f"{em['scope2_kg']:,.0f} kg",
            "sub": f"{fmt_t(em['scope2_kg'])} t",
            "accent": ORANGE,
        },
        {
            "label": "Scope 3",
            "value": f"{em['scope3_kg']:,.0f} kg",
            "sub": f"{fmt_t(em['scope3_kg'])} t",
            "accent": BLUE,
        },
        {
            "label": "Total",
            "value": f"{em['total_kg']:,.0f} kg",
            "sub": f"{em['total_tons']:.3f} t",
        },
    ])

    reconciled = (
        abs(
            table["Emissions (kg)"].sum()
            - em["total_kg"]
        ) < 1e-6
    )

    if reconciled:
        callout(
            "Reconciliation check passed: the table adds up exactly to the calculator total.",
            "good",
        )
    else:
        callout(
            "Reconciliation difference detected between the table and the calculator total.",
            "bad",
        )


# --------------------------------------------------------------------------- hotspots
def render_hotspots(ctx):
    sources = ctx["analysis"]["sources"]

    section(
        "Carbon hotspot analysis",
        "Where your emissions come from, ranked",
    )

    callout(
        hotspot_insight(sources),
        "good",
    )

    top3 = top_hotspots(
        sources,
        3,
    )

    accents = [
        RED,
        ORANGE,
        "#FBC02D",
    ]

    kpi_row([
        {
            "label": f"#{row['rank']} hotspot - {row['scope']}",
            "value": row["source"],
            "sub": (
                f"{row['tons']:,.2f} tCO2e/month | "
                f"{row['pct']:.1f}%"
            ),
            "accent": accents[i],
        }
        for i, row in enumerate(top3)
    ])

    show_chart(
        charts.sources_bar(
            sources,
            "Ranked Emission Sources (tCO2e / month)",
            400,
        ),
        key="hot_bar",
    )

    table = pd.DataFrame([
        {
            "Rank": r["rank"],
            "Source": r["source"],
            "Scope": r["scope"],
            "Emissions (kg/month)": round(
                r["kg"],
                2,
            ),
            "Emissions (tCO2e/month)": round(
                r["tons"],
                3,
            ),
            "Contribution (%)": round(
                r["pct"],
                2,
            ),
        }
        for r in sources
    ])

    st.dataframe(
        table,
        hide_index=True,
    )


# --------------------------------------------------------------------------- AI forecast
def render_forecast(ctx):
    a = ctx["analysis"]

    ml_rows = ctx["ml_forecast"]
    rule_rows = ctx["rule_forecast"]

    section(
        "AI emissions forecast",
        "ML-based emissions prediction using the existing Gradient Boosting model",
    )

    st.slider(
        "Expected monthly growth rate (%)",
        -5.0,
        10.0,
        step=0.5,
        key="fc_growth",
        help=(
            "Expected monthly growth/decline in business activity "
            "applied to the projection."
        ),
    )

    if (
        a.get("ml_prediction_kg") is None
        or ml_rows is None
    ):
        callout(
            ctx.get("ml_error")
            or ctx.get("ml_forecast_error")
            or "ML model unavailable.",
            "warn",
        )

        callout(
            "Showing the rule-based projection only. Run the app from "
            "the repository root so models/carbon_predictor.joblib and "
            "models/preprocessor.joblib can be found.",
            "info",
        )

    for warning in a["warnings"]:
        if "ML model" in warning:
            callout(
                warning,
                "warn",
            )

    for note in ctx.get("ml_notes", []):
        callout(
            f"Model loading note: {note}",
            "warn",
        )

    rule_total = sum(
        r["predicted_emissions_kg"]
        for r in rule_rows
    )

    cards = []

    if ml_rows:
        ml_total = sum(
            r["predicted_emissions_kg"]
            for r in ml_rows
        )

        cards += [
            {
                "label": "Current ML prediction",
                "value": f"{fmt_t(a['ml_prediction_kg'])} tCO2e",
                "sub": "per month, current inputs",
                "accent": PURPLE,
            },
            {
                "label": "Average monthly (12-month)",
                "value": f"{fmt_t(ml_total / len(ml_rows))} tCO2e",
                "sub": "ML projection",
                "accent": PURPLE,
            },
            {
                "label": "12-month total (ML)",
                "value": f"{fmt_t(ml_total, 1)} tCO2e",
                "sub": f"{ml_total:,.0f} kg",
                "accent": PURPLE,
            },
        ]

    cards.append(
        {
            "label": "12-month total (rule-based)",
            "value": f"{fmt_t(rule_total, 1)} tCO2e",
            "sub": (
                f"average {fmt_t(rule_total / len(rule_rows))} t/month"
            ),
            "accent": GREY,
        }
    )

    kpi_row(cards)

    show_chart(
        charts.forecast_line(
            ml_rows,
            rule_rows,
            a.get("ml_prediction_kg"),
        ),
        key="fc_line",
    )

    callout(
        "This is a projection based on your current activity and the "
        "growth assumption above, not a guarantee. Tree-based ML models "
        "do not extrapolate beyond their training range, so the ML line "
        "can flatten at high growth.",
        "info",
    )

    table = pd.DataFrame({
        "Month": [
            r["month"]
            for r in rule_rows
        ],
        "ML projection (tCO2e)": (
            [
                round(
                    r["predicted_emissions_kg"] / 1000,
                    3,
                )
                for r in ml_rows
            ]
            if ml_rows
            else [None] * len(rule_rows)
        ),
        "Rule-based (tCO2e)": [
            round(
                r["predicted_emissions_kg"] / 1000,
                3,
            )
            for r in rule_rows
        ],
    })

    st.dataframe(
        table,
        hide_index=True,
    )


# --------------------------------------------------------------------------- what-if
def render_whatif(ctx):
    a = ctx["analysis"]

    baseline = ctx["scenarios"][0]
    custom = ctx["scenarios"][-1]

    section(
        "What-If decarbonization simulator",
        "Reductions are applied on top of your unchanged baseline",
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.slider(
        "⚡ Renewable electricity / electricity reduction (%)",
        0,
        100,
        key="wi_elec",
        help=(
            "Share of electricity emissions removed through "
            "renewable supply and/or efficiency."
        ),
    )

    c2.slider(
        "⛽ Fuel reduction (%)",
        0,
        50,
        key="wi_fuel",
        help="Reduction in fuel consumption.",
    )

    c3.slider(
        "🚚 Transport reduction (%)",
        0,
        50,
        key="wi_transport",
        help=(
            "Reduction in business transport "
            "distance/emissions."
        ),
    )

    c4.slider(
        "🏭 Production / supply-chain efficiency (%)",
        0,
        30,
        key="wi_prod",
        help=(
            "Applied to production-linked "
            "(supply-chain) emissions."
        ),
    )

    st.button(
        "Reset sliders",
        on_click=_reset_levers,
        key="wi_reset",
    )

    kpi_row([
        {
            "label": "Baseline",
            "value": f"{fmt_t(baseline['emissions_kg'])} tCO2e",
            "sub": (
                f"per month | "
                f"{fmt_t(baseline['emissions_kg'] * 12, 1)} t/year"
            ),
            "accent": GREY,
        },
        {
            "label": "Scenario",
            "value": f"{fmt_t(custom['emissions_kg'])} tCO2e",
            "sub": (
                f"per month | "
                f"{fmt_t(custom['emissions_kg'] * 12, 1)} t/year"
            ),
            "accent": "#1565C0",
        },
        {
            "label": "CO2 avoided",
            "value": f"{fmt_t(custom['reduction_kg'])} tCO2e",
            "sub": (
                f"{fmt_t(custom['reduction_kg'] * 12, 1)} t/year"
            ),
        },
        {
            "label": "Reduction",
            "value": f"{custom['reduction_pct']:.1f}%",
            "sub": "vs baseline",
        },
    ])

    show_chart(
        charts.before_after_bar(
            baseline["sources_kg"],
            custom["sources_kg"],
        ),
        key="wi_bar",
    )

    if (
        custom["ml_kg"] is not None
        and a.get("ml_prediction_kg") is not None
    ):
        callout(
            f"ML model estimate for this scenario: "
            f"{fmt_t(custom['ml_kg'])} tCO2e per month "
            f"(ML baseline {fmt_t(a['ml_prediction_kg'])} t). "
            "The rule-based figures above are the accounting reference.",
            "info",
        )

    if custom["reduction_kg"] <= 0:
        callout(
            "Move the sliders to simulate reductions.",
            "info",
        )


# --------------------------------------------------------------------------- scenarios
def render_scenarios(ctx):
    scenarios = ctx["scenarios"]

    section(
        "Reduction scenarios",
        "Compare Baseline, Moderate, Aggressive and your Custom Scenario",
    )

    # Scenario cards
    columns = st.columns(len(scenarios))

    for column, scenario in zip(columns, scenarios):
        with column:

            name = scenario.get(
                "name",
                "Scenario",
            )

            emissions_kg = scenario.get(
                "emissions_kg",
                0.0,
            )

            reduction_kg = scenario.get(
                "reduction_kg",
                0.0,
            )

            reduction_pct = scenario.get(
                "reduction_pct",
                0.0,
            )

            st.subheader(name)

            st.metric(
                "Emissions",
                f"{emissions_kg / 1000:,.2f} tCO2e/month",
            )

            st.metric(
                "Reduction",
                f"{reduction_pct:.1f}%",
                delta=(
                    f"-{reduction_kg / 1000:,.2f} "
                    "tCO2e/month"
                ),
            )

            actions = scenario.get(
                "actions",
                [],
            )

            if actions:
                st.caption("Key actions")

                for action in actions[:4]:
                    st.write(
                        f"• {action}"
                    )

    # Comparison chart
    show_chart(
        charts.scenario_comparison(scenarios),
        key="scn_bar",
    )

    # Comparison table
    table = pd.DataFrame(
        [
            {
                "Scenario": s["name"],
                "Emissions (tCO2e/month)": round(
                    s["emissions_kg"] / 1000,
                    3,
                ),
                "Reduction (tCO2e/month)": round(
                    s["reduction_kg"] / 1000,
                    3,
                ),
                "Reduction (%)": round(
                    s["reduction_pct"],
                    2,
                ),
                "ML estimate (tCO2e/month)": (
                    None
                    if s["ml_kg"] is None
                    else round(
                        s["ml_kg"] / 1000,
                        3,
                    )
                ),
            }
            for s in scenarios
        ]
    )

    st.dataframe(
        table,
        hide_index=True,
        use_container_width=True,
    )

    # Custom assumptions
    lv = ctx["custom_levers"]

    callout(
        f"Custom Scenario assumptions from the What-If Simulator: "
        f"electricity {lv['electricity']:.0f}%, "
        f"fuel {lv['fuel']:.0f}%, "
        f"transport {lv['transport']:.0f}%, "
        f"production {lv['production']:.0f}%.",
        "info",
    )


# --------------------------------------------------------------------------- net zero
def render_netzero(ctx):
    nz = ctx["nz"]

    s = nz["summary"]
    rows = nz["rows"]

    section(
        "Net-zero planner",
        "A transparent linear pathway from your baseline toward zero",
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.radio(
            "Target year",
            list(TARGET_YEARS),
            horizontal=True,
            key="nz_target",
        )

    with c2:
        st.slider(
            "Expected annual activity growth (%)",
            -5.0,
            10.0,
            step=0.5,
            key="nz_growth",
            help=(
                "Business-as-usual yearly growth used "
                "for the forecast line."
            ),
        )

    with c3:
        st.slider(
            "Residual emissions allowed at target (% of baseline)",
            0,
            10,
            key="nz_residual",
            help=(
                "0% = full zero. Residual emissions would need "
                "to be neutralised separately."
            ),
        )

    gap_open = s["gap_open"]

    kpi_row([
        {
            "label": "Baseline (annualised)",
            "value": f"{s['baseline_kg'] / 1000:,.1f} tCO2e",
            "sub": (
                f"base year {s['base_year']} "
                "(monthly x 12)"
            ),
        },
        {
            "label": "Target year",
            "value": str(s["target_year"]),
            "sub": "net-zero planning target",
            "accent": "#1565C0",
        },
        {
            "label": "Years remaining",
            "value": str(s["years_remaining"]),
            "sub": f"from {s['base_year']}",
            "accent": "#1565C0",
        },
        {
            "label": "Required avg annual reduction",
            "value": (
                f"{s['required_annual_reduction_kg'] / 1000:,.1f} t/year"
            ),
            "sub": (
                f"{s['required_annual_reduction_pct']:.1f}% "
                "of baseline per year"
            ),
            "accent": TEAL,
        },
    ])

    kpi_row([
        {
            "label": (
                f"Forecast emissions in "
                f"{s['target_year']}"
            ),
            "value": (
                f"{s['forecast_at_target_kg'] / 1000:,.1f} tCO2e"
            ),
            "sub": (
                f"business as usual, growth "
                f"{ctx['nz']['settings']['growth']:+.1f}%/year"
            ),
            "accent": RED,
        },
        {
            "label": "Pathway target",
            "value": (
                f"{s['pathway_at_target_kg'] / 1000:,.1f} tCO2e"
            ),
            "sub": "on the net-zero pathway",
            "accent": "#2E7D32",
        },
        {
            "label": "Net-zero gap",
            "value": (
                f"{max(s['gap_kg'], 0) / 1000:,.1f} tCO2e"
            ),
            "sub": (
                "per year at target"
                if gap_open
                else "no gap: forecast is at/below pathway"
            ),
            "accent": (
                "#C62828"
                if gap_open
                else "#2E7D32"
            ),
        },
        {
            "label": "Reduction needed to close gap",
            "value": (
                f"{s['reduction_needed_pct_of_forecast']:.1f}%"
            ),
            "sub": "of forecast emissions in target year",
            "accent": (
                "#C62828"
                if gap_open
                else "#2E7D32"
            ),
        },
    ])

    show_chart(
        charts.net_zero_chart(
            rows,
            s["target_year"],
        ),
        key="nz_chart",
    )

    custom = ctx["scenarios"][-1]

    if s["baseline_kg"] <= 0:
        callout(
            "Baseline emissions are zero, so there is nothing to plan against yet.",
            "info",
        )

    elif s["scenario_gap_kg"] > 0:
        callout(
            f"Applying your Custom Scenario "
            f"({custom['reduction_pct']:.1f}% reduction) "
            f"would still leave a gap of "
            f"{s['scenario_gap_kg'] / 1000:,.1f} tCO2e per year "
            f"in {s['target_year']}. Deeper or repeated reductions are needed.",
            "warn",
        )

    else:
        callout(
            f"Your Custom Scenario "
            f"({custom['reduction_pct']:.1f}% reduction) "
            f"would bring {s['target_year']} emissions to or below "
            "the pathway in this simulation.",
            "good",
        )

    callout(
        "Planning simulation only. It does not claim that the "
        "organisation is net-zero. Residual emissions, offsets and "
        "verified targets (e.g. SBTi) are outside this tool.",
        "info",
    )

    with st.expander("Year-by-year table"):
        table = pd.DataFrame([
            {
                "Year": r["year"],
                "Forecast (tCO2e)": round(
                    r["forecast_kg"] / 1000,
                    2,
                ),
                "Pathway (tCO2e)": round(
                    r["pathway_kg"] / 1000,
                    2,
                ),
                "Gap (tCO2e)": round(
                    r["gap_kg"] / 1000,
                    2,
                ),
                "With Custom Scenario (tCO2e)": round(
                    r["scenario_kg"] / 1000,
                    2,
                ),
            }
            for r in rows
        ])

        st.dataframe(
            table,
            hide_index=True,
        )


# --------------------------------------------------------------------------- recommendations
def render_recommendations(ctx):
    recs = ctx["recs"]

    section(
        "Smart recommendations",
        "Generated from your emissions using the existing rule engine",
    )

    # Recommendation cards
    for index, rec in enumerate(recs, 1):

        title = rec.get(
            "title",
            rec.get(
                "action",
                rec.get(
                    "name",
                    "Recommended Action",
                ),
            ),
        )

        priority = rec.get(
            "priority",
            "",
        )

        category = rec.get(
            "category",
            "",
        )

        timeframe = rec.get(
            "timeframe",
            "",
        )

        why = rec.get(
            "why",
            rec.get(
                "description",
                "",
            ),
        )

        estimate = rec.get(
            "estimate_text",
            rec.get(
                "estimated_reduction",
                "",
            ),
        )

        lever = rec.get(
            "lever_text",
            rec.get(
                "lever",
                "",
            ),
        )

        with st.container(border=True):

            st.subheader(
                f"{index}. {title}"
            )

            info_columns = st.columns(4)

            with info_columns[0]:
                if priority:
                    st.write(
                        f"**Priority**\n\n{priority}"
                    )

            with info_columns[1]:
                if category:
                    st.write(
                        f"**Category**\n\n{category}"
                    )

            with info_columns[2]:
                if timeframe:
                    st.write(
                        f"**Timeframe**\n\n{timeframe}"
                    )

            with info_columns[3]:
                investment = rec.get(
                    "investment",
                    "",
                )

                if investment:
                    st.write(
                        f"**Investment**\n\n{investment}"
                    )

            if why:
                st.write(
                    f"**Why:** {why}"
                )

            if estimate:
                st.write(
                    f"**Estimated impact:** {estimate}"
                )

            if lever:
                st.write(
                    f"**Reduction lever:** {lever}"
                )

    callout(
        "Estimates may overlap because multiple actions can affect "
        "the same emissions. They are indicative planning ranges, "
        "not financial savings.",
        "info",
    )


# --------------------------------------------------------------------------- report
def render_report(ctx):
    section(
        "Report",
        "Download your analysis",
    )

    report = build_report_df(ctx)
    legacy = build_legacy_summary_df(
        ctx["analysis"]
    )

    c1, c2 = st.columns(2)

    with c1:
        st.download_button(
            "📄 Download full report (CSV)",
            data=report.to_csv(index=False),
            file_name="carbonwise_full_report.csv",
            mime="text/csv",
            key="dl_full",
            **stretch_kwargs(st.download_button),
        )

    with c2:
        st.download_button(
            "📄 Download summary (CSV, original format)",
            data=legacy.to_csv(index=False),
            file_name="carbonwise_emissions_report.csv",
            mime="text/csv",
            key="dl_legacy",
            **stretch_kwargs(st.download_button),
        )

    st.caption(DISCLAIMER)

    with st.expander(
        "Preview full report",
        expanded=True,
    ):
        st.dataframe(
            report,
            hide_index=True,
        )


# --------------------------------------------------------------------------- methodology
def render_methodology(calc):
    section(
        "Methodology & limitations"
    )

    with st.expander(
        "Emission factors and Scope 1/2/3 formulas",
        expanded=True,
    ):
        factors = pd.DataFrame([
            {
                "Factor": "Electricity",
                "Value": calc.EMISSION_FACTORS["electricity"],
                "Unit": "kg CO2 / kWh",
            },
            {
                "Factor": "Diesel",
                "Value": calc.EMISSION_FACTORS["Diesel"],
                "Unit": "kg CO2 / liter",
            },
            {
                "Factor": "Petrol",
                "Value": calc.EMISSION_FACTORS["Petrol"],
                "Unit": "kg CO2 / liter",
            },
            {
                "Factor": "Natural Gas",
                "Value": calc.EMISSION_FACTORS["Natural Gas"],
                "Unit": "kg CO2 / liter-or-unit (as in original)",
            },
            {
                "Factor": "Coal",
                "Value": calc.EMISSION_FACTORS["Coal"],
                "Unit": "kg CO2 / liter-or-unit (as in original)",
            },
            {
                "Factor": "LPG",
                "Value": calc.EMISSION_FACTORS["LPG"],
                "Unit": "kg CO2 / liter-or-unit (as in original)",
            },
            {
                "Factor": "Transport",
                "Value": calc.EMISSION_FACTORS["transport"],
                "Unit": "kg CO2 / km",
            },
            {
                "Factor": "Employee commute",
                "Value": calc.EMISSION_FACTORS["employee_commute"],
                "Unit": "kg CO2 / employee-km",
            },
            {
                "Factor": "Supply chain",
                "Value": calc.EMISSION_FACTORS["supply_chain"],
                "Unit": "kg CO2 / production unit",
            },
        ])

        st.dataframe(
            factors,
            hide_index=True,
        )

        st.markdown(
            "- **Scope 1** = fuel quantity x fuel emission factor\n"
            "- **Scope 2** = electricity (kWh) x 0.82\n"
            "- **Scope 3** = transport km x 0.21 + employees x 22 days x 10 km x 2 trips x 0.12 + production units x 0.15\n"
            "- **Total** = Scope 1 + Scope 2 + Scope 3 (monthly, kg CO2; shown in tCO2e)\n"
            "- Factors are the original project values. They are CO2-based and shown as CO2e for presentation, "
            "and the grid factor is region-specific."
        )

    with st.expander("Assumptions"):
        st.markdown(
            "- All activity inputs are **monthly**; annual values are monthly x 12.\n"
            "- Transport is counted under Scope 3, including any owned-fleet travel.\n"
            "- Natural gas, coal and LPG use the original per-liter/unit factors.\n"
            "- Commute is fixed at 22 days x 10 km x 2 trips per employee per month.\n"
            "- What-If levers scale the activity inputs; production efficiency scales production-linked emissions."
        )

    with st.expander(
        "ML model role and forecast assumptions"
    ):
        st.markdown(
            "- The existing **Gradient Boosting** model (`models/carbon_predictor.joblib`) with its "
            "preprocessor is loaded unchanged; it is not retrained here.\n"
            "- It predicts monthly total emissions from industry, fuel type and activity inputs.\n"
            "- The 12-month forecast multiplies electricity, fuel, transport and production by "
            "(1 + monthly growth)^month; employees are held constant.\n"
            "- The Net-Zero planner uses a separate **annual** growth assumption with the rule-based baseline."
        )

    with st.expander(
        "Limitations",
        expanded=True,
    ):
        st.markdown(
            "- The ML model was trained on **synthetic data generated from the same rule-based formula**, so it "
            "mirrors the calculator rather than real-world measurements.\n"
            "- Tree models cannot extrapolate beyond training ranges, so predictions are less reliable for "
            "very small or very large inputs.\n"
            "- Industry does not change the calculation.\n"
            "- Results are **estimates for planning**, not verified corporate GHG inventories. "
            "Consult certified carbon accountants for official reporting.\n"
            "- Recommendation impacts are conservative indicative ranges, not guaranteed or financial savings."
        )