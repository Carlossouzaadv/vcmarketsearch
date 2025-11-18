"""
Capital Scout: VC Market Intelligence Agent
Professional Streamlit Dashboard for automated due diligence.
"""

import os
import sys
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# Import the main analysis function
from main import run_due_diligence

# Load environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="Capital Scout - VC Market Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Capital Scout branding
st.markdown("""
<style>
    /* Capital Scout Color Scheme */
    :root {
        --primary-navy: #1e3a5f;
        --primary-cyan: #00d4aa;
        --primary-emerald: #10b981;
        --accent-blue: #3b82f6;
        --bg-dark: #0f172a;
        --text-light: #f1f5f9;
    }

    /* Main title styling */
    .main-title {
        color: var(--primary-navy);
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #1e3a5f 0%, #00d4aa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .subtitle {
        text-align: center;
        color: #64748b;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8fafc;
    }

    /* Status messages */
    .status-running {
        padding: 1rem;
        border-radius: 0.5rem;
        background: linear-gradient(135deg, #00d4aa22 0%, #10b98122 100%);
        border-left: 4px solid var(--primary-cyan);
        margin: 1rem 0;
    }

    /* Metrics cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-top: 3px solid var(--primary-cyan);
    }

    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #1e3a5f 0%, #00d4aa 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        border-radius: 0.5rem;
        width: 100%;
        transition: transform 0.2s;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 212, 170, 0.3);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }

    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        color: var(--primary-navy);
    }

    .stTabs [aria-selected="true"] {
        border-bottom-color: var(--primary-cyan) !important;
        color: var(--primary-cyan) !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-title">🔍 Capital Scout</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">VC Market Intelligence Agent - Automated Due Diligence Platform</p>', unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    # API Status indicators
    st.markdown("#### API Credentials")

    parallel_key = os.getenv("PARALLEL_AI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if parallel_key:
        st.success("✅ Parallel AI: Connected")
    else:
        st.error("❌ Parallel AI: Not configured")
        st.info("Set `PARALLEL_AI_API_KEY` in .env file")

    if gemini_key:
        st.success("✅ Gemini AI: Connected")
    else:
        st.error("❌ Gemini AI: Not configured")
        st.info("Set `GEMINI_API_KEY` in .env file")

    st.markdown("---")

    # Analysis Settings
    st.markdown("#### Analysis Settings")

    max_competitors = st.slider(
        "Max Competitors",
        min_value=3,
        max_value=15,
        value=10,
        help="Number of competitors to analyze"
    )

    # Geographic Focus
    geographic_focus = st.selectbox(
        "🌍 Geographic Focus",
        options=[
            "Global",
            "Brazil",
            "United States",
            "United Kingdom",
            "Germany",
            "France",
            "Spain",
            "Italy",
            "Canada",
            "Australia",
            "China",
            "India",
            "Japan",
            "South Korea",
            "Singapore",
            "Latin America",
            "Europe",
            "Asia-Pacific",
            "Middle East",
            "Africa"
        ],
        index=0,  # Default to Global
        help="Select the geographic market to focus on when discovering competitors"
    )

    skip_viz = st.checkbox(
        "Skip Visualizations",
        value=False,
        help="Faster analysis without graphs"
    )

    st.markdown("---")

    # Info Section
    with st.expander("ℹ️ About Capital Scout"):
        st.markdown("""
        **Capital Scout** is an AI-powered market research agent that automates the VC due diligence process.

        **What it does:**
        - 🔍 Discovers & analyzes competitors
        - 💰 Tracks funding & investors
        - 💡 Identifies market opportunities
        - 📊 Generates investment reports
        - 📈 Creates visual analytics

        **Powered by:**
        - Parallel AI for web intelligence
        - Google Gemini for analysis
        - NetworkX for investor mapping
        """)

# Main Content Area
st.markdown("---")

# Input Section
col1, col2 = st.columns([3, 1])

with col1:
    startup_url = st.text_input(
        "🌐 Target Startup URL",
        placeholder="https://example-startup.com",
        help="Enter the website URL of the startup you want to analyze"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Spacing
    run_button = st.button("🚀 Run Due Diligence", type="primary")

# Analysis Execution
if run_button:
    if not startup_url:
        st.error("⚠️ Please enter a startup URL")
    elif not startup_url.startswith(('http://', 'https://')):
        st.error("⚠️ URL must start with http:// or https://")
    elif not parallel_key or not gemini_key:
        st.error("⚠️ API credentials not configured. Please set up your .env file.")
    else:
        # Create a status container
        status_container = st.container()

        with status_container:
            st.markdown('<div class="status-running">', unsafe_allow_html=True)
            st.markdown("### 🔄 Analysis in Progress...")
            st.markdown("</div>", unsafe_allow_html=True)

            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Create placeholder for real-time logs
            log_placeholder = st.empty()

            try:
                # Update progress
                status_text.text("Step 1/7: Initializing components...")
                progress_bar.progress(0.05)

                # Show info message
                with log_placeholder.container():
                    st.info("🔄 Analysis running... Check Railway logs for real-time progress.")

                # Run the analysis WITHOUT capturing output (so logs appear in Railway/terminal)
                result = run_due_diligence(
                    startup_url=startup_url,
                    max_competitors=max_competitors,
                    skip_visualizations=skip_viz,
                    parallel_api_key=parallel_key,
                    gemini_api_key=gemini_key,
                    geographic_focus=geographic_focus
                )

                if result and result.get('success'):
                    progress_bar.progress(1.0)
                    status_text.text("✅ Analysis Complete!")
                    log_placeholder.empty()

                    st.success("🎉 Due diligence completed successfully!")

                    # Store results in session state
                    st.session_state['analysis_result'] = result

                else:
                    st.error("❌ Analysis failed. Check Railway deployment logs for error details.")
                    if result:
                        st.json({
                            'startup_name': result.get('startup_info', {}).get('name', 'Unknown'),
                            'competitors_found': len(result.get('competitors', [])),
                            'status': 'partial_failure'
                        })

            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.warning("💡 Check Railway logs for detailed error information.")

# Display Results (if available)
if 'analysis_result' in st.session_state:
    result = st.session_state['analysis_result']

    st.markdown("---")
    st.markdown("## 📊 Analysis Results")

    # Summary Metrics
    startup_info = result.get('startup_info', {})
    competitors = result.get('competitors', [])
    funding_landscape = result.get('funding_landscape', {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Target Company",
            startup_info.get('name', 'Unknown'),
            delta=None
        )

    with col2:
        st.metric(
            "Competitors Analyzed",
            len(competitors),
            delta=None
        )

    with col3:
        total_funding = funding_landscape.get('total_market_funding', 0)
        st.metric(
            "Market Funding",
            f"${total_funding:,.0f}",
            delta=None
        )

    with col4:
        funded_count = funding_landscape.get('funded_competitors_count', 0)
        st.metric(
            "Funded Competitors",
            f"{funded_count}/{len(competitors)}",
            delta=None
        )

    st.markdown("---")

    # Tabbed Results View
    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Full Report",
        "🗺️ Market Map",
        "📊 Competitive Matrix",
        "🔗 Investor Network"
    ])

    with tab1:
        # Display the markdown report
        report_path = result.get('report_path')
        if report_path and Path(report_path).exists():
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()

            # Add download button
            col1, col2 = st.columns([3, 1])
            with col2:
                st.download_button(
                    label="⬇️ Download Report",
                    data=report_content,
                    file_name=Path(report_path).name,
                    mime="text/markdown"
                )

            st.markdown(report_content)
        else:
            st.warning("Report file not found")

    with tab2:
        viz_paths = result.get('visualization_paths', [])
        market_map = next((p for p in viz_paths if 'market_map' in p), None)

        if market_map and Path(market_map).exists():
            st.image(market_map, use_container_width=True)

            with open(market_map, 'rb') as f:
                st.download_button(
                    label="⬇️ Download Market Map",
                    data=f,
                    file_name=Path(market_map).name,
                    mime="image/png"
                )
        else:
            st.info("Market map not available")

    with tab3:
        comp_matrix = next((p for p in viz_paths if 'competitive_matrix' in p), None)

        if comp_matrix and Path(comp_matrix).exists():
            st.image(comp_matrix, use_container_width=True)

            with open(comp_matrix, 'rb') as f:
                st.download_button(
                    label="⬇️ Download Competitive Matrix",
                    data=f,
                    file_name=Path(comp_matrix).name,
                    mime="image/png"
                )
        else:
            st.info("Competitive matrix not available")

    with tab4:
        investor_network = next((p for p in viz_paths if 'investor_network' in p), None)

        if investor_network and Path(investor_network).exists():
            st.image(investor_network, use_container_width=True)

            with open(investor_network, 'rb') as f:
                st.download_button(
                    label="⬇️ Download Investor Network",
                    data=f,
                    file_name=Path(investor_network).name,
                    mime="image/png"
                )
        else:
            st.info("Investor network not available")

    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Run New Analysis"):
            del st.session_state['analysis_result']
            st.rerun()

    with col2:
        report_path = result.get('report_path')
        if report_path:
            report_dir = str(Path(report_path).parent)
            st.info(f"📁 Results saved in: `{report_dir}`")

    with col3:
        st.info(f"⏱️ Completed: {result.get('timestamp', 'N/A')}")

else:
    # Show welcome message when no analysis has been run
    st.markdown("---")
    st.info("""
    ### 👋 Welcome to Capital Scout!

    To get started:
    1. ✅ Ensure your API credentials are configured in the sidebar
    2. 🌐 Enter the target startup's website URL above
    3. ⚙️ Adjust analysis settings if needed (sidebar)
    4. 🚀 Click "Run Due Diligence" to start the analysis

    The analysis typically takes **7-11 minutes** for a complete market research report including:
    - Competitor discovery and analysis
    - Funding and investor landscape
    - Market opportunity identification
    - Visual analytics and reports
    """)

    # Example URLs
    with st.expander("💡 Example Startup URLs to Try"):
        st.markdown("""
        - `https://www.stripe.com`
        - `https://www.notion.so`
        - `https://www.linear.app`
        - `https://www.vercel.com`
        - `https://www.retool.com`

        *Note: Analysis quality depends on publicly available information.*
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 2rem 0;'>
    <p><strong>Capital Scout</strong> - AI-Powered VC Market Intelligence</p>
    <p style='font-size: 0.9rem;'>Powered by Parallel AI • Google Gemini • NetworkX</p>
</div>
""", unsafe_allow_html=True)
