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

# Initialisation de la base de données (crée le fichier voyage.db s'il n'existe pas)
db.init_db()

# Style CSS personnalisé pour l'interface
st.markdown("""
    <style>
    .main-title { font-size: 2.6rem; font-weight: bold; color: #1E3A8A; margin-bottom: 0.5rem; }
    .subtitle { font-size: 1.2rem; color: #4B5563; margin-bottom: 2rem; }
    .stButton>button { width: 100%; }
    .legend { padding: 10px; font-size: 14px; background: white; border-radius: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.1); margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">✈️ WorldPlanner AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Planifiez votre voyage sur mesure selon votre budget, vos envies et visualisez vos activités</div>', unsafe_allow_html=True)

tab_planifier, tab_outils, tab_database = st.tabs([
    "🗺️ Planificateur & Carte", 
    "🧮 Outils & Météo", 
    "🗄️ Structure Base de Données"
])

# ---------------------------------------------------------------------
# ONGLET 1 : LE PLANIFICATEUR DE VOYAGE & CARTE INTERACTIVE
# ---------------------------------------------------------------------
with tab_planifier:
    st.header("Configurez vos critères de voyage")
    
    # Récupération des villes depuis la BDD pour alimenter le sélecteur
    df_villes = db.exec_query("SELECT id, Nom FROM Ville")
    dict_villes = dict(zip(df_villes['Nom'], df_villes['id']))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ville_depart = st.selectbox("Aéroport de départ", ["Paris CDG (LFPG)"])
        ville_cible = st.selectbox("Destination souhaitée", list(dict_villes.keys()), index=1) # New York par défaut
    with col2:
        nb_personnes = st.number_input("Nombre de voyageurs", min_value=1, value=1)
        duree_jours = st.number_input("Durée du séjour (jours)", min_value=1, max_value=30, value=5)
    with col3:
        budget_par_personne = st.number_input("Budget max / personne (€)", min_value=100, value=2000)
        gamme_confort = st.select_slider("Gamme de confort souhaitée", options=["Économique", "Normal", "Luxe"], value="Normal")
    with col4:
        interets = st.multiselect("Vos centres d'intérêt", ["Culture", "Détente", "Aventure", "Shopping"], default=["Culture", "Aventure"])

    total_budget_alloue = budget_par_personne * nb_personnes
    st.info(f"💰 **Budget total disponible pour le groupe : {total_budget_alloue:,.2f} €**")
    
    # Logique exécutée lors du clic sur le bouton
    if st.button("🚀 Générer mon itinéraire personnalisé", type="primary"):
        id_ville_cible = dict_villes[ville_cible]
        
        # 1. Recherche du Vol adapté
        query_vol = """
            SELECT v.Prix, v.Type, a_dep.Nom as Dep, a_arr.Nom as Arr 
            FROM Vol v
            JOIN Aeroport a_dep ON v.Aéroport_de_départ = a_dep.id
            JOIN Aeroport a_arr ON v.Aéroport_d_arrivée = a_arr.id
            WHERE a_arr.Adresse_Ville = ? AND v.Type = ?
            LIMIT 1
        """
        df_vol_trouve = db.exec_query(query_vol, (id_ville_cible, gamme_confort))
        if df_vol_trouve.empty:
            df_vol_trouve = db.exec_query("""
                SELECT v.Prix, v.Type, a_dep.Nom as Dep, a_arr.Nom as Arr 
                FROM Vol v
                JOIN Aeroport a_dep ON v.Aéroport_de_départ = a_dep.id
                JOIN Aeroport a_arr ON v.Aéroport_d_arrivée = a_arr.id
                WHERE a_arr.Adresse_Ville = ? LIMIT 1
            """, (id_ville_cible,))

        # 2. Recherche de l'Hôtel adapté
        query_hotel = "SELECT Nom, Adresse, Prix FROM Hotel WHERE Ville_id = ? AND Type = ? LIMIT 1"
        df_hotel_trouve = db.exec_query(query_hotel, (id_ville_cible, gamme_confort))
        if df_hotel_trouve.empty:
            df_hotel_trouve = db.exec_query("SELECT Nom, Adresse, Prix FROM Hotel WHERE Ville_id = ? LIMIT 1", (id_ville_cible,))
            
        # 3. Recherche des Activités géolocalisées
        if interets:
            placeholders = ','.join(['?'] * len(interets))
            query_act = f"SELECT Nom, Type, Prix, lat, lon FROM Activité WHERE Ville_id = ? AND Type IN ({placeholders})"
            params_act = [id_ville_cible] + interets
        else:
            query_act = "SELECT Nom, Type, Prix, lat, lon FROM Activité WHERE Ville_id = ?"
            params_act = [id_ville_cible]
        df_activities = db.exec_query(query_act, params_act)

        # 4. Construction et répartition du planning jour par jour
        planning = []
        if not df_activities.empty:
            max_act = min(len(df_activities), duree_jours * 3) # Maximum 3 activités par jour
            df_selection_act = df_activities.sample(n=max_act, replace=len(df_activities) < max_act)
            
            current_act_list = df_selection_act.to_dict('records')
            for jour in range(1, duree_jours + 1):
                num_acts = random.randint(1, 3) if current_act_list else 0
                acts_du_jour = [current_act_list.pop(0) for _ in range(min(num_acts, len(current_act_list)))]
                planning.append({"jour": jour, "activites": acts_du_jour})

        # Sauvegarde des résultats de la génération dans le state Session
        st.session_state.voyage_genere = {
            "ville": ville_cible,
            "id_ville": id_ville_cible,
            "vol": df_vol_trouve.iloc[0].to_dict() if not df_vol_trouve.empty else None,
            "hotel": df_hotel_trouve.iloc[0].to_dict() if not df_hotel_trouve.empty else None,
            "planning": planning,
            "nb_personnes": nb_personnes,
            "duree_jours": duree_jours,
            "total_budget_alloue": total_budget_alloue
        }

    # Affichage des résultats si le voyage existe en mémoire
    if 'voyage_genere' in st.session_state:
        data = st.session_state.voyage_genere
        
        # Calculs budgétaires globaux
        cout_vols_total = data['vol']['Prix'] * data['nb_personnes'] * 2 if data['vol'] else 0
        cout_hotel_total = data['hotel']['Prix'] * (data['duree_jours'] - 1) * data['nb_personnes'] if data['hotel'] else 0
        
        cout_activites_total = 0
        for j in data['planning']:
            for a in j['activites']:
                cout_activites_total += a['Prix'] * data['nb_personnes']
                
        cout_total_estime = cout_vols_total + cout_hotel_total + cout_activites_total
        
        # Métriques financières
        st.markdown("---")
        st.subheader("📋 Récapitulatif Budgétaire du Groupe")
        c_vol, c_hotel, c_act, c_tot = st.columns(4)
        c_vol.metric("Vols (Total AR Groupe)", f"{cout_vols_total:,.2f} €")
        c_hotel.metric("Hôtel (Total Séjour)", f"{cout_hotel_total:,.2f} €")
        c_act.metric("Activités (Total Groupe)", f"{cout_activites_total:,.2f} €")
        
        if cout_total_estime <= data['total_budget_alloue']:
            c_tot.metric("Coût Total Estimé", f"{cout_total_estime:,.2f} €", delta="Dans le budget", delta_color="inverse")
            st.success("🎉 Parfait ! Ce séjour respecte votre budget global.")
        else:
            c_tot.metric("Coût Total Estimé", f"{cout_total_estime:,.2f} €", delta="Budget Dépassé", delta_color="normal")
            st.warning("⚠️ Attention : La configuration actuelle dépasse votre enveloppe.")

        # Séparation de l'écran : Itinéraire textuel à gauche, Carte à droite
        col_gauche, col_droite = st.columns([1, 2])
        
        with col_gauche:
            st.markdown(f"### 🗓️ Itinéraire à {data['ville']}")
            if data['hotel']:
                st.info(f"🏨 **Hébergement sélectionné :**\n{data['hotel']['Nom']}\n({data['hotel']['Adresse']})")
            
            # Sélecteur de jour pour la mise à jour de la carte
            jours_dispos = [f"Jour {j['jour']}" for j in data['planning']]
            if jours_dispos:
                jour_selectionne_txt = st.radio("Sélectionnez un jour à afficher :", jours_dispos, horizontal=True)
                jour_selectionne_idx = int(jour_selectionne_txt.split(" ")[1]) - 1
                
                activities_display = data['planning'][jour_selectionne_idx]['activites']
                st.markdown(f"**Activités du {jour_selectionne_txt} :**")
                if activities_display:
                    for idx, a in enumerate(activities_display):
                        st.markdown(f"{idx+1}. ✨ **{a['Nom']}** — {a['Prix']} € *({a['Type']})*")
                else:
                    st.write("🌿 *Journée libre.*")
                
                # Sauvegarde temporaire des activités du jour sélectionné pour la carte
                data['current_acts_for_map'] = activities_display
            else:
                st.warning("Aucun itinéraire généré.")

        with col_droite:
            st.markdown("### 🗺️ Carte Interactive des Activités")
            
            # Récupération des coordonnées de la ville pour centrer la carte
            ville_geo = db.exec_query("SELECT lat, lon FROM Ville WHERE id = ?", (data['id_ville'],))
            if not ville_geo.empty:
                center_lat, center_lon = ville_geo.iloc[0]['lat'], ville_geo.iloc[0]['lon']
                
                # Création de la carte Folium de base
                m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="OpenStreetMap")
                
                colors_map = {
                    "Culture": "blue",
                    "Aventure": "red",
                    "Détente": "green",
                    "Shopping": "orange"
                }
                
                # Placement des marqueurs pour le jour sélectionné
                acts_to_map = data.get('current_acts_for_map', [])
                if acts_to_map:
                    coords_points = []
                    for idx, act in enumerate(acts_to_map):
                        color = colors_map.get(act['Type'], 'gray')
                        icon = folium.Icon(color=color, icon='info-sign')
                        
                        popup_html = f"""
                            <div style='width: 200px; font-family: Arial, sans-serif;'>
                                <b>{idx+1}. {act['Nom']}</b><br>
                                <span style='color:gray;'>Catégorie : {act['Type']}</span><br>
                                <b>Prix : {act['Prix']} €</b>
                            </div>
                        """
                        
                        folium.Marker(
                            [act['lat'], act['lon']],
                            popup=folium.Popup(popup_html, max_width=250),
                            tooltip=f"{idx+1}. {act['Nom']}",
                            icon=icon
                        ).add_to(m)
                        
                        coords_points.append([act['lat'], act['lon']])
                    
                    # Ajustement automatique des bordures pour englober tous les points
                    if coords_points:
                        m.fit_bounds(coords_points)

                # Rendu de la carte dans l'application Streamlit
                st_folium(m, width=None, height=480, returned_objects=[])
                
                # Légende des couleurs HTML
                legend_html = "<div class='legend'><b>Légende :</b> "
                for type_act, color in colors_map.items():
                    legend_html += f"<span style='color:{color};'>●</span> {type_act} &nbsp; "
                legend_html += "</div>"
                st.markdown(legend_html, unsafe_allow_html=True)
                
                # Bouton JavaScript d'impression natif du navigateur
                st.write("")
                if st.button("📥 Télécharger / Imprimer l'itinéraire et la carte"):
                    st.components.v1.html("<script>window.print();</script>", height=0, width=0)
                st.caption("💡 *Astuce : Pour enregistrer la carte et le planning en fichier, choisissez 'Enregistrer au format PDF' comme destination dans la fenêtre d'impression.*")
            else:
                st.error("Impossible de charger les coordonnées géographiques de la destination.")

# ---------------------------------------------------------------------
# ONGLET 2 : OUTILS & MÉTÉO
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
# ONGLET 3 : COIN TECHNIQUE / INSPECTION BDD
# ---------------------------------------------------------------------
with tab_database:
    st.header("🗄️ Inspection des tables de la Base de Données")
    st.markdown("Visualisez les données volumineuses actuellement injectées dans le fichier local `voyage.db`.")
    table_choisie = st.selectbox("Choisissez une table à inspecter :", ["Activité", "Hotel", "Ville", "Vol", "Pays", "Devise"])
    df_table = db.exec_query(f"SELECT * FROM {table_choisie}")
    st.dataframe(df_table, use_container_width=True)
