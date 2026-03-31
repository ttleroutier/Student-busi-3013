import streamlit as st
import pandas as pd
import plotly.express as px

# Professional Page Setup
st.set_page_config(page_title="Academic Risk Analyzer", layout="wide")

# --- HEADER ---
st.title("🎓 Student Success & Socio-Economic Risk Index")
st.markdown("""
This dashboard identifies students whose academic success is threatened by **external time constraints** (commute, activities) and **financial pressure**.
""")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    # Loading the cleaned dataset exported from Colab
    return pd.read_csv("cleaned_student_data.csv")

try:
    df = load_data()

    # --- SIDEBAR: INTERACTIVITY ---
    st.sidebar.header("Risk Configuration")
    # Allowing the user to adjust the 25-hour 'Danger Zone' threshold
    threshold = st.sidebar.slider("External Load Threshold (Hours/Week)", 10, 40, 25)
    
    # Dynamic recalculation based on the slider
    df['Is_Critical'] = df['External_Load'] > threshold

    # --- KEY PERFORMANCE INDICATORS (KPIs) ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Average Risk Index", round(df['Risk_Score'].mean(), 2))
    
    critical_count = df['Is_Critical'].sum()
    col2.metric("Critical Students", f"{critical_count} ({round(critical_count/len(df)*100)}%)")
    
    col3.metric("Average Exam Score", f"{round(df['Exam_Score'].mean(), 1)}%")

    # --- VISUAL ANALYSIS ---
    st.subheader("Time Allocation & Study Variance")
    
    # Aggregating data for the grouped bar chart
    df_grouped = df.groupby(['Family_Income', 'Is_Critical'])['Study_Variance'].mean().reset_index()
    
    fig = px.bar(df_grouped, 
                 x="Family_Income", 
                 y="Study_Variance", 
                 color="Is_Critical",
                 barmode="group",
                 title=f"Average Study Gap by Income (Threshold: {threshold}h)",
                 labels={"Study_Variance": "Gap to 20h Goal (Hours)", "Family_Income": "Income Level"},
                 color_discrete_map={True: '#e74c3c', False: '#3498db'})
    
    # Target line at 0 (20h study goal)
    fig.add_hline(y=0, line_dash="dash", line_color="black", annotation_text="20h Goal")
    st.plotly_chart(fig, use_container_width=True)

    # --- PRIORITY LIST ---
    st.subheader("📋 Priority Support List (High-Risk Profiles)")
    # Showing only students above the chosen threshold, sorted by Risk Score
    critical_list = df[df['Is_Critical'] == True][['Family_Income', 'External_Load', 'Exam_Score', 'Risk_Score']]
    st.dataframe(critical_list.sort_values(by="Risk_Score", ascending=False), use_container_width=True)

except FileNotFoundError:
    st.error("⚠️ Error: 'cleaned_student_data.csv' not found. Please upload it to the app folder.")
