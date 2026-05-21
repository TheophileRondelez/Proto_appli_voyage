import random
import streamlit as st
import pandas as pd
# Importation de notre nouveau module de base de données
import database as db

# Configuration de la page
st.set_page_config(
    page_title="WorldPlanner - Votre voyage sur mesure",
    page_icon="✈️",
    layout="wide",
)

# Initialisation de la base de données (crée le fichier voyage.db s'il n'existe pas)
db.init_db()

# Style CSS personnalisé
st.markdown("""
    <style>
    .main-title { font-size: 2.6rem; font-weight: bold; color: #1E3A8A; margin-bottom: 0.5rem; }
    .subtitle { font-size: 1.2rem; color: #4B5563; margin-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">✈️ WorldPlanner AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Planifiez votre voyage sur mesure selon votre budget et vos envies</div>', unsafe_allow_html=True)

tab_planifier, tab_outils, tab_database = st.tabs([
    "🗺️ Planificateur de Voyage", 
    "🧮 Outils & Météo", 
    "🗄️ Structure Base de Données"
])

# ---------------------------------------------------------------------
# ONGLET 1 : LE PLANIFICATEUR DE VOYAGE
# ---------------------------------------------------------------------
with tab_planifier:
    st.header("Configurez vos critères de voyage")
    
    # Utilisation de la fonction du fichier externe pour récupérer les villes
    df_villes = db.exec_query("SELECT id, Nom FROM Ville")
    dict_villes = dict(zip(df_villes['Nom'], df_villes['id']))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ville_depart = st.selectbox("Aéroport de départ", ["Paris CDG"])
        ville_cible = st.selectbox("Destination souhaitée", list(dict_villes.keys()), index=3)
    with col2:
        nb_personnes = st.number_input("Nombre de voyageurs", min_value=1, value=1)
        duree_jours = st.number_input("Durée du séjour (jours)", min_value=1, max_value=30, value=5)
    with col3:
        budget_par_personne = st.number_input("Budget max / personne (€)", min_value=100, value=2000)
        gamme_confort = st.select_slider("Gamme de confort souhaitée", options=["Économique", "Normal", "Luxe"], value="Normal")
    with col4:
        interets = st.multiselect("Vos centres d'intérêt", ["Culture", "Détente", "Aventure", "Shopping"], default=["Culture", "Détente"])

    total_budget_alloue = budget_par_personne * nb_personnes
    st.info(f"💰 **Budget total disponible pour le groupe : {total_budget_alloue:,.2f} €**")
    
    if st.button("🚀 Générer mon itinéraire personnalisé", type="primary"):
        id_ville_cible = dict_villes[ville_cible]
        
        # 1. Recherche du Vol adapté via notre module BDD
        query_vol = """
            SELECT v.id, v.Prix, v.Type, a_dep.Nom as Dep, a_arr.Nom as Arr 
            FROM Vol v
            JOIN Aeroport a_dep ON v.Aéroport_de_départ = a_dep.id
            JOIN Aeroport a_arr ON v.Aéroport_d_arrivée = a_arr.id
            WHERE a_arr.Adresse = ? AND v.Type = ?
            LIMIT 1
        """
        df_vol_trouve = db.exec_query(query_vol, (id_ville_cible, gamme_confort))
        
        if df_vol_trouve.empty:
            df_vol_trouve = db.exec_query("""
                SELECT v.id, v.Prix, v.Type, a_dep.Nom as Dep, a_arr.Nom as Arr 
                FROM Vol v
                JOIN Aeroport a_dep ON v.Aéroport_de_départ = a_dep.id
                JOIN Aeroport a_arr ON v.Aéroport_d_arrivée = a_arr.id
                WHERE a_arr.Adresse = ? LIMIT 1
            """, (id_ville_cible,))

        # 2. Recherche de l'Hôtel adapté
        query_hotel = "SELECT * FROM Hotel WHERE Ville_id = ? AND Type = ? LIMIT 1"
        df_hotel_trouve = db.exec_query(query_hotel, (id_ville_cible, gamme_confort))
        if df_hotel_trouve.empty:
            df_hotel_trouve = db.exec_query("SELECT * FROM Hotel WHERE Ville_id = ? LIMIT 1", (id_ville_cible,))
            
        # 3. Recherche des Activités
        if interets:
            placeholders = ','.join(['?'] * len(interets))
            query_act = f"SELECT * FROM Activité WHERE Ville_id = ? AND Type IN ({placeholders})"
            params_act = [id_ville_cible] + interets
        else:
            query_act = "SELECT * FROM Activité WHERE Ville_id = ?"
            params_act = [id_ville_cible]

        df_activities = db.exec_query(query_act, params_act)

        # Calculs financiers et affichage
        st.markdown("---")
        st.subheader("📋 Votre Proposition de Voyage")
        
        cout_vols_total = df_vol_trouve.iloc[0]['Prix'] * nb_personnes * 2 if not df_vol_trouve.empty else 0
        cout_hotel_total = df_hotel_trouve.iloc[0]['Prix'] * (duree_jours - 1) * ((nb_personnes // 2) + 1) if not df_hotel_trouve.empty else 0

        liste_activites_planifiees = []
        cout_activites_total = 0
        if not df_activities.empty:
            max_act = min(len(df_activities), duree_jours * 2)
            df_selection_act = df_activities.sample(n=max_act, replace=len(df_activities) < max_act)
            for _, act in df_selection_act.iterrows():
                liste_activites_planifiees.append(act)
                cout_activites_total += act['Prix'] * nb_personnes

        cout_total_estime = cout_vols_total + cout_hotel_total + cout_activites_total
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Vols (Total Groupe AR)", f"{cout_vols_total:,.2f} €")
        c2.metric("Hôtel (Total Séjour)", f"{cout_hotel_total:,.2f} €")
        c3.metric("Activités (Total Groupe)", f"{cout_activites_total:,.2f} €")
        
        if cout_total_estime <= total_budget_alloue:
            c4.metric("Coût Total Estimé", f"{cout_total_estime:,.2f} €", delta="Dans le budget", delta_color="inverse")
            st.success("🎉 Excellente nouvelle ! Ce séjour respecte votre enveloppe budgétaire globale.")
        else:
            c4.metric("Coût Total Estimé", f"{cout_total_estime:,.2f} €", delta="Budget Dépassé", delta_color="normal")
            st.warning("⚠️ Attention : La configuration actuelle dépasse le budget.")

        col_gauche, col_droite = st.columns([2, 1])
        with col_gauche:
            st.markdown("### 🗓️ Votre Itinéraire Jour par Jour")
            if not df_vol_trouve.empty:
                st.markdown(f"**🛫 Jour 1 : Voyage Aller** — Vol {df_vol_trouve.iloc[0]['Type']} ({df_vol_trouve.iloc[0]['Prix']} € / pers)")
            
            for jour in range(1, duree_jours + 1):
                with st.expander(f"📍 Jour {jour}"):
                    if not df_hotel_trouve.empty:
                        st.write(f"🏨 **Hébergement :** {df_hotel_trouve.iloc[0]['Nom']}")
                    acts_du_jour = [liste_activites_planifiees.pop(0) for _ in range(min(2, len(liste_activites_planifiees)))] if liste_activites_planifiees else []
                    if acts_du_jour:
                        for a in acts_du_jour:
                            st.write(f"- ✨ **{a['Nom']}** — {a['Prix']} € (Type: {a['Type']})")
                    else:
                        st.write("🌿 *Journée libre.*")

        with col_droite:
            st.markdown("### 🗺️ Carte du Voyage")
            ville_geo = db.exec_query("SELECT Nom, lat, lon FROM Ville WHERE id = ?", (id_ville_cible,))
            if not ville_geo.empty:
                st.map(pd.DataFrame({'lat': [ville_geo.iloc[0]['lat']], 'lon': [ville_geo.iloc[0]['lon']]}), zoom=11)

# ---------------------------------------------------------------------
# ONGLET 2 : OUTILS APPLICATIFS
# ---------------------------------------------------------------------
with tab_outils:
    st.header("🧰 Outils Pratiques pour le Voyageur")
    col_meteo, col_devise = st.columns(2)
    
    with col_meteo:
        st.markdown("### ☀️ Météo en temps réel")
        ville_select_meteo = st.selectbox("Sélectionnez une ville pour voir la météo", list(dict_villes.keys()))
        info_meteo = db.exec_query("SELECT Météo FROM Ville WHERE Nom = ?", (ville_select_meteo,)).iloc[0]['Météo']
        st.info(f"**Météo actuelle à {ville_select_meteo} :** {info_meteo}")
        
    with col_devise:
        st.markdown("### 💱 Convertisseur de Devises Intégré")
        montant_eur = st.number_input("Montant en Euros (€)", min_value=1.0, value=100.0)
        devises_df = db.exec_query("SELECT * FROM Devise")
        taux_usd = devises_df.loc[devises_df['id'] == 2, 'EUR'].values[0]
        taux_jpy = devises_df.loc[devises_df['id'] == 3, 'EUR'].values[0]
        st.write(f"🇺🇸 **{montant_eur * taux_usd:.2f} USD**")
        st.write(f"🇯🇵 **{montant_eur * taux_jpy:.2f} JPY**")

# ---------------------------------------------------------------------
# ONGLET 3 : LE COIN TECHNIQUE
# ---------------------------------------------------------------------
with tab_database:
    st.header("🗄️ Inspection des tables de la Base de Données")
    table_choisie = st.selectbox("Choisissez une table à inspecter :", ["Pays", "Ville", "Hotel", "Activité", "Aeroport", "Vol", "Devise"])
    df_table = db.exec_query(f"SELECT * FROM {table_choisie}")
    st.dataframe(df_table, use_container_width=True)
