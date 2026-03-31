import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff

# --- PROFESSIONAL PAGE CONFIGURATION ---
st.set_page_config(page_title="Academic Risk Dashboard Pro", layout="wide", page_icon="🎓")

# Custom CSS for styling
st.markdown("""
<style>
    .reportview-container .main .block-container{
        padding-top: 2rem;
    }
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
    # Load the cleaned dataset exported from Colab
    return pd.read_csv("cleaned_student_data.csv")

try:
    df_raw = load_data()
    df = df_raw.copy() 

    # --- SIDEBAR (FILTERS & CONFIGURATION) ---
    st.sidebar.header("🕹️ Control Panel")
    st.sidebar.markdown("---")
    
    # 1. Interactive Threshold Slider
    st.sidebar.subheader("Risk Threshold Settings")
    threshold = st.sidebar.slider("Critical Load Threshold (Hours/Week)", 10, 40, 25, help="Total commute + activities")
    
    # Dynamic recalculation based on slider
    df['Is_Critical'] = df['External_Load'] > threshold
    
    st.sidebar.markdown("---")

    # 2. NEW: Income Class Filter
    st.sidebar.subheader("Filter by Socio-Economic Class")
    income_options = ["All Classes"] + sorted(df['Family_Income'].unique().tolist())
    selected_income = st.sidebar.selectbox("Select a Class", income_options)
    
    # Apply income filter
    if selected_income != "All Classes":
        df = df[df['Family_Income'] == selected_income]

    st.sidebar.markdown("---")
    st.sidebar.info(f"💡 Visualizing {len(df)} students.")

    # --- HEADER ---
    st.title("🎓 Academic Risk Analysis System (Pro)")
    st.markdown(f"Performance Analysis for: **{selected_income}** (Critical Threshold: {threshold}h/week)")
    st.markdown("---")

    # --- KEY PERFORMANCE INDICATORS (KPIs) ---
    col1, col2, col3, col4 = st.columns(4)
    
    # KPI 1: Average Risk Index
    avg_risk = df['Risk_Score'].mean()
    overall_risk_avg = df_raw['Risk_Score'].mean()
    col1.metric("Avg Risk Score", round(avg_risk, 2), 
               delta=f"{round(avg_risk - overall_risk_avg, 2)} vs Total Avg", delta_color="inverse")
    
    # KPI 2: % Critical Students
    critical_count = df['Is_Critical'].sum()
    critical_pct = (critical_count / len(df)) * 100
    col2.metric("Critical Students", f"{critical_count}", f"{round(critical_pct, 1)}% of group")
    
    # KPI 3: Avg Grade
    avg_exam = df['Exam_Score'].mean()
    overall_exam_avg = df_raw['Exam_Score'].mean()
    col3.metric("Avg Exam Score", f"{round(avg_exam, 1)}%", 
               delta=f"{round(avg_exam - overall_exam_avg, 1)}% vs Total Avg")

    # KPI 4: Attendance rate
    avg_attendance = df['Attendance'].mean()
    col4.metric("Avg Attendance", f"{round(avg_attendance, 1)}%")

    st.markdown("---")

    # --- VISUAL SECTION: ANALYSIS TABS ---
    tab1, tab2, tab3 = st.tabs(["🔍 Success Analysis", "⚖️ Comparison & Variance", "🔥 Correlations"])

    with tab1:
        st.subheader("Exam Score Distribution")
        # Histogram comparing Critical vs Non-Critical students
        fig_score_dist = px.histogram(df, x="Exam_Score", color="Is_Critical", 
                                      marginal="box", 
                                      title=f"Grade Distribution (Critical Student Comparison)",
                                      labels={"Exam_Score": "Exam Grade", "count": "Student Count"},
                                      color_discrete_map={True: '#e74c3c', False: '#3498db'},
                                      opacity=0.7,
                                      barmode="overlay")
        
        fig_score_dist.add_vline(x=70, line_dash="dash", line_color="white", annotation_text="Class Goal (70%)")
        st.plotly_chart(fig_score_dist, use_container_width=True)
        st.info("💡 Insight: If the red distribution is shifted left, it proves external load negatively impacts grades.")

    with tab2:
        colA, colB = st.columns(2)
        
        with colA:
            st.subheader("Study Variance by Class")
            df_grouped_var = df.groupby(['Family_Income', 'Is_Critical'])['Study_Variance'].mean().reset_index()
            fig_grouped_var = px.bar(df_grouped_var, x="Family_Income", y="Study_Variance", color="Is_Critical", 
                                     barmode="group",
                                     title=f"Average Study Gap (20h Goal)",
                                     labels={"Study_Variance": "Variance (Hours)", "Family_Income": "Income Level"},
                                     color_discrete_map={True: '#e74c3c', False: '#3498db'})
            fig_grouped_var.add_hline(y=0, line_dash="dash", line_color="white")
            st.plotly_chart(fig_grouped_var, use_container_width=True)

        with colB:
            st.subheader("External Load vs. Grades")
            fig_scatter_load = px.scatter(df, x="External_Load", y="Exam_Score", color="Is_Critical",
                                          title="Correlation: External Load vs Final Grade",
                                          labels={"External_Load": "Total Weekly Load (Hours)", "Exam_Score": "Final Grade"},
                                          color_discrete_map={True: '#e74c3c', False: '#3498db'},
                                          hover_data=['Family_Income', 'Attendance'],
                                          trendline="ols") 
            st.plotly_chart(fig_scatter_load, use_container_width=True)

    with tab3:
        st.subheader("Correlation Heatmap: Socio-Economic vs. Performance")
        
        correlation_cols = ['Exam_Score', 'Hours_Studied', 'Attendance', 'Risk_Score', 
                            'Family_Income_Score', 'Distance_Score', 'External_Load']
        corr_matrix = df[correlation_cols].corr()

        fig_heatmap = ff.create_annotated_heatmap(
            z=corr_matrix.values,
            x=list(corr_matrix.columns),
            y=list(corr_matrix.index),
            annotation_text=corr_matrix.round(2).values,
            colorscale='RdYlGn',
            showscale=True,
            font_colors=['white'],
            xgap=2, ygap=2
        )
        
        fig_heatmap.update_layout(title="Statistical Links (Near 1 = Strong Link, Near -1 = Inverse)", 
                                  height=600)
        st.plotly_chart(fig_heatmap, use_container_width=True)
        st.warning("⚠️ Reading the Heatmap: Look at correlations with 'Exam_Score'. Is success linked more to Attendance or Study Hours?")

    st.markdown("---")

    # --- PRIORITY SUPPORT LIST ---
    st.subheader("📋 Priority List: High-Risk Students to Support")
    critical_df = df[df['Is_Critical'] == True].sort_values(by="Risk_Score", ascending=False)
    
    if not critical_df.empty:
        st.dataframe(critical_df[['Family_Income', 'External_Load', 'Attendance', 'Exam_Score', 'Risk_Score']], 
                     use_container_width=True, 
                     column_config={
                        "Risk_Score": st.column_config.NumberColumn(format="%.2f", label="Risk Score"),
                        "Exam_Score": st.column_config.NumberColumn(format="%d%%", label="Final Grade")
                     })
    else:
        st.success("🎉 Great news! No students in this category exceed the critical threshold.")

except FileNotFoundError:
    st.error("⚠️ Error: 'cleaned_student_data.csv' not found. Please upload it to your GitHub repository.")
