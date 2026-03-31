import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff

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
    st.sidebar.markdown("---")
    threshold = st.sidebar.slider("Critical Load Threshold (Hours/Week)", 10, 40, 25)
    df['Is_Critical'] = df['External_Load'] > threshold
    
    income_options = ["All Classes"] + sorted(df['Family_Income'].unique().tolist())
    selected_income = st.sidebar.selectbox("Select a Class", income_options)
    
    if selected_income != "All Classes":
        df = df[df['Family_Income'] == selected_income]

    # --- HEADER ---
    st.title("🎓 Academic Risk Analysis System (Pro)")
    st.markdown(f"Performance Analysis for: **{selected_income}**")
    st.markdown("---")

    # --- MAIN KPIs ---
    col1, col2, col3, col4 = st.columns(4)
    avg_risk = df['Risk_Score'].mean()
    overall_risk_avg = df_raw['Risk_Score'].mean()
    col1.metric("Avg Risk Score", round(avg_risk, 2), 
               delta=f"{round(avg_risk - overall_risk_avg, 2)} vs Total Avg", delta_color="inverse")
    
    critical_count = df['Is_Critical'].sum()
    col2.metric("Critical Students", f"{critical_count}", f"{round((critical_count/len(df))*100, 1)}% of group")
    col3.metric("Avg Exam Score", f"{round(df['Exam_Score'].mean(), 1)}%")
    col4.metric("Avg Attendance", f"{round(df['Attendance'].mean(), 1)}%")

    st.markdown("---")

    # --- VISUAL SECTION ---
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Success Analysis", "⚖️ Comparison", "🔥 Correlations", "🚀 Strategic Insights"])

    with tab1:
        st.subheader("Performance Overview & Success Distribution")
        
        # NEW KPIs for Success Analysis
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Students at Risk", f"{critical_count}")
        kpi2.metric("Total Students (Segment)", f"{len(df)}")
        kpi3.metric("Average Grade", f"{round(df['Exam_Score'].mean(), 1)}%")
        kpi4.metric("Minimum Grade", f"{round(df['Exam_Score'].min(), 1)}%")

        st.info("**Interpretation:** Compare the 'Critical' (Red) vs 'Non-Critical' (Blue) curves. A shift to the left for red bars indicates that high load is directly impacting performance.")
        
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
        st.subheader("Advanced Population Mapping & Risk Percentages")
        
        # CALCULATING PERCENTAGES PER CLASS
        # We group by Income and Risk Status, then calculate the % relative to each income group
        df_stats = df.groupby(['Family_Income', 'Is_Critical']).size().reset_index(name='count')
        df_stats['Percentage'] = df_stats.groupby('Family_Income')['count'].transform(lambda x: (x / x.sum() * 100).round(1))
        
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.markdown("**Risk Distribution by Class (%)**")
            # Using a sunburst with percentage data
            fig_sun = px.sunburst(df_stats, path=['Family_Income', 'Is_Critical'], values='count',
                                 color='Is_Critical', color_discrete_map={True: '#e74c3c', False: '#3498db'},
                                 custom_data=['Percentage'])
            fig_sun.update_traces(hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Share of Class: %{customdata[0]}%')
            st.plotly_chart(fig_sun, use_container_width=True)
            
        with col_right:
            st.markdown("**Risk Proportions Table**")
            st.dataframe(df_stats, use_container_width=True)
            st.info("💡 **Insight:** This table shows the exact percentage of students in each class who are over the threshold.")

        st.markdown("---")
        # DENSITY HEATMAP
        st.subheader("Performance Density Hotspots")
        fig_density = px.density_heatmap(df, x="External_Load", y="Exam_Score", 
                                        color_continuous_scale="Viridis", text_auto=True)
        st.plotly_chart(fig_density, use_container_width=True)

    # --- RECOMMENDATIONS & LIST ---
    st.markdown("---")
    st.header("💡 Executive Recommendations")
    rec_col1, rec_col2 = st.columns(2)
    with rec_col1:
        st.write("### 🚨 Immediate Actions")
        if critical_count > 0:
            st.error(f"**Targeted Support:** {critical_count} students are at high risk.")
        if df['Attendance'].mean() < 85:
            st.warning("**Attendance Intervention:** Low attendance detected.")
    with rec_col2:
        st.write("### 📅 Long-term Strategy")
        st.info(f"Strategy for **{selected_income}** class: Focus on reducing 'External Load' through transport/scholarship aid.")

    st.markdown("---")
    st.subheader("📋 Priority Student List")
    critical_df = df[df['Is_Critical'] == True].sort_values(by="Risk_Score", ascending=False)
    st.dataframe(critical_df[['Family_Income', 'External_Load', 'Attendance', 'Exam_Score', 'Risk_Score']], use_container_width=True)

except FileNotFoundError:
    st.error("⚠️ Error: 'cleaned_student_data.csv' not found.")
