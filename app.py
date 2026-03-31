import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import numpy as np

# --- CONFIGURATION PROFESSIONNELLE ---
st.set_page_config(page_title="Academic Risk Dashboard Pro", layout="wide", page_icon="🎓")

# Style CSS personnalisé
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

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data
def load_data():
    return pd.read_csv("cleaned_student_data.csv")

try:
    df_raw = load_data()
    df = df_raw.copy() 

    # --- BARRE LATÉRALE (FILTRES) ---
    st.sidebar.header("🕹️ Panneau de Contrôle")
    st.sidebar.markdown("---")
    threshold = st.sidebar.slider("Seuil de Charge Critique (Heures/Semaine)", 10, 40, 25)
    df['Is_Critical'] = df['External_Load'] > threshold
    
    income_options = ["Toutes les Classes"] + sorted(df['Family_Income'].unique().tolist())
    selected_income = st.sidebar.selectbox("Filtrer par Classe Sociale", income_options)
    
    if selected_income != "Toutes les Classes":
        df = df[df['Family_Income'] == selected_income]

    # --- EN-TÊTE ---
    st.title("🎓 Système d'Analyse du Risque Académique (Pro)")
    st.markdown(f"Analyse pour le segment : **{selected_income}**")
    st.markdown("---")

    # --- KPIs PRINCIPAUX ---
    col1, col2, col3, col4 = st.columns(4)
    avg_risk = df['Risk_Score'].mean()
    overall_risk_avg = df_raw['Risk_Score'].mean()
    
    col1.metric("Score de Risque Moyen", round(avg_risk, 2), 
               delta=f"{round(avg_risk - overall_risk_avg, 2)} vs Moyenne Totale", delta_color="inverse")
    
    critical_count = df['Is_Critical'].sum()
    col2.metric("Étudiants Critiques", f"{critical_count}", f"{round((critical_count/len(df))*100, 1)}% du groupe")
    col3.metric("Note Moyenne (Examen)", f"{round(df['Exam_Score'].mean(), 1)}%")
    col4.metric("Taux de Présence Moyen", f"{round(df['Attendance'].mean(), 1)}%")

    st.markdown("---")

    # --- SECTIONS VISUELLES (ONGLETS) ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Analyse de Succès", 
        "⚖️ Comparaisons", 
        "🔥 Corrélations", 
        "📊 Mapping Population",
        "🚀 Simulateur d'Intervention"
    ])

    with tab1:
        st.subheader("Distribution des Performances & KPIs de Succès")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Étudiants à Risque", f"{critical_count}")
        k2.metric("Total Étudiants (Segment)", f"{len(df)}")
        k3.metric("Note Moyenne", f"{round(df['Exam_Score'].mean(), 1)}%")
        k4.metric("Note Minimale", f"{round(df['Exam_Score'].min(), 1)}%")

        st.info("**Interprétation :** Observez le décalage entre les 'Critiques' (Rouge) et les 'Non-Critiques' (Bleu). Si les barres rouges sont plus à gauche, la charge horaire dégrade les notes.")
        
        fig_score_dist = px.histogram(df, x="Exam_Score", color="Is_Critical", marginal="box", 
                                      color_discrete_map={True: '#e74c3c', False: '#3498db'},
                                      opacity=0.7, barmode="overlay")
        st.plotly_chart(fig_score_dist, use_container_width=True)

    with tab2:
        colA, colB = st.columns(2)
        with colA:
            st.subheader("Écart de Travail par Revenu")
            df_var = df.groupby(['Family_Income', 'Is_Critical'])['Study_Variance'].mean().reset_index()
            fig_var = px.bar(df_var, x="Family_Income", y="Study_Variance", color="Is_Critical", barmode="group",
                             color_discrete_map={True: '#e74c3c', False: '#3498db'})
            fig_var.add_hline(y=0, line_dash="dash", line_color="white")
            st.plotly_chart(fig_var, use_container_width=True)
        with colB:
            st.subheader("Impact de la Charge Externe")
            fig_scatter = px.scatter(df, x="External_Load", y="Exam_Score", color="Is_Critical", trendline="ols",
                                     color_discrete_map={True: '#e74c3c', False: '#3498db'})
            st.plotly_chart(fig_scatter, use_container_width=True)

    with tab3:
        st.subheader("Matrice de Corrélation Statistique")
        corr_cols = ['Exam_Score', 'Hours_Studied', 'Attendance', 'Risk_Score', 'External_Load']
        corr_matrix = df[corr_cols].corr()
        fig_heatmap = ff.create_annotated_heatmap(z=corr_matrix.values, x=list(corr_matrix.columns), 
                                                  y=list(corr_matrix.index), colorscale='RdYlGn')
        st.plotly_chart(fig_heatmap, use_container_width=True)

    with tab4:
        st.subheader("Mapping Avancé & Répartition du Risque")
        df_stats = df.groupby(['Family_Income', 'Is_Critical']).size().reset_index(name='count')
        df_stats['Pourcentage'] = df_stats.groupby('Family_Income')['count'].transform(lambda x: (x / x.sum() * 100).round(1))
        
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("**Part du Risque par Classe (%)**")
            fig_sun = px.sunburst(df_stats, path=['Family_Income', 'Is_Critical'], values='count',
                                 color='Is_Critical', color_discrete_map={True: '#e74c3c', False: '#3498db'},
                                 custom_data=['Pourcentage'])
            fig_sun.update_traces(hovertemplate='<b>%{label}</b><br>Nombre: %{value}<br>Part dans la classe: %{customdata[0]}%')
            st.plotly_chart(fig_sun, use_container_width=True)
        with c_right:
            st.markdown("**Tableau de Répartition**")
            st.dataframe(df_stats, use_container_width=True)

        st.markdown("---")
        st.subheader("Densité de Performance (Points Chauds)")
        fig_density = px.density_heatmap(df, x="External_Load", y="Exam_Score", color_continuous_scale="Viridis", text_auto=True)
        st.plotly_chart(fig_density, use_container_width=True)

    with tab5:
        st.header("🚀 Simulateur d'Intervention Stratégique")
        st.markdown("""
        **Objectif :** Prédire l'impact d'une politique sociale (ex: bourses de transport) qui réduirait la charge externe des étudiants.
        """)

        s_col1, s_col2 = st.columns([1, 2])
        with s_col1:
            st.subheader("Paramètres de Simulation")
            reduction = st.slider("Heures économisées par semaine", 0, 20, 5, 
                                 help="Heures gagnées via un logement plus proche ou aide financière.")
            
            # Calcul de la pente réelle entre Charge Externe et Note d'Examen
            slope = np.polyfit(df_raw['External_Load'], df_raw['Exam_Score'], 1)[0]
            st.info(f"Taux d'impact calculé : Chaque heure économisée = **+{abs(round(slope, 2))} points** sur la note finale.")

        with s_col2:
            df_sim = df.copy()
            df_sim['Note_Simulée'] = (df_sim['Exam_Score'] + (reduction * abs(slope))).clip(upper=100)
            
            cur_avg = df['Exam_Score'].mean()
            sim_avg = df_sim['Note_Simulée'].mean()
            
            m1, m2 = st.columns(2)
            m1.metric("Moyenne Actuelle", f"{round(cur_avg, 1)}%")
            m2.metric("Moyenne Simulée", f"{round(sim_avg, 1)}%", delta=f"+{round(sim_avg - cur_avg, 1)}% d'amélioration")

        st.subheader("Projection de l'Évolution des Notes")
        comp_df = pd.DataFrame({
            'Statut': ['Actuel'] * len(df) + ['Après Intervention'] * len(df),
            'Notes': pd.concat([df['Exam_Score'], df_sim['Note_Simulée']])
        })
        fig_violin = px.violin(comp_df, x='Statut', y='Notes', color='Statut', box=True, points="all")
        st.plotly_chart(fig_violin, use_container_width=True)

    # --- RECOMMANDATIONS EXÉCUTIVES ---
    st.markdown("---")
    st.header("💡 Recommandations Stratégiques")
    rec1, rec2 = st.columns(2)
    with rec1:
        st.write("### 🚨 Actions Immédiates")
        if critical_count > 0:
            st.error(f"**Soutien Ciblé :** {critical_count} étudiants sont en zone critique.")
        if df['Attendance'].mean() < 85:
            st.warning("**Alerte Assiduité :** Le taux de présence est faible.")
    with rec2:
        st.write("### 📅 Stratégie Long Terme")
        st.info(f"Pour la classe **{selected_income}** : Priorité à la réduction de la charge externe (Aide au transport/logement).")

    st.markdown("---")
    st.subheader("📋 Liste Prioritaire : Étudiants à Contacter")
    critical_df = df[df['Is_Critical'] == True].sort_values(by="Risk_Score", ascending=False)
    st.dataframe(critical_df[['Family_Income', 'External_Load', 'Attendance', 'Exam_Score', 'Risk_Score']], use_container_width=True)

except FileNotFoundError:
    st.error("⚠️ Erreur : 'cleaned_student_data.csv' non trouvé.")
