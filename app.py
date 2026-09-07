import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys

# Add src to path
sys.path.append('src')

from emissions import EmissionsCalculator
from predict import EmissionsPredictor
from recommendations import RecommendationEngine

# Page configuration
st.set_page_config(
    page_title="CarbonWise AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #2E7D32;
        text-align: center;
        font-weight: bold;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #2E7D32;
    }
    .scope-card {
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .scope1 { border-left: 5px solid #EF5350; }
    .scope2 { border-left: 5px solid #FFA726; }
    .scope3 { border-left: 5px solid #42A5F5; }
    .recommendation-card {
        background-color: #E8F5E9;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 5px solid #4CAF50;
    }
    .high-priority { border-left-color: #D32F2F; }
    .medium-priority { border-left-color: #F57C00; }
    .low-priority { border-left-color: #FDD835; }
    </style>
""", unsafe_allow_html=True)


def load_models():
    """Load ML model and preprocessor."""
    try:
        predictor = EmissionsPredictor(
            model_path='models/carbon_predictor.joblib',
            preprocessor_path='models/preprocessor.joblib'
        )
        return predictor
    except FileNotFoundError:
        st.error("⚠️ Model files not found. Please run `python src/train_model.py` first.")
        return None


def create_emissions_chart(emissions):
    """Create pie chart for emissions breakdown."""
    labels = ['Scope 1<br>(Direct Fuel)', 'Scope 2<br>(Electricity)', 'Scope 3<br>(Indirect)']
    values = [emissions['scope1_kg'], emissions['scope2_kg'], emissions['scope3_kg']]
    colors = ['#EF5350', '#FFA726', '#42A5F5']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=colors),
        textinfo='label+percent',
        textfont_size=14
    )])
    
    fig.update_layout(
        title="Emissions Breakdown by Scope",
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    return fig


def create_scenario_chart(scenarios):
    """Create bar chart comparing reduction scenarios."""
    scenario_names = list(scenarios.keys())
    emissions = [scenarios[name]['predicted_emissions_kg'] for name in scenario_names]
    reductions = [scenarios[name]['reduction_pct'] for name in scenario_names]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Emissions',
        x=scenario_names,
        y=emissions,
        marker_color='#42A5F5',
        text=[f"{e:,.0f} kg" for e in emissions],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Carbon Reduction Scenarios Comparison",
        xaxis_title="Scenario",
        yaxis_title="Emissions (kg CO2)",
        height=400,
        showlegend=False
    )
    
    return fig


def create_future_predictions_chart(predictions):
    """Create line chart for future emissions predictions."""
    df = pd.DataFrame(predictions)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['month'],
        y=df['predicted_emissions_kg'],
        mode='lines+markers',
        name='Predicted Emissions',
        line=dict(color='#EF5350', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="12-Month Emissions Forecast",
        xaxis_title="Month",
        yaxis_title="Emissions (kg CO2)",
        height=350,
        showlegend=False
    )
    
    return fig


def main():
    # Header
    st.markdown('<h1 class="main-header">🌍 CarbonWise AI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Intelligent Carbon Footprint Estimator & Reduction Planner</p>', unsafe_allow_html=True)
    
    # Disclaimer
    with st.expander("ℹ️ About This Tool"):
        st.info("""
        **CarbonWise AI** is a prototype tool developed for the Greenovators Hackathon that uses Machine Learning 
        to estimate and predict carbon emissions for businesses.
        
        **Key Features:**
        - Calculate emissions across Scope 1, 2, and 3
        - ML-powered emissions prediction
        - Scenario-based reduction planning
        - Actionable recommendations
        
        **Important Notes:**
        - Emission factors are based on standard values and may need regional customization
        - Results are estimates for planning purposes
        - Always consult with certified carbon accounting professionals for official reporting
        - This is an educational prototype demonstrating AI for climate action
        """)
    
    # Sidebar
    st.sidebar.header("Input Parameters")
    
    # Sample data button
    if st.sidebar.button("📝 Load Sample Data"):
        st.session_state['use_sample'] = True
    
    # Industry selection
    industries = ['Manufacturing', 'IT Services', 'Logistics', 'Retail', 'Food Processing', 
                  'Textiles', 'Chemicals', 'Construction', 'Hospitality', 'Healthcare']
    industry = st.sidebar.selectbox("Industry Type", industries)
    
    # Activity inputs
    st.sidebar.subheader("Monthly Activity Data")
    
    if st.session_state.get('use_sample', False):
        electricity = 100000.0
        fuel = 5000.0
        transport = 15000.0
        employees = 250
        production = 20000.0
        fuel_type = 'Diesel'
    else:
        electricity = 0.0
        fuel = 0.0
        transport = 0.0
        employees = 0
        production = 0.0
        fuel_type = 'Diesel'
    
    electricity_kwh = st.sidebar.number_input(
        "Electricity Consumption (kWh)", 
        min_value=0.0, 
        value=electricity,
        step=1000.0,
        help="Total monthly electricity usage in kilowatt-hours"
    )
    
    fuel_types = ['Diesel', 'Petrol', 'Natural Gas', 'Coal', 'LPG']
    fuel_type = st.sidebar.selectbox("Fuel Type", fuel_types, index=fuel_types.index(fuel_type))
    
    fuel_liters = st.sidebar.number_input(
        "Fuel Consumption (Liters/Units)", 
        min_value=0.0, 
        value=fuel,
        step=100.0,
        help="Monthly fuel consumption in liters or equivalent units"
    )
    
    transport_km = st.sidebar.number_input(
        "Transport Distance (km)", 
        min_value=0.0, 
        value=transport,
        step=500.0,
        help="Total business transport/logistics distance per month"
    )
    
    num_employees = st.sidebar.number_input(
        "Number of Employees", 
        min_value=1, 
        value=employees if employees > 0 else 1,
        step=10,
        help="Total number of employees (for commute estimation)"
    )
    
    production_units = st.sidebar.number_input(
        "Production Volume (Units)", 
        min_value=0.0, 
        value=production,
        step=1000.0,
        help="Monthly production volume or business output metric"
    )
    
    # Calculate button
    calculate_button = st.sidebar.button("🔍 Calculate Emissions", type="primary")
    
    # Main content
    if calculate_button:
        # Prepare input data
        input_data = {
            'industry': industry,
            'electricity_kwh_monthly': electricity_kwh,
            'fuel_liters_monthly': fuel_liters,
            'fuel_type': fuel_type,
            'transport_km_monthly': transport_km,
            'num_employees': num_employees,
            'production_units_monthly': production_units
        }
        
        # Initialize calculators
        calculator = EmissionsCalculator()
        predictor = load_models()
        rec_engine = RecommendationEngine()
        
        if predictor is None:
            st.stop()
        
        # Calculate emissions
        emissions = calculator.calculate_total_emissions(input_data)
        breakdown = calculator.get_breakdown_percentage(emissions)
        top_contributor = calculator.identify_top_contributor(emissions)
        
        # ML Prediction
        ml_prediction = predictor.predict(input_data)
        
        # Display results
        st.header("📊 Emissions Analysis Results")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Emissions (Rule-based)",
                value=f"{emissions['total_kg']:,.0f} kg",
                delta=f"{emissions['total_tons']:.2f} tons CO2"
            )
        
        with col2:
            st.metric(
                label="ML Model Prediction",
                value=f"{ml_prediction:,.0f} kg",
                delta=f"{ml_prediction/1000:.2f} tons CO2"
            )
        
        with col3:
            st.metric(
                label="Top Contributor",
                value=top_contributor.split('(')[0].strip()
            )
        
        with col4:
            trees_needed = int(emissions['total_kg'] / 20)  # Rough estimate: 1 tree absorbs ~20kg CO2/year
            st.metric(
                label="Trees to Offset",
                value=f"{trees_needed:,}",
                help="Approximate number of trees needed to offset annual emissions"
            )
        
        # Scope breakdown
        st.subheader("Emissions by Scope")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Scope details
            st.markdown(f"""
            <div class="scope-card scope1">
                <h4>🔥 Scope 1: Direct Emissions</h4>
                <p><strong>{emissions['scope1_kg']:,.0f} kg CO2</strong> ({breakdown['scope1_pct']}%)</p>
                <p><small>From direct fuel combustion in owned/controlled sources</small></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="scope-card scope2">
                <h4>⚡ Scope 2: Indirect Emissions (Electricity)</h4>
                <p><strong>{emissions['scope2_kg']:,.0f} kg CO2</strong> ({breakdown['scope2_pct']}%)</p>
                <p><small>From purchased electricity consumption</small></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="scope-card scope3">
                <h4>🚚 Scope 3: Other Indirect Emissions</h4>
                <p><strong>{emissions['scope3_kg']:,.0f} kg CO2</strong> ({breakdown['scope3_pct']}%)</p>
                <p><small>From transportation, employee commute, and supply chain</small></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Pie chart
            fig_pie = create_emissions_chart(emissions)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Future predictions
        st.header("🔮 Future Emissions Forecast")
        
        growth_rate = st.slider(
            "Expected Monthly Growth Rate (%)", 
            min_value=-5.0, 
            max_value=10.0, 
            value=2.0,
            step=0.5,
            help="Expected growth/decline in business activity"
        ) / 100
        
        future_predictions = predictor.predict_future_months(input_data, months=12, growth_rate=growth_rate)
        
        fig_future = create_future_predictions_chart(future_predictions)
        st.plotly_chart(fig_future, use_container_width=True)
        
        total_future = sum(p['predicted_emissions_kg'] for p in future_predictions)
        st.info(f"📈 Projected annual emissions: **{total_future:,.0f} kg CO2** ({total_future/1000:.2f} tons)")
        
        # Reduction scenarios
        st.header("🎯 Carbon Reduction Scenarios")
        
        scenarios = predictor.predict_reduction_scenarios(input_data)
        
        fig_scenarios = create_scenario_chart(scenarios)
        st.plotly_chart(fig_scenarios, use_container_width=True)
        
        # Scenario details
        st.subheader("Scenario Details")
        
        cols = st.columns(len(scenarios))
        for idx, (name, scenario) in enumerate(scenarios.items()):
            with cols[idx]:
                st.markdown(f"""
                **{name}**
                
                {scenario['description']}
                
                **Emissions:** {scenario['predicted_emissions_kg']:,.0f} kg
                
                **Reduction:** {scenario['reduction_kg']:,.0f} kg ({scenario['reduction_pct']}%)
                """)
        
        # Recommendations
        st.header("💡 Recommended Actions")
        
        recommendations = rec_engine.get_recommendations(input_data, breakdown)
        
        for i, rec in enumerate(recommendations[:8], 1):  # Show top 8
            priority_class = f"{rec['priority'].lower()}-priority"
            st.markdown(f"""
            <div class="recommendation-card {priority_class}">
                <h4>{i}. {rec['action']} <span style="color: #666;">[{rec['priority']} Priority]</span></h4>
                <p><strong>Category:</strong> {rec['category']}</p>
                <p><strong>Description:</strong> {rec['description']}</p>
                <p><strong>Potential Reduction:</strong> {rec['potential_reduction']}</p>
                <p><strong>Investment:</strong> {rec['investment']} | <strong>Timeframe:</strong> {rec['timeframe']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Download report
        st.header("📥 Download Report")
        
        report_data = {
            'Metric': ['Industry', 'Total Emissions (kg)', 'Total Emissions (tons)', 
                      'Scope 1 (kg)', 'Scope 2 (kg)', 'Scope 3 (kg)',
                      'ML Prediction (kg)', 'Top Contributor'],
            'Value': [industry, emissions['total_kg'], emissions['total_tons'],
                     emissions['scope1_kg'], emissions['scope2_kg'], emissions['scope3_kg'],
                     ml_prediction, top_contributor]
        }
        
        df_report = pd.DataFrame(report_data)
        csv = df_report.to_csv(index=False)
        
        st.download_button(
            label="📄 Download Summary (CSV)",
            data=csv,
            file_name="carbonwise_emissions_report.csv",
            mime="text/csv"
        )
    
    else:
        # Welcome screen
        st.info("👈 Enter your business activity data in the sidebar and click 'Calculate Emissions' to begin analysis.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 🎯 What We Do
            - Calculate carbon footprint
            - Predict future emissions
            - Recommend reduction strategies
            - Compare scenarios
            """)
        
        with col2:
            st.markdown("""
            ### 🔬 Technology
            - Machine Learning models
            - Standard emission factors
            - Scope 1, 2, 3 categorization
            - Scenario simulation
            """)
        
        with col3:
            st.markdown("""
            ### 🌱 Impact
            - Identify emission hotspots
            - Plan reduction strategies
            - Track carbon abatement
            - Achieve net-zero goals
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p><strong>CarbonWise AI</strong> - Greenovators Hackathon Project</p>
        <p><small>Built with Python, Streamlit, scikit-learn | For educational purposes</small></p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
