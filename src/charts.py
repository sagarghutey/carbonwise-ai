import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# Common styling
# ============================================================

def _style(fig, height=None):
    if height is not None:
        fig.update_layout(height=height)

    fig.update_layout(
        margin=dict(
            l=30,
            r=30,
            t=70,
            b=55,
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(
            family="Arial",
            size=13,
        ),
    )

    return fig


# ============================================================
# Scope donut
# ============================================================

def scope_donut(emissions, height=420):
    """
    Clean Scope 1 / Scope 2 / Scope 3 donut chart.

    Only Scope 1, Scope 2 and Scope 3 are displayed.
    total_kg and total_tons are NOT chart slices.
    """

    if not isinstance(emissions, dict):
        emissions = {}

    scope1 = float(
        emissions.get(
            "scope1_kg",
            0.0,
        )
    )

    scope2 = float(
        emissions.get(
            "scope2_kg",
            0.0,
        )
    )

    scope3 = float(
        emissions.get(
            "scope3_kg",
            0.0,
        )
    )

    labels = [
        "Scope 1",
        "Scope 2",
        "Scope 3",
    ]

    values = [
        scope1,
        scope2,
        scope3,
    ]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.50,
                textinfo="label+percent",
                textposition="inside",
                insidetextorientation="horizontal",
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Emissions: %{value:,.0f} kg CO2e"
                    "<extra></extra>"
                ),
            )
        ]
    )

    fig.update_layout(
        title={
            "text": "Emissions by Scope",
            "x": 0.02,
            "xanchor": "left",
            "y": 0.98,
            "yanchor": "top",
            "font": {
                "size": 20,
                "family": "Arial",
            },
        },
        height=height,
        margin=dict(
            l=20,
            r=20,
            t=95,
            b=80,
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(
            family="Arial",
            size=13,
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.03,
            xanchor="center",
            x=0.5,
            title=None,
            font=dict(
                size=12,
            ),
        ),
    )

    return fig


# ============================================================
# Sources bar chart
# ============================================================

def sources_bar(
    sources,
    title="Emission Sources",
    height=400,
):
    """
    Ranked emission-source bar chart.

    Compatible with:
        sources_bar(sources, title, height)
    """

    rows = []

    if sources is None:
        sources = []

    # --------------------------------------------------------
    # Hotspot list
    # --------------------------------------------------------

    if isinstance(
        sources,
        list,
    ):

        for row in sources:

            if not isinstance(
                row,
                dict,
            ):
                continue

            source = row.get(
                "source",
                "Unknown",
            )

            value = row.get(
                "kg",
                row.get(
                    "emissions_kg",
                    row.get(
                        "value",
                        0.0,
                    ),
                ),
            )

            try:
                value = float(value)
            except (
                TypeError,
                ValueError,
            ):
                value = 0.0

            rows.append(
                {
                    "Source": str(source),
                    "Emissions": value,
                }
            )

    # --------------------------------------------------------
    # Dictionary source -> emissions
    # --------------------------------------------------------

    elif isinstance(
        sources,
        dict,
    ):

        for source, value in sources.items():

            try:
                value = float(value)
            except (
                TypeError,
                ValueError,
            ):
                continue

            rows.append(
                {
                    "Source": str(source),
                    "Emissions": value,
                }
            )

    if not rows:
        rows = [
            {
                "Source": "No data",
                "Emissions": 0.0,
            }
        ]

    df = pd.DataFrame(
        rows
    )

    df = df.sort_values(
        "Emissions",
        ascending=True,
    )

    fig = px.bar(
        df,
        x="Emissions",
        y="Source",
        orientation="h",
        title=title,
        labels={
            "Emissions": "Emissions (kg CO2e)",
            "Source": "Source",
        },
        text="Emissions",
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        title={
            "x": 0.02,
            "xanchor": "left",
            "font": {
                "size": 20,
            },
        },
        margin=dict(
            l=120,
            r=80,
            t=75,
            b=60,
        ),
    )

    return _style(
        fig,
        height,
    )


# ============================================================
# Forecast line chart
# ============================================================

def forecast_line(
    ml_rows,
    rule_rows,
    current_ml=None,
    height=430,
):
    """
    Compare ML and rule-based forecasts.
    """

    records = []

    # --------------------------------------------------------
    # ML forecast
    # --------------------------------------------------------

    if ml_rows:

        for index, row in enumerate(
            ml_rows,
            start=1,
        ):

            if isinstance(
                row,
                dict,
            ):

                month = row.get(
                    "month",
                    index,
                )

                value = row.get(
                    "predicted_emissions_kg",
                    row.get(
                        "prediction_kg",
                        row.get(
                            "predicted_kg",
                            row.get(
                                "emissions_kg",
                                0.0,
                            ),
                        ),
                    ),
                )

            else:

                month = index
                value = row

            try:
                value = float(value)
            except (
                TypeError,
                ValueError,
            ):
                value = 0.0

            records.append(
                {
                    "Month": month,
                    "Emissions (kg)": value,
                    "Method": "ML Forecast",
                }
            )

    # --------------------------------------------------------
    # Rule forecast
    # --------------------------------------------------------

    if rule_rows:

        for index, row in enumerate(
            rule_rows,
            start=1,
        ):

            if isinstance(
                row,
                dict,
            ):

                month = row.get(
                    "month",
                    index,
                )

                value = row.get(
                    "predicted_emissions_kg",
                    row.get(
                        "prediction_kg",
                        row.get(
                            "predicted_kg",
                            row.get(
                                "emissions_kg",
                                0.0,
                            ),
                        ),
                    ),
                )

            else:

                month = index
                value = row

            try:
                value = float(value)
            except (
                TypeError,
                ValueError,
            ):
                value = 0.0

            records.append(
                {
                    "Month": month,
                    "Emissions (kg)": value,
                    "Method": "Rule-Based Forecast",
                }
            )

    if not records:
        records = [
            {
                "Month": 1,
                "Emissions (kg)": 0.0,
                "Method": "No forecast",
            }
        ]

    df = pd.DataFrame(
        records
    )

    fig = px.line(
        df,
        x="Month",
        y="Emissions (kg)",
        color="Method",
        markers=True,
        title="12-Month Emissions Forecast",
    )

    fig.update_layout(
        title={
            "x": 0.02,
            "xanchor": "left",
            "font": {
                "size": 20,
            },
        },
        margin=dict(
            l=70,
            r=40,
            t=75,
            b=60,
        ),
    )

    fig.update_xaxes(
        title="Month",
    )

    fig.update_yaxes(
        title="Emissions (kg CO2e)",
    )

    return _style(
        fig,
        height,
    )


# ============================================================
# Before vs Custom
# ============================================================

def before_after_bar(
    baseline_sources,
    custom_sources,
    height=420,
):
    """
    Compare baseline and custom scenario emissions.
    """

    if not isinstance(
        baseline_sources,
        dict,
    ):
        baseline_sources = {}

    if not isinstance(
        custom_sources,
        dict,
    ):
        custom_sources = {}

    source_names = sorted(
        set(
            baseline_sources.keys()
        )
        |
        set(
            custom_sources.keys()
        )
    )

    rows = []

    for source in source_names:

        try:
            baseline_value = float(
                baseline_sources.get(
                    source,
                    0.0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            baseline_value = 0.0

        try:
            custom_value = float(
                custom_sources.get(
                    source,
                    0.0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            custom_value = 0.0

        rows.append(
            {
                "Source": source,
                "Emissions (kg)": baseline_value,
                "Scenario": "Baseline",
            }
        )

        rows.append(
            {
                "Source": source,
                "Emissions (kg)": custom_value,
                "Scenario": "Custom",
            }
        )

    if not rows:
        rows = [
            {
                "Source": "No data",
                "Emissions (kg)": 0.0,
                "Scenario": "Baseline",
            },
            {
                "Source": "No data",
                "Emissions (kg)": 0.0,
                "Scenario": "Custom",
            },
        ]

    df = pd.DataFrame(
        rows
    )

    fig = px.bar(
        df,
        x="Source",
        y="Emissions (kg)",
        color="Scenario",
        barmode="group",
        title="Before vs Custom Scenario",
        text="Emissions (kg)",
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        title={
            "x": 0.02,
            "xanchor": "left",
            "font": {
                "size": 20,
            },
        },
        margin=dict(
            l=60,
            r=60,
            t=75,
            b=90,
        ),
    )

    return _style(
        fig,
        height,
    )


# ============================================================
# Scenario comparison
# ============================================================

def scenario_comparison(
    scenarios,
    height=430,
):
    """
    Compare Baseline, Moderate, Aggressive and Custom.
    """

    rows = []

    if scenarios is None:
        scenarios = []

    for scenario in scenarios:

        if not isinstance(
            scenario,
            dict,
        ):
            continue

        name = scenario.get(
            "name",
            "Scenario",
        )

        value = scenario.get(
            "emissions_kg",
            scenario.get(
                "scenario_kg",
                0.0,
            ),
        )

        try:
            value = float(value)
        except (
            TypeError,
            ValueError,
        ):
            value = 0.0

        rows.append(
            {
                "Scenario": name,
                "Emissions (kg)": value,
            }
        )

    if not rows:
        rows = [
            {
                "Scenario": "No data",
                "Emissions (kg)": 0.0,
            }
        ]

    df = pd.DataFrame(
        rows
    )

    fig = px.bar(
        df,
        x="Scenario",
        y="Emissions (kg)",
        title="Scenario Comparison",
        text="Emissions (kg)",
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        title={
            "x": 0.02,
            "xanchor": "left",
            "font": {
                "size": 20,
            },
        },
        margin=dict(
            l=60,
            r=60,
            t=75,
            b=70,
        ),
    )

    return _style(
        fig,
        height,
    )


# ============================================================
# Net-zero chart
# ============================================================

def net_zero_chart(
    rows,
    target_year=None,
    height=430,
):
    """
    Display net-zero pathway and business-as-usual forecast.
    """

    records = []

    if rows is None:
        rows = []

    for index, row in enumerate(
        rows
    ):

        if not isinstance(
            row,
            dict,
        ):
            continue

        year = row.get(
            "year",
            index,
        )

        pathway = row.get(
            "pathway_kg",
            row.get(
                "pathway",
                row.get(
                    "target_kg",
                    row.get(
                        "emissions_kg",
                        0.0,
                    ),
                ),
            ),
        )

        forecast = row.get(
            "forecast_kg",
            row.get(
                "forecast",
                row.get(
                    "business_as_usual_kg",
                    None,
                ),
            ),
        )

        try:
            pathway = float(
                pathway
            )
        except (
            TypeError,
            ValueError,
        ):
            pathway = 0.0

        record = {
            "Year": year,
            "Pathway (kg)": pathway,
        }

        if forecast is not None:

            try:
                record[
                    "Business as Usual (kg)"
                ] = float(
                    forecast
                )
            except (
                TypeError,
                ValueError,
            ):
                pass

        records.append(
            record
        )

    if not records:
        records = [
            {
                "Year": 0,
                "Pathway (kg)": 0.0,
            }
        ]

    df = pd.DataFrame(
        records
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Year"],
            y=df["Pathway (kg)"],
            mode="lines+markers",
            name="Net-Zero Pathway",
        )
    )

    if "Business as Usual (kg)" in df.columns:

        fig.add_trace(
            go.Scatter(
                x=df["Year"],
                y=df[
                    "Business as Usual (kg)"
                ],
                mode="lines+markers",
                name="Business as Usual",
            )
        )

    title = "Net-Zero Pathway"

    if target_year is not None:
        title += (
            f" — Target {target_year}"
        )

    fig.update_layout(
        title={
            "text": title,
            "x": 0.02,
            "xanchor": "left",
            "font": {
                "size": 20,
            },
        },
        xaxis_title="Year",
        yaxis_title="Annual Emissions (kg CO2e)",
        margin=dict(
            l=70,
            r=40,
            t=75,
            b=60,
        ),
    )

    return _style(
        fig,
        height,
    )


# ============================================================
# Empty chart
# ============================================================

def show_empty_chart(
    title="No data available",
    height=300,
):
    fig = go.Figure()

    fig.update_layout(
        title=title,
        height=height,
        xaxis=dict(
            visible=False,
        ),
        yaxis=dict(
            visible=False,
        ),
    )

    return _style(
        fig,
        height,
    )


# ============================================================
# Exports
# ============================================================

__all__ = [
    "scope_donut",
    "sources_bar",
    "forecast_line",
    "before_after_bar",
    "scenario_comparison",
    "net_zero_chart",
    "show_empty_chart",
]