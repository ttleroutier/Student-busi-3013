import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import numpy as np

# --- CONFIGURATION ---
st.set_page_config(page_title="Academic Risk Dashboard Pro", layout="wide", page_icon="🎓")

# Custom CSS
st.markdown("""
<style>
    .reportview-container .main .block-container{ padding-top: 2rem; }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #3e4258;
    }
</style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data
def load_data():
    return pd.read_csv("cleaned_student_data.csv")

try:
    df_raw = load_data()
    df = df_raw.copy() 

    # --- SIDEBAR ---
    st.sidebar.header("🕹️ Control Panel")
    threshold = st.sidebar.slider("Critical Load Threshold (Hours/Week)", 10, 40, 25)
    df['Is_Critical'] = df['External_Load'] > threshold
    
    income_options = ["All Classes"] + sorted(df['Family_Income'].unique().tolist())
    selected_income = st.sidebar.selectbox("Select a Class", income_options)
    
    if selected_income != "All Classes":
        df = df[df['Family_Income'] == selected_income]

    # --- HEADER ---
    st.title("🎓 Academic Risk Analysis System (Pro)")
    st.markdown(f"Analysis for: **{selected_income}**")
    st.markdown("---")

    # --- MAIN KPIs ---
    col1, col2, col3, col4 = st.columns(4)
    avg_risk = df['Risk_Score'].mean()
    col1.metric("Avg Risk Score", round(avg_risk, 2))
    
    critical_count = df['Is_Critical'].sum()
    col2.metric("Critical Students", f"{critical_count}", f"{round((critical_count/len(df))*100, 1)}% of group")
    col3.metric("Avg Exam Score", f"{round(df['Exam_Score'].mean(), 1)}%")
    col4.metric("Avg Attendance", f"{round(df['Attendance'].mean(), 1)}%")

    st.markdown("---")

    # --- VISUAL SECTION ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Success Analysis", 
        "⚖️ Comparison", 
        "🔥 Correlations", 
        "📊 Strategic Insights",
        "🚀 Intervention Simulator"
    ])

    # --- TABS 1-4 (KEEP PREVIOUS LOGIC) ---
    with tab1:
        st.subheader("Performance Overview")
        fig_score_dist = px.histogram(df, x="Exam_Score", color="Is_Critical", marginal="box", 
                                      color_discrete_map={True: '#e74c3c', False: '#3498db'},
                                      opacity=0.7, barmode="overlay")
        st.plotly_chart(fig_score_dist, use_container_width=True)

    with tab2:
        colA, colB = st.columns(2)
        with colA:
            st.subheader("Study Variance")
            df_var = df.groupby(['Family_Income', 'Is_Critical'])['Study_Variance'].mean().reset_index()
            fig_var = px.bar(df_var, x="Family_Income", y="Study_Variance", color="Is_Critical", barmode="group")
            st.plotly_chart(fig_var, use_container_width=True)
        with colB:
            st.subheader("Load vs Grade Impact")
            fig_scatter = px.scatter(df, x="External_Load", y="Exam_Score", color="Is_Critical", trendline="ols")
            st.plotly_chart(fig_scatter, use_container_width=True)

    with tab3:
        st.subheader("Correlation Matrix")
        corr_matrix = df[['Exam_Score', 'Hours_Studied', 'Attendance', 'Risk_Score', 'External_Load']].corr()
        fig_heatmap = ff.create_annotated_heatmap(z=corr_matrix.values, x=list(corr_matrix.columns), 
                                                  y=list(corr_matrix.index), colorscale='RdYlGn')
        st.plotly_chart(fig_heatmap, use_container_width=True)

    with tab4:
        st.subheader("Risk Mapping")
        df_stats = df.groupby(['Family_Income', 'Is_Critical']).size().reset_index(name='count')
        fig_sun = px.sunburst(df_stats, path=['Family_Income', 'Is_Critical'], values='count', color='Is_Critical')
        st.plotly_chart(fig_sun, use_container_width=True)

    # --- TAB 5: THE SIMULATOR (NEW & CORRECTED) ---
    with tab5:
        st.header("🚀 Strategic Intervention Simulator")
        
        # 1. MATHEMATICAL EXPLAINER
        with st.expander("📖 How is this calculated? (Model Logic)"):
            st.write("This simulator uses a **Linear Regression (OLS)** model calculated specifically for the current segment.")
            st.latex(r"Grade_{new} = Grade_{old} + (Hours_{saved} \times |\beta|)")
            st.info("""
            * **β (Beta/Slope):** The statistical 'cost' of each hour of external load.
            * **Abs Value:** We use the absolute value because reducing a 'negative' load results in a 'positive' gain.
            * **Cap:** Scores are capped at 100% to remain realistic.
            """)

        if len(df) > 5: # Needs a few points to calculate a trend
            s_col1, s_col2 = st.columns([1, 2])
            
            with s_col1:
                st.subheader("Parameters")
                reduction = st.slider("Hours Saved Per Week (e.g. Housing Aid)", 0, 20, 10)
                
                # --- CALCULATION ---
                # Calculate the local slope for the filtered group
                z = np.polyfit(df['External_Load'], df['Exam_Score'], 1)
                slope = abs(z[0]) # We take the absolute impact
                
                # Safety fallback if data is too noisy (slope too low)
                if slope < 0.2: 
                    slope = 0.5
                    st.caption("⚠️ Low correlation detected. Using a baseline impact of 0.5pts/h.")

                st.success(f"Calculated Impact: **+{round(slope, 2)} points** per hour saved.")

            with s_col2:
                # Apply simulation
                df_sim = df.copy()
                df_sim['Sim_Score'] = (df_sim['Exam_Score'] + (reduction * slope)).clip(upper=100)
                
                old_avg = df['Exam_Score'].mean()
                new_avg = df_sim['Sim_Score'].mean()
                
                m1, m2 = st.columns(2)
                m1.metric("Current Avg Grade", f"{round(old_avg, 1)}%")
                m2.metric("Simulated Avg Grade", f"{round(new_avg, 1)}%", 
                         delta=f"+{round(new_avg - old_avg, 1)}% improvement")

            # Comparison Visual
            comp_df = pd.DataFrame({
                'Status': ['Current'] * len(df) + ['Simulated'] * len(df),
                'Grades': pd.concat([df['Exam_Score'], df_sim['Sim_Score']])
            })
            fig_sim = px.violin(comp_df, x='Status', y='Grades', color='Status', box=True, points="all",
                               color_discrete_map={'Current': '#3498db', 'Simulated': '#2ecc71'})
            st.plotly_chart(fig_sim, use_container_width=True)
        else:
            st.warning("Insufficient data in this segment to run a reliable simulation.")

    # --- RECOMMENDATIONS ---
    st.markdown("---")
    st.header("💡 Executive Summary")
    r1, r2 = st.columns(2)
    with r1:
        st.error(f"**Immediate:** {critical_count} students identified as high-risk in the {selected_income} group.")
    with r2:
        st.info(f"**Strategy:** Reducing external load by 10h could boost the average by up to {round(10*slope, 1)} points.")

except FileNotFoundError:
    st.error("⚠️ Error: 'cleaned_student_data.csv' not found.")
