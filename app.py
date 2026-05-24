import random
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import database as db

# Configuration de la page
st.set_page_config(
    page_title="WorldPlanner - Votre voyage sur mesure",
    page_icon="✈️",
    layout="wide",
)

# Initialisation de la base de données
db.init_db()

# Initialisation des variables d'étape dans le Session State
if 'etape' not in st.session_state:
    st.session_state.etape = 1
if 'form_data' not in st.session_state:
    st.session_state.form_data = {}

# Style CSS personnalisé
st.markdown("""
    <style>
    .main-title { font-size: 2.6rem; font-weight: bold; color: #1E3A8A; margin-bottom: 0.5rem; }
    .subtitle { font-size: 1.2rem; color: #4B5563; margin-bottom: 2rem; }
    .stButton>button { width: 100%; }
    .legend { padding: 10px; font-size: 14px; background: white; border-radius: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.1); margin-top: 10px; }
    .step-indicator { font-weight: bold; color: #1E3A8A; margin-bottom: 10px; font-size: 1.1rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">✈️ WorldPlanner AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Créez votre voyage sur mesure via notre configurateur étape par étape</div>', unsafe_allow_html=True)

tab_planifier, tab_outils, tab_database = st.tabs([
    "🗺️ Planificateur Séquentiel", 
    "🧮 Outils & Météo", 
    "🗄️ Structure Base de Données"
])

# Récupération des villes pour le besoin global
df_villes = db.exec_query("SELECT id, Nom FROM Ville")
dict_villes = dict(zip(df_villes['Nom'], df_villes['id']))

# ---------------------------------------------------------------------
# ONGLET 1 : PLANIFICATEUR EN PLUSIEURS ÉTAPES
# ---------------------------------------------------------------------
with tab_planifier:
    
    # On n'affiche le formulaire que si on n'a pas encore validé les résultats finaux
    if 'voyage_genere' not in st.session_state:
        st.header("Configurez votre séjour")
        
        # --- ÉTAPE 1 : DESTINATION ---
        if st.session_state.etape == 1:
            st.markdown('<div class="step-indicator">📌 Étape 1 sur 4 : Choisissez votre destination</div>', unsafe_allow_html=True)
            st.progress(0.25)
            ville_depart = st.selectbox("Aéroport de départ", ["Paris CDG (LFPG)"])
            ville_cible = st.selectbox("Destination souhaitée", list(dict_villes.keys()), index=1)
            
            if st.button("Suivant ➡️", type="primary"):
                st.session_state.form_data['ville_cible'] = ville_cible
                st.session_state.etape = 2
                st.rerun()

        # --- ÉTAPE 2 : PARTICIPANTS & DURÉE ---
        elif st.session_state.etape == 2:
            st.markdown('<div class="step-indicator">👥 Étape 2 sur 4 : Qui voyage et combien de temps ?</div>', unsafe_allow_html=True)
            st.progress(0.50)
            nb_personnes = st.number_input("Nombre de voyageurs", min_value=1, value=1)
            duree_jours = st.number_input("Durée du séjour (jours)", min_value=1, max_value=30, value=5)
            
            c_back, c_next = st.columns(2)
            with c_back:
                if st.button("⬅️ Retour"):
                    st.session_state.etape = 1
                    st.rerun()
            with c_next:
                if st.button("Suivant ➡️", type="primary"):
                    st.session_state.form_data['nb_personnes'] = nb_personnes
                    st.session_state.form_data['duree_jours'] = duree_jours
                    st.session_state.etape = 3
                    st.rerun()

        # --- ÉTAPE 3 : BUDGET & CONFORT ---
        elif st.session_state.etape == 3:
            st.markdown('<div class="step-indicator">💰 Étape 3 sur 4 : Budget & Confort</div>', unsafe_allow_html=True)
            st.progress(0.75)
            budget_par_personne = st.number_input("Budget max par personne (€)", min_value=100, value=2000)
            gamme_confort = st.select_slider("Gamme de confort souhaitée", options=["Économique", "Normal", "Luxe"], value="Normal")
            
            c_back, c_next = st.columns(2)
            with c_back:
                if st.button("⬅️ Retour"):
                    st.session_state.etape = 2
                    st.rerun()
            with c_next:
                if st.button("Suivant ➡️", type="primary"):
                    st.session_state.form_data['budget_par_personne'] = budget_par_personne
                    st.session_state.form_data['gamme_confort'] = gamme_confort
                    st.session_state.etape = 4
                    st.rerun()

        # --- ÉTAPE 4 : INTÉRÊTS & GÉNÉRATION ---
        elif st.session_state.etape == 4:
            st.markdown('<div class="step-indicator">🎭 Étape 4 sur 4 : Vos centres d\'intérêt</div>', unsafe_allow_html=True)
            st.progress(1.0)
            interets = st.multiselect("Sélectionnez vos thématiques préférées", ["Culture", "Détente", "Aventure", "Shopping"], default=["Culture", "Aventure"])
            
            # Rappel des choix précédents avant validation
            fd = st.session_state.form_data
            st.caption(f"Résumé : {fd['nb_personnes']} pers. à {fd['ville_cible']} pendant {fd['duree_jours']} jours ({fd['gamme_confort']})")
            
            c_back, c_next = st.columns(2)
            with c_back:
                if st.button("⬅️ Retour"):
                    st.session_state.etape = 3
                    st.rerun()
            with c_next:
                if st.button("🚀 Générer mon voyage personnalisé !", type="primary"):
                    # Récupération de toutes les données accumulées
                    v_cible = fd['ville_cible']
                    id_ville_cible = dict_villes[v_cible]
                    n_pers = fd['nb_personnes']
                    d_jours = fd['duree_jours']
                    g_confort = fd['gamme_confort']
                    tot_budget = fd['budget_par_personne'] * n_pers

                    # 1. Requête Vol
                    query_vol = """
                        SELECT v.Prix, v.Type FROM Vol v
                        JOIN Aeroport a_arr ON v.Aéroport_d_arrivée = a_arr.id
                        WHERE a_arr.Adresse_Ville = ? AND v.Type = ? LIMIT 1
                    """
                    df_vol_trouve = db.exec_query(query_vol, (id_ville_cible, g_confort))
                    if df_vol_trouve.empty:
                        df_vol_trouve = db.exec_query("SELECT v.Prix, v.Type FROM Vol v JOIN Aeroport a_arr ON v.Aéroport_d_arrivée = a_arr.id WHERE a_arr.Adresse_Ville = ? LIMIT 1", (id_ville_cible,))

                    # 2. Requête Hôtel
                    query_hotel = "SELECT Nom, Adresse, Prix FROM Hotel WHERE Ville_id = ? AND Type = ? LIMIT 1"
                    df_hotel_trouve = db.exec_query(query_hotel, (id_ville_cible, g_confort))
                    if df_hotel_trouve.empty:
                        df_hotel_trouve = db.exec_query("SELECT Nom, Adresse, Prix FROM Hotel WHERE Ville_id = ? LIMIT 1", (id_ville_cible,))
                        
                    # 3. Requête Activités
                    if interets:
                        placeholders = ','.join(['?'] * len(interets))
                        query_act = f"SELECT Nom, Type, Prix, lat, lon FROM Activité WHERE Ville_id = ? AND Type IN ({placeholders})"
                        params_act = [id_ville_cible] + interets
                    else:
                        query_act = "SELECT Nom, Type, Prix, lat, lon FROM Activité WHERE Ville_id = ?"
                        params_act = [id_ville_cible]
                    df_activities = db.exec_query(query_act, params_act)

                    # 4. Dispatching des activités par jour
                    planning = []
                    if not df_activities.empty:
                        max_act = min(len(df_activities), d_jours * 3)
                        df_selection_act = df_activities.sample(n=max_act, replace=len(df_activities) < max_act)
                        current_act_list = df_selection_act.to_dict('records')
                        for jour in range(1, d_jours + 1):
                            num_acts = random.randint(1, 3) if current_act_list else 0
                            acts_du_jour = [current_act_list.pop(0) for _ in range(min(num_acts, len(current_act_list)))]
                            planning.append({"jour": jour, "activites": acts_du_jour})

                    # Stockage complet pour l'affichage final
                    st.session_state.voyage_genere = {
                        "ville": v_cible,
                        "id_ville": id_ville_cible,
                        "vol": df_vol_trouve.iloc[0].to_dict() if not df_vol_trouve.empty else None,
                        "hotel": df_hotel_trouve.iloc[0].to_dict() if not df_hotel_trouve.empty else None,
                        "planning": planning,
                        "nb_personnes": n_pers,
                        "duree_jours": d_jours,
                        "total_budget_alloue": tot_budget
                    }
                    st.rerun()

    # --- AFFICHAGE DES RÉSULTATS (Une fois le bouton final pressé) ---
    else:
        data = st.session_state.voyage_genere
        
        # Bouton pour réinitialiser le questionnaire et refaire une recherche
        if st.button("🔄 Recommencer une nouvelle recherche", help="Efface les données actuelles"):
            del st.session_state.voyage_genere
            st.session_state.etape = 1
            st.session_state.form_data = {}
            st.rerun()
            
        # Calcul des totaux
        cout_vols_total = data['vol']['Prix'] * data['nb_personnes'] * 2 if data['vol'] else 0
        cout_hotel_total = data['hotel']['Prix'] * (data['duree_jours'] - 1) * data['nb_personnes'] if data['hotel'] else 0
        cout_activites_total = sum(a['Prix'] * data['nb_personnes'] for j in data['planning'] for a in j['activites'])
        cout_total_estime = cout_vols_total + cout_hotel_total + cout_activites_total
        
        st.markdown("---")
        st.subheader(f"📋 Votre Proposition de Voyage pour {data['ville']}")
        
        c_vol, c_hotel, c_act, c_tot = st.columns(4)
        c_vol.metric("Vols (AR Groupe)", f"{cout_vols_total:,.2f} €")
        c_hotel.metric("Hôtel (Séjour)", f"{cout_hotel_total:,.2f} €")
        c_act.metric("Activités (Groupe)", f"{cout_activites_total:,.2f} €")
        
        if cout_total_estime <= data['total_budget_alloue']:
            c_tot.metric("Coût Total", f"{cout_total_estime:,.2f} €", delta="Dans le budget", delta_color="inverse")
            st.success("🎉 Ce séjour respecte parfaitement votre enveloppe budgétaire.")
        else:
            c_tot.metric("Coût Total", f"{cout_total_estime:,.2f} €", delta="Budget Dépassé", delta_color="normal")
            st.warning("⚠️ Configuration actuelle au-dessus de votre budget initial.")

        col_gauche, col_droite = st.columns([1, 2])
        with col_gauche:
            st.markdown(f"### 🗓️ Déroulé du Séjour")
            if data['hotel']:
                st.info(f"🏨 **Hôtel retenu :** {data['hotel']['Nom']}\n({data['hotel']['Adresse']})")
            
            jours_dispos = [f"Jour {j['jour']}" for j in data['planning']]
            if jours_dispos:
                jour_selectionne_txt = st.radio("Choisir le jour à cartographier :", jours_dispos, horizontal=True)
                jour_selectionne_idx = int(jour_selectionne_txt.split(" ")[1]) - 1
                
                activities_display = data['planning'][jour_selectionne_idx]['activites']
                st.markdown(f"**Activités du {jour_selectionne_txt} :**")
                if activities_display:
                    for idx, a in enumerate(activities_display):
                        st.markdown(f"{idx+1}. ✨ **{a['Nom']}** — {a['Prix']} € *({a['Type']})*")
                else:
                    st.write("🌿 *Journée libre.*")
                data['current_acts_for_map'] = activities_display

        with col_droite:
            st.markdown("### 🗺️ Carte Interactive")
            ville_geo = db.exec_query("SELECT lat, lon FROM Ville WHERE id = ?", (data['id_ville'],))
            if not ville_geo.empty:
                center_lat, center_lon = ville_geo.iloc[0]['lat'], ville_geo.iloc[0]['lon']
                m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="OpenStreetMap")
                
                colors_map = {"Culture": "blue", "Aventure": "red", "Détente": "green", "Shopping": "orange"}
                acts_to_map = data.get('current_acts_for_map', [])
                
                if acts_to_map:
                    coords_points = []
                    for idx, act in enumerate(acts_to_map):
                        color = colors_map.get(act['Type'], 'gray')
                        icon = folium.Icon(color=color, icon='info-sign')
                        popup_html = f"<div style='width:200px;'><b>{idx+1}. {act['Nom']}</b><br>Prix: {act['Prix']} €</div>"
                        
                        folium.Marker(
                            [act['lat'], act['lon']],
                            popup=folium.Popup(popup_html, max_width=250),
                            tooltip=act['Nom'],
                            icon=icon
                        ).add_to(m)
                        coords_points.append([act['lat'], act['lon']])
                    
                    if coords_points:
                        m.fit_bounds(coords_points)

                st_folium(m, width=None, height=450, returned_objects=[])
                
                legend_html = "<div class='legend'><b>Légende :</b> "
                for type_act, color in colors_map.items():
                    legend_html += f"<span style='color:{color};'>●</span> {type_act} &nbsp; "
                legend_html += "</div>"
                st.markdown(legend_html, unsafe_allow_html=True)
                
                st.write("")
                if st.button("📥 Télécharger / Imprimer l'itinéraire et la carte"):
                    st.components.v1.html("<script>window.print();</script>", height=0, width=0)

# ---------------------------------------------------------------------
# ONGLETS SÉCURITAIRES (Inchangés)
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

with tab_database:
    st.header("🗄️ Inspection des tables de la Base de Données")
    table_choisie = st.selectbox("Choisissez une table à inspecter :", ["Activité", "Hotel", "Ville", "Vol"])
    df_table = db.exec_query(f"SELECT * FROM {table_choisie}")
    st.dataframe(df_table, use_container_width=True)
