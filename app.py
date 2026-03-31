import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff

# --- PROFESSIONAL PAGE CONFIGURATION ---
st.set_page_config(page_title="Academic Risk Dashboard Pro", layout="wide", page_icon="🎓")

# Custom CSS for styling
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

    # --- SIDEBAR (FILTERS & CONFIGURATION) ---
    st.sidebar.header("🕹️ Control Panel")
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("Risk Threshold Settings")
    threshold = st.sidebar.slider("Critical Load Threshold (Hours/Week)", 10, 40, 25)
    df['Is_Critical'] = df['External_Load'] > threshold
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filter by Socio-Economic Class")
    income_options = ["All Classes"] + sorted(df['Family_Income'].unique().tolist())
    selected_income = st.sidebar.selectbox("Select a Class", income_options)
    
    if selected_income != "All Classes":
        df = df[df['Family_Income'] == selected_income]

    # --- HEADER ---
    st.title("🎓 Academic Risk Analysis System (Pro)")
    st.markdown(f"Performance Analysis for: **{selected_income}**")
    st.markdown("---")

    # --- KEY PERFORMANCE INDICATORS (KPIs) ---
    col1, col2, col3, col4 = st.columns(4)
    avg_risk = df['Risk_Score'].mean()
    overall_risk_avg = df_raw['Risk_Score'].mean()
    col1.metric("Avg Risk Score", round(avg_risk, 2), 
               delta=f"{round(avg_risk - overall_risk_avg, 2)} vs Total Avg", delta_color="inverse")
    
    critical_count = df['Is_Critical'].sum()
    col2.metric("Critical Students", f"{critical_count}", f"{round((critical_count/len(df))*100, 1)}% of group")
    
    avg_exam = df['Exam_Score'].mean()
    col3.metric("Avg Exam Score", f"{round(avg_exam, 1)}%")

    avg_attendance = df['Attendance'].mean()
    col4.metric("Avg Attendance", f"{round(avg_attendance, 1)}%")

    st.markdown("---")

    # --- VISUAL SECTION: ANALYSIS TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Success Analysis", "⚖️ Comparison", "🔥 Correlations", "🚀 Strategic Insights"])

    with tab1:
        st.subheader("Grade Distribution (Critical vs. Non-Critical)")
        fig_score_dist = px.histogram(df, x="Exam_Score", color="Is_Critical", marginal="box", 
                                      color_discrete_map={True: '#e74c3c', False: '#3498db'},
                                      opacity=0.7, barmode="overlay")
        st.plotly_chart(fig_score_dist, use_container_width=True)

    with tab2:
        colA, colB = st.columns(2)
        with colA:
            st.subheader("Study Variance by Income")
            df_var = df.groupby(['Family_Income', 'Is_Critical'])['Study_Variance'].mean().reset_index()
            fig_var = px.bar(df_var, x="Family_Income", y="Study_Variance", color="Is_Critical", barmode="group",
                             color_discrete_map={True: '#e74c3c', False: '#3498db'})
            fig_var.add_hline(y=0, line_dash="dash", line_color="white")
            st.plotly_chart(fig_var, use_container_width=True)
        with colB:
            st.subheader("External Load Impact")
            fig_scatter = px.scatter(df, x="External_Load", y="Exam_Score", color="Is_Critical", trendline="ols",
                                     color_discrete_map={True: '#e74c3c', False: '#3498db'})
            st.plotly_chart(fig_scatter, use_container_width=True)

    with tab3:
        st.subheader("Statistical Correlation Matrix")
        corr_cols = ['Exam_Score', 'Hours_Studied', 'Attendance', 'Risk_Score', 'External_Load']
        corr_matrix = df[corr_cols].corr()
        fig_heatmap = ff.create_annotated_heatmap(z=corr_matrix.values, x=list(corr_matrix.columns), 
                                                  y=list(corr_matrix.index), colorscale='RdYlGn')
        st.plotly_chart(fig_heatmap, use_container_width=True)

    with tab4:
        st.subheader("Advanced Population Mapping")
        col_left, col_right = st.columns(2)
        
        with col_left:
            # Hierarchical breakdown of the population
            fig_sun = px.sunburst(df, path=['Family_Income', 'Is_Critical'], 
                                 title="Income vs Risk Breakdown")
            st.plotly_chart(fig_sun, use_container_width=True)
        
        with col_right:
            # Density hotspots for performance
            fig_density = px.density_heatmap(df, x="External_Load", y="Exam_Score", 
                                            title="Performance Density Hotspots",
                                            color_continuous_scale="Viridis")
            st.plotly_chart(fig_density, use_container_width=True)

        st.markdown("---")
        st.header("💡 Business Recommendations")
        
        # Dynamic Recommendations based on Data
        rec_col1, rec_col2 = st.columns(2)
        
        with rec_col1:
            st.write("### 🚨 Immediate Actions")
            if critical_count > 0:
                st.error(f"**Targeted Support:** {critical_count} students are in the high-risk zone. Initiate 1-on-1 counseling for students with Risk Scores > {round(df['Risk_Score'].median(), 2)}.")
            if avg_attendance < 85:
                st.warning("**Attendance Intervention:** Average attendance is low. Implement an automated SMS alert system for missed classes.")
            else:
                st.success("**Attendance levels** are healthy for this segment.")

        with rec_col2:
            st.write("### 📅 Long-term Strategy")
            if selected_income == "Low":
                st.info("**Financial Relief:** Data shows Low-Income students have the tightest study margins. Recommendation: Expand 'Travel Grants' to reduce commute-based time poverty.")
            elif selected_income == "High":
                st.info("**Engagement Strategy:** High-Income students show negative study variance. Recommendation: Increase academic rigor or extracurricular integration.")
            else:
                st.info("**Hybrid Solutions:** For Mid-Income groups, offer more 'Asynchronous Learning' options to accommodate their {round(df['External_Load'].mean(), 1)}h average external load.")

    st.markdown("---")
    st.subheader("📋 Priority Student List")
    critical_df = df[df['Is_Critical'] == True].sort_values(by="Risk_Score", ascending=False)
    st.dataframe(critical_df[['Family_Income', 'External_Load', 'Attendance', 'Exam_Score', 'Risk_Score']], use_container_width=True)

except FileNotFoundError:
    st.error("⚠️ Error: 'cleaned_student_data.csv' not found.")
