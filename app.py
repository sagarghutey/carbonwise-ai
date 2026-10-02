
"""CarbonWise AI v2 - ML-Powered Carbon Intelligence & Net-Zero Planning Platform.
Streamlit entry point. Heavy logic lives in src/ (emissions, predict,
recommendations are the ORIGINAL modules; the rest are v2 additions).
Run from the repository root:  streamlit run app.py
"""

import sys
import warnings
from datetime import datetime
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="CarbonWise AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)


ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


MODEL_PATH = ROOT / "models" / "carbon_predictor.joblib"
PREPROCESSOR_PATH = ROOT / "models" / "preprocessor.joblib"


from emissions import EmissionsCalculator  # noqa: E402
from hotspots import carbon_intensity, ranked_hotspots  # noqa: E402
from net_zero import build_projection, current_year, summarize_pathway  # noqa: E402
from predict import EmissionsPredictor  # noqa: E402

from scenarios import (  # noqa: E402
    build_scenarios,
    rule_based_forecast,
    safe_ml_forecast,
    safe_ml_predict,
)

from smart_recommendations import build_smart_recommendations  # noqa: E402
from ui_helpers import hero, inject_css, stretch_kwargs  # noqa: E402
from validation import FUEL_TYPES, INDUSTRIES, validate_inputs  # noqa: E402

import views  # noqa: E402


SAMPLE_INPUTS = {
    "in_industry": "Manufacturing",
    "in_elec": 100000.0,
    "in_fuel_type": "Diesel",
    "in_fuel": 5000.0,
    "in_transport": 15000.0,
    "in_emp": 250,
    "in_prod": 20000.0,
}


TAB_NAMES = [
    "📊 Dashboard",
    "🧮 Accounting",
    "🔥 Hotspots",
    "🤖 AI Forecast",
    "🎛️ What-If",
    "⚖️ Scenarios",
    "🎯 Net-Zero",
    "💡 Actions",
    "📥 Report",
    "📚 Methodology",
]


# ---------------------------------------------------------------------------
# model loading
@st.cache_resource(show_spinner=False)
def _load_predictor():
    """Load the EXISTING model files once. Returns (predictor, error, notes)."""

    if (
        not MODEL_PATH.exists()
        or not PREPROCESSOR_PATH.exists()
    ):
        return (
            None,
            (
                "Model files not found in the models/ folder "
                "(expected carbon_predictor.joblib and preprocessor.joblib)."
            ),
            [],
        )

    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            predictor = EmissionsPredictor(
                model_path=str(MODEL_PATH),
                preprocessor_path=str(PREPROCESSOR_PATH),
            )

        notes = sorted({
            str(w.message).split("\n")[0][:220]
            for w in caught
            if "version" in str(w.message).lower()
        })[:3]

        return predictor, None, notes

    except Exception as exc:
        return (
            None,
            f"Could not load the ML model: {exc}",
            [],
        )


def _retry_model_load():
    _load_predictor.clear()


# ---------------------------------------------------------------------------
# state
def init_state():
    for key, value in views.WIDGET_DEFAULTS.items():
        st.session_state.setdefault(
            key,
            value,
        )


def collect_raw():
    ss = st.session_state

    return {
        "industry": ss["in_industry"],
        "electricity_kwh_monthly": ss["in_elec"],
        "fuel_liters_monthly": ss["in_fuel"],
        "fuel_type": ss["in_fuel_type"],
        "transport_km_monthly": ss["in_transport"],
        "num_employees": ss["in_emp"],
        "production_units_monthly": ss["in_prod"],
    }


def load_sample():
    for key, value in SAMPLE_INPUTS.items():
        st.session_state[key] = value


def run_analysis():
    """
    Validate inputs, run the ORIGINAL calculations
    and persist the results.
    """

    ss = st.session_state

    raw = collect_raw()

    clean, errors, warns = validate_inputs(raw)

    ss["calc_errors"] = errors

    if errors:
        return

    calc = EmissionsCalculator()

    emissions = calc.calculate_total_emissions(
        clean
    )

    breakdown = calc.get_breakdown_percentage(
        emissions
    )

    top_contributor = calc.identify_top_contributor(
        emissions
    )

    predictor, ml_error, _notes = _load_predictor()

    ml_prediction, ml_predict_error = safe_ml_predict(
        predictor,
        clean,
    )

    ss["analysis"] = {
        "raw": raw,
        "input_data": clean,
        "emissions": emissions,
        "breakdown": breakdown,
        "top_contributor": top_contributor,
        "sources": ranked_hotspots(
            clean,
            calc,
        ),
        "intensity": carbon_intensity(
            emissions["total_kg"],
            clean["num_employees"],
            clean["production_units_monthly"],
        ),
        "ml_prediction_kg": ml_prediction,
        "ml_error": ml_error or ml_predict_error,
        "warnings": warns,
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        ),
    }


def load_sample_and_run():
    load_sample()
    run_analysis()


# ---------------------------------------------------------------------------
# sidebar
def render_sidebar():
    sb = st.sidebar

    sb.header("Input Parameters")

    sb.button(
        "📝 Load Sample Data",
        on_click=load_sample,
        key="btn_sample",
        **stretch_kwargs(st.button),
    )

    sb.selectbox(
        "Industry Type",
        INDUSTRIES,
        key="in_industry",
    )

    sb.subheader(
        "Monthly Activity Data"
    )

    sb.number_input(
        "Electricity Consumption (kWh)",
        min_value=0.0,
        step=1000.0,
        key="in_elec",
        help=(
            "Total monthly electricity usage "
            "in kilowatt-hours"
        ),
    )

    sb.selectbox(
        "Fuel Type",
        FUEL_TYPES,
        key="in_fuel_type",
    )

    sb.number_input(
        "Fuel Consumption (Liters/Units)",
        min_value=0.0,
        step=100.0,
        key="in_fuel",
        help=(
            "Monthly fuel consumption in liters "
            "or equivalent units"
        ),
    )

    sb.number_input(
        "Transport Distance (km)",
        min_value=0.0,
        step=500.0,
        key="in_transport",
        help=(
            "Total business transport/logistics "
            "distance per month"
        ),
    )

    sb.number_input(
        "Number of Employees",
        min_value=1,
        step=10,
        key="in_emp",
        help=(
            "Total number of employees "
            "(for commute estimation)"
        ),
    )

    sb.number_input(
        "Production Volume (Units)",
        min_value=0.0,
        step=1000.0,
        key="in_prod",
        help=(
            "Monthly production volume or "
            "business output metric"
        ),
    )

    sb.button(
        "🔍 Calculate Emissions",
        type="primary",
        on_click=run_analysis,
        key="btn_calc",
        **stretch_kwargs(st.button),
    )

    analysis = st.session_state.get(
        "analysis"
    )

    if (
        analysis is not None
        and collect_raw() != analysis["raw"]
    ):
        sb.warning(
            "Inputs changed since the last calculation. "
            "Press Calculate Emissions to update."
        )

    elif analysis is not None:
        sb.caption(
            f"Results calculated {analysis['timestamp']}"
        )

    predictor, error, _notes = _load_predictor()

    sb.divider()

    if predictor is not None:
        sb.caption(
            "✅ Existing ML model loaded"
        )

    else:
        sb.caption(
            f"⚠️ ML unavailable: {error}"
        )

        sb.button(
            "Retry loading model",
            on_click=_retry_model_load,
            key="btn_retry",
        )


# ---------------------------------------------------------------------------
# context
def build_context(analysis):
    ss = st.session_state

    calc = EmissionsCalculator()

    predictor, ml_error, ml_notes = _load_predictor()

    input_data = analysis["input_data"]

    custom_levers = {
        "electricity": ss["wi_elec"],
        "fuel": ss["wi_fuel"],
        "transport": ss["wi_transport"],
        "production": ss["wi_prod"],
    }

    scenarios = build_scenarios(
        input_data,
        calc,
        predictor,
        custom_levers,
    )

    custom = scenarios[-1]

    growth = float(
        ss["fc_growth"]
    ) / 100

    ml_forecast, ml_forecast_error = safe_ml_forecast(
        predictor,
        input_data,
        12,
        growth,
    )

    rule_forecast = rule_based_forecast(
        calc,
        input_data,
        12,
        growth,
    )

    base_year = current_year()

    target_year = int(
        ss["nz_target"]
    )

    nz_growth = float(
        ss["nz_growth"]
    )

    nz_residual = float(
        ss["nz_residual"]
    )

    baseline_annual = (
        analysis["emissions"]["total_kg"]
        * 12
    )

    nz_rows = build_projection(
        baseline_annual,
        base_year,
        target_year,
        nz_growth,
        nz_residual,
        custom["reduction_pct"],
    )

    nz_summary = summarize_pathway(
        nz_rows,
        baseline_annual,
        base_year,
        target_year,
        nz_residual,
    )

    sources_kg = {
        row["source"]: row["kg"]
        for row in analysis["sources"]
    }

    recs = build_smart_recommendations(
        input_data,
        analysis["breakdown"],
        sources_kg,
    )

    return {
        "analysis": analysis,
        "calc": calc,
        "predictor": predictor,
        "ml_error": (
            analysis.get("ml_error")
            or ml_error
        ),
        "ml_notes": ml_notes,
        "scenarios": scenarios,
        "custom_levers": custom["levers"],
        "forecast_growth": growth,
        "ml_forecast": ml_forecast,
        "ml_forecast_error": ml_forecast_error,
        "rule_forecast": rule_forecast,
        "nz": {
            "rows": nz_rows,
            "summary": nz_summary,
            "settings": {
                "growth": nz_growth,
                "residual": nz_residual,
                "target_year": target_year,
            },
        },
        "recs": recs,
    }


# ---------------------------------------------------------------------------
# main
def main():
    init_state()

    inject_css()

    hero(
        "🌍 CarbonWise AI",
        "ML-Powered Carbon Intelligence & Net-Zero Planning Platform",
    )

    render_sidebar()

    for message in st.session_state.get(
        "calc_errors",
        [],
    ):
        st.error(message)

    analysis = st.session_state.get(
        "analysis"
    )

    if analysis is None:
        views.render_welcome(
            load_sample_and_run
        )

        views.render_methodology(
            EmissionsCalculator()
        )

    else:
        ctx = build_context(
            analysis
        )

        tabs = st.tabs(
            TAB_NAMES
        )

        renderers = [
            views.render_dashboard,
            views.render_accounting,
            views.render_hotspots,
            views.render_forecast,
            views.render_whatif,
            views.render_scenarios,
            views.render_netzero,
            views.render_recommendations,
            views.render_report,
        ]

        for tab, render in zip(
            tabs,
            renderers,
        ):
            with tab:
                render(ctx)

        with tabs[-1]:
            views.render_methodology(
                ctx["calc"]
            )

    st.markdown(
        '<div class="cw-foot">'
        'CarbonWise AI v2 | Greenovators Hackathon | '
        'Built with Python, Streamlit, scikit-learn | '
        'Estimates for planning only, not verified GHG inventories'
        '</div>',
        unsafe_allow_html=True,
    )


main()