import random
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
# Import du plugin pour l'impression/téléchargement
from folium.plugins import Print
import database as db

# Configuration de la page
st.set_page_config(
    page_title="WorldPlanner - Votre itinéraire cartographié",
    page_icon="🗺️",
    layout="wide",
)

# Initialisation de la base de données (si nécessaire)
db.init_db()

# Style CSS pour une interface plus propre
st.markdown("""
    <style>
    .main-title { font-size: 2.6rem; font-weight: bold; color: #1E3A8A; margin-bottom: 0.5rem; }
    .subtitle { font-size: 1.2rem; color: #4B5563; margin-bottom: 1.5rem; }
    .stButton>button { width: 100%; }
    /* Style pour la légende de la carte */
    .legend { padding: 10px; font-size: 14px; background: white; border-radius: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.2); }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">✈️ WorldPlanner AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Votre voyage sur mesure avec carte des activités interactive</div>', unsafe_allow_html=True)

tab_planifier, tab_outils = st.tabs(["🗺️ Planificateur & Carte", "🧮 Outils & BDD"])

# ---------------------------------------------------------------------
# ONGLET 1 : LE PLANIFICATEUR & LA CARTE INTERACTIVE
# ---------------------------------------------------------------------
with tab_planifier:
    
    # 1. FORMULAIRE DE CRITÈRES
    st.header("Configurez vos critères de voyage")
    df_villes = db.exec_query("SELECT id, Nom FROM Ville")
    dict_villes = dict(zip(df_villes['Nom'], df_villes['id']))
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ville_cible = st.selectbox("Destination souhaitée", list(dict_villes.keys()), index=1) # NY par défaut
    with c2:
        nb_personnes = st.number_input("Voyageurs", min_value=1, value=1)
        duree_jours = st.number_input("Durée (jours)", min_value=1, max_value=30, value=5)
    with c3:
        gamme_confort = st.select_slider("Gamme de confort", options=["Économique", "Normal", "Luxe"], value="Normal")
    with c4:
        interets = st.multiselect("Intérêts", ["Culture", "Détente", "Aventure", "Shopping"], default=["Culture", "Aventure"])

    st.markdown("---")
    
    # 2. LOGIQUE DE GÉNÉRATION (Stockée dans session_state pour persisté au clic)
    if st.button("🚀 Générer mon itinéraire personnalisé", type="primary"):
        id_ville_cible = dict_villes[ville_cible]
        
        # Recherche de l'Hôtel
        query_hotel = "SELECT Nom, Adresse FROM Hotel WHERE Ville_id = ? AND Type = ? LIMIT 1"
        df_hotel_trouve = db.exec_query(query_hotel, (id_ville_cible, gamme_confort))
        if df_hotel_trouve.empty:
            df_hotel_trouve = db.exec_query("SELECT Nom, Adresse FROM Hotel WHERE Ville_id = ? LIMIT 1", (id_ville_cible,))
            
        # Recherche des Activités géo-localisées
        if interets:
            placeholders = ','.join(['?'] * len(interets))
            query_act = f"SELECT Nom, Type, Prix, lat, lon FROM Activité WHERE Ville_id = ? AND Type IN ({placeholders})"
            params_act = [id_ville_cible] + interets
        else:
            query_act = "SELECT Nom, Type, Prix, lat, lon FROM Activité WHERE Ville_id = ?"
            params_act = [id_ville_cible]
        df_activities = db.exec_query(query_act, params_act)

        # Construction du planning jour par jour
        planning = []
        if not df_activities.empty:
            # On prend un échantillon aléatoire pour varier
            max_act = min(len(df_activities), duree_jours * 3) # Max 3 par jour
            df_selection_act = df_activities.sample(n=max_act, replace=len(df_activities) < max_act)
            
            # Répartition des activités
            current_act_list = df_selection_act.to_dict('records')
            for jour in range(1, duree_jours + 1):
                num_acts = random.randint(1, 3) if current_act_list else 0
                acts_du_jour = [current_act_list.pop(0) for _ in range(min(num_acts, len(current_act_list)))]
                planning.append({"jour": jour, "activites": acts_du_jour})
        
        # Sauvegarde dans le state pour l'affichage
        st.session_state.voyage_genere = {
            "ville": ville_cible,
            "id_ville": id_ville_cible,
            "hotel": df_hotel_trouve.iloc[0].to_dict() if not df_hotel_trouve.empty else None,
            "planning": planning
        }

    # 3. AFFICHAGE DES RÉSULTATS ET DE LA CARTE
    if 'voyage_genere' in st.session_state:
        data = st.session_state.voyage_genere
        
        col_gauche, col_droite = st.columns([1, 2])
        
        with col_gauche:
            st.markdown(f"### 🗓️ Itinéraire à {data['ville']}")
            if data['hotel']:
                st.info(f"🏨 **Hôtel :** {data['hotel']['Nom']}\n({data['hotel']['Adresse']})")
            
            # Affichage du planning et sélection du jour pour la carte
            jours_dispos = [f"Jour {j['jour']}" for j in data['planning']]
            if jours_dispos:
                jour_selectionne_txt = st.radio("Sélectionnez un jour pour voir les activités sur la carte :", jours_dispos, horizontal=True)
                jour_selectionne_idx = int(jour_selectionne_txt.split(" ")[1]) - 1
                
                activities_display = data['planning'][jour_selectionne_idx]['activites']
                if activities_display:
                    for a in activities_display:
                        st.markdown(f"- ✨ **{a['Nom']}** — {a['Prix']} € (Type: {a['Type']})")
                else:
                    st.write("🌿 *Journée libre.*")
                
                # Sauvegarde du jour sélectionné pour la carte
                data['current_acts_for_map'] = activities_display
            else:
                st.warning("Aucune activité trouvée pour ces critères.")

        with col_droite:
            st.markdown("### 🗺️ Carte Interactive du Jour Sélectionné")
            
            # Coordonnées de la ville (centre)
            ville_geo = db.exec_query("SELECT lat, lon FROM Ville WHERE id = ?", (data['id_ville'],))
            if not ville_geo.empty:
                center_lat, center_lon = ville_geo.iloc[0]['lat'], ville_geo.iloc[0]['lon']
                
                # Création de la carte Folium (fond OpenStreetMap)
                m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="OpenStreetMap")
                
                # Ajout du plugin d'impression/téléchargement (bouton en haut à gauche)
                Print().add_to(m)
                
                # Définition des couleurs par type d'activité
                colors_map = {
                    "Culture": "blue",
                    "Aventure": "red",
                    "Détente": "green",
                    "Shopping": "orange"
                }
                
                # Ajout des marqueurs pour les activités du jour
                acts_to_map = data.get('current_acts_for_map', [])
                if acts_to_map:
                    # Pour ajuster le zoom aux points
                    coords_points = []
                    
                    for idx, act in enumerate(acts_to_map):
                        color = colors_map.get(act['Type'], 'gray')
                        icon = folium.Icon(color=color, icon='info-sign')
                        
                        # Création du Popup HTML
                        popup_html = f"""
                            <div style='width: 200px;'>
                                <b>{idx+1}. {act['Nom']}</b><br>
                                <i>Type : {act['Type']}</i><br>
                                Coût : {act['Prix']} €
                            </div>
                        """
                        
                        folium.Marker(
                            [act['lat'], act['lon']],
                            popup=folium.Popup(popup_html, max_width=250),
                            tooltip=f"{idx+1}. {act['Nom']}",
                            icon=icon
                        ).add_to(m)
                        
                        coords_points.append([act['lat'], act['lon']])
                    
                    # Ajustement automatique du zoom pour voir tous les points
                    if coords_points:
                        m.fit_bounds(coords_points)

                # Affichage de la carte dans Streamlit
                # Note: `returned_objects=[]` évite les rechargements inutiles au clic sur un marqueur
                st_folium(m, width=None, height=500, returned_objects=[])
                
                # Petite légende manuelle en HTML
                legend_html = "<div class='legend'><b>Légende :</b> "
                for type_act, color in colors_map.items():
                    legend_html += f"<span style='color:{color};'>●</span> {type_act} &nbsp; "
                legend_html += "</div>"
                st.markdown(legend_html, unsafe_allow_html=True)
                st.write("💡 *Cliquez sur le bouton d'imprimante (en haut à gauche de la carte) pour la télécharger en PDF ou Image via la boîte de dialogue d'impression de votre navigateur.*")

            else:
                st.error("Données géographiques de la ville manquantes.")

# ---------------------------------------------------------------------
# ONGLET 2 : OUTILS APPLICATIFS
# ---------------------------------------------------------------------
with tab_outils:
    st.header("🧰 Outils & Base de Données")
    st.markdown("Inspection des tables pour vérifier l'injection massive de données géolocalisées.")
    
    table_choisie = st.selectbox("Choisissez une table à inspecter :", ["Activité", "Hotel", "Ville", "Vol", "Devise"])
    df_table = db.exec_query(f"SELECT * FROM {table_choisie}")
    st.dataframe(df_table, use_container_width=True)
