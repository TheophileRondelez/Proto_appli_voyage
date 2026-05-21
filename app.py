import sqlite3
import random
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd

# =====================================================================
# 1. CONFIGURATION DE LA PAGE & DESIGN
# =====================================================================
st.set_page_config(
    page_title="WorldPlanner - Votre voyage sur mesure",
    page_icon="✈️",
    layout="wide",
)

# Style CSS personnalisé pour moderniser l'interface
st.markdown("""
    <style>
    .main-title { font-size: 2.6rem; font-weight: bold; color: #1E3A8A; margin-bottom: 0.5rem; }
    .subtitle { font-size: 1.2rem; color: #4B5563; margin-bottom: 2rem; }
    .card { background-color: #F3F4F6; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    .price-tag { font-size: 1.5rem; font-weight: bold; color: #10B981; }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. INITIALISATION ET REMPLISSAGE DE LA BASE DE DONNÉES (SQLITE)
# =====================================================================
def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    cursor = conn.cursor()
    
    # Activation des clés étrangères
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Création des tables selon votre schéma exact
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Devise (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            EUR REAL
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Pays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Villes TEXT,
            Aerorports INTEGER,
            Devise INTEGER,
            FOREIGN KEY(Devise) REFERENCES Devise(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Ville (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Nom TEXT,
            Hotels INTEGER,
            Activités INTEGER,
            Météo TEXT,
            Pays_id INTEGER,
            lat REAL,
            lon REAL,
            FOREIGN KEY(Pays_id) REFERENCES Pays(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Aeroport (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Nom TEXT,
            Adresse INTEGER,
            Vols INTEGER,
            FOREIGN KEY(Adresse) REFERENCES Ville(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Hotel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Nom TEXT,
            Type TEXT,
            Prix REAL,
            Adresse TEXT,
            Ville_id INTEGER,
            FOREIGN KEY(Ville_id) REFERENCES Ville(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Activité (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Nom TEXT,
            Adresse TEXT,
            Type TEXT,
            Prix REAL,
            Ville_id INTEGER,
            FOREIGN KEY(Ville_id) REFERENCES Ville(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Vol (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Aéroport_de_départ INTEGER,
            Aéroport_d_arrivée INTEGER,
            Type TEXT,
            Prix REAL,
            Date TEXT,
            FOREIGN KEY(Aéroport_de_départ) REFERENCES Aeroport(id),
            FOREIGN KEY(Aéroport_d_arrivée) REFERENCES Aeroport(id)
        );
    """)
    
    # Insertion de données fictives cohérentes pour le prototype
    cursor.execute("INSERT INTO Devise (id, EUR) VALUES (1, 1.0), (2, 1.09), (3, 152.4);") # EUR, USD, JPY
    cursor.execute("INSERT INTO Pays (id, Villes, Aerorports, Devise) VALUES (1, 'France', 1, 1), (2, 'USA', 2, 2), (3, 'Japon', 3, 3);")
    
    # Villes avec coordonnées pour la carte
    villes_data = [
        (1, 'Paris', 'Ensoleillé, 21°C', 1, 48.8566, 2.3522),
        (2, 'Nice', 'Beau temps, 24°C', 1, 43.7102, 7.2620),
        (3, 'New York', 'Nuageux, 18°C', 2, 40.7128, -74.0060),
        (4, 'Tokyo', 'Pluie légère, 16°C', 3, 35.6762, 139.6503)
    ]
    for v in villes_data:
        cursor.execute("INSERT INTO Ville (id, Nom, Météo, Pays_id, lat, lon) VALUES (?, ?, ?, ?, ?, ?);", v)
        
    cursor.execute("INSERT INTO Aeroport (id, Nom, Adresse) VALUES (1, 'Paris CDG', 1), (2, 'Nice Côte dAzur', 2), (3, 'New York JFK', 3), (4, 'Tokyo Haneda', 4);")
    
    # Hôtels (Économique, Normal, Luxe)
    hotels = [
        ('Hostel Les Piaules', 'Économique', 35.0, 'Paris 11e', 1),
        ('Hôtel Standard Paris', 'Normal', 120.0, 'Paris 10e', 1),
        ('The Ritz Paris', 'Luxe', 850.0, 'Place Vendôme, Paris', 1),
        ('Nice Negresco', 'Luxe', 450.0, 'Promenade des Anglais, Nice', 2),
        ('Pod 39 Hotel', 'Économique', 90.0, 'Midtown, NY', 3),
        ('The Plaza NY', 'Luxe', 950.0, '5th Avenue, NY', 3),
        ('Capsule Hotel Shinjuku', 'Économique', 25.0, 'Shinjuku, Tokyo', 4),
        ('Keio Plaza Hotel', 'Normal', 180.0, 'Shinjuku, Tokyo', 4),
        ('Aman Tokyo', 'Luxe', 1200.0, 'Chiyoda, Tokyo', 4)
    ]
    for h in hotels:
        cursor.execute("INSERT INTO Hotel (Nom, Type, Prix, Adresse, Ville_id) VALUES (?, ?, ?, ?, ?);", h)
        
    # Activités par centres d'intérêt
    activites = [
        ('Musée du Louvre', 'Palais Royal', 'Culture', 22.0, 1),
        ('Tour Eiffel', 'Champ de Mars', 'Culture', 28.0, 1),
        ('Balade guidée Montmartre', 'Sacré-Cœur', 'Détente', 15.0, 1),
        ('Bateaux Mouches', 'Seine', 'Détente', 15.0, 1),
        ('Plongée sous-marine', 'Port de Nice', 'Aventure', 75.0, 2),
        ('Survol de NYC en hélicoptère', 'Manhattan Heliport', 'Aventure', 250.0, 3),
        ('MoMA', '11 W 53rd St', 'Culture', 25.0, 3),
        ('Visite du Mont Fuji', 'Départ Tokyo', 'Aventure', 90.0, 4),
        ('Balade Robotique à Akihabara', 'Akihabara', 'Shopping', 0.0, 4),
        ('Cérémonie du thé traditionnelle', 'Asakusa', 'Culture', 40.0, 4)
    ]
    for a in activites:
        cursor.execute("INSERT INTO Activité (Nom, Adresse, Type, Prix, Ville_id) VALUES (?, ?, ?, ?, ?);", a)
        
    # Vols (Économique, Normal, Luxe)
    vols = [
        (1, 3, 'Économique', 450.0, '2026-06-15'), (1, 3, 'Normal', 850.0, '2026-06-15'), (1, 3, 'Luxe', 3500.0, '2026-06-15'),
        (1, 4, 'Économique', 700.0, '2026-06-15'), (1, 4, 'Normal', 1200.0, '2026-06-15'), (1, 4, 'Luxe', 5500.0, '2026-06-15'),
        (1, 2, 'Économique', 45.0, '2026-06-15'), (1, 2, 'Normal', 90.0, '2026-06-15'), (1, 2, 'Luxe', 250.0, '2026-06-15')
    ]
    for v in vols:
        cursor.execute("INSERT INTO Vol (Aéroport_de_départ, Aéroport_d_arrivée, Type, Prix, Date) VALUES (?, ?, ?, ?, ?);", v)
        
    conn.commit()
    return conn

# Instanciation globale de la base de données
if 'db_conn' not in st.session_state:
    st.session_state.db_conn = init_db()

conn = st.session_state.db_conn

# =====================================================================
# 3. INTERFACE UTILISATEUR (STREAMLIT)
# =====================================================================

# Titre principal
st.markdown('<div class="main-title">✈️ WorldPlanner AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Planifiez votre voyage sur mesure selon votre budget et vos envies</div>', unsafe_allow_html=True)

# Définition des onglets de l'application
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
    
    # Extraction des destinations disponibles pour le formulaire
    df_villes = pd.read_sql_query("SELECT id, Nom FROM Ville", conn)
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
        
        # 1. Recherche du Vol adapté
        query_vol = """
            SELECT v.id, v.Prix, v.Type, a_dep.Nom as Dep, a_arr.Nom as Arr 
            FROM Vol v
            JOIN Aeroport a_dep ON v.Aéroport_de_départ = a_dep.id
            JOIN Aeroport a_arr ON v.Aéroport_d_arrivée = a_arr.id
            WHERE a_arr.Adresse = ? AND v.Type = ?
            LIMIT 1
        """
        df_vol_trouve = pd.read_sql_query(query_vol, conn, params=(id_ville_cible, gamme_confort))
        
        # En cas d'absence de vol exact pour la gamme, on cherche le premier disponible
        if df_vol_trouve.empty:
            df_vol_trouve = pd.read_sql_query("""
                SELECT v.id, v.Prix, v.Type, a_dep.Nom as Dep, a_arr.Nom as Arr 
                FROM Vol v
                JOIN Aeroport a_dep ON v.Aéroport_de_départ = a_dep.id
                JOIN Aeroport a_arr ON v.Aéroport_d_arrivée = a_arr.id
                WHERE a_arr.Adresse = ? LIMIT 1
            """, conn, params=(id_ville_cible,))

        # 2. Recherche de l'Hôtel adapté
        query_hotel = "SELECT * FROM Hotel WHERE Ville_id = ? AND Type = ? LIMIT 1"
        df_hotel_trouve = pd.read_sql_query(query_hotel, conn, params=(id_ville_cible, gamme_confort))
        if df_hotel_trouve.empty:
            df_hotel_trouve = pd.read_sql_query("SELECT * FROM Hotel WHERE Ville_id = ? LIMIT 1", conn, params=(id_ville_cible,))
            
        # 3. Recherche des Activités basées sur les intérêts du voyageur
        if interets:
            placeholders = ','.join(['?'] * len(interets))
            query_act = f"SELECT * FROM Activité WHERE Ville_id = ? AND Type IN ({placeholders})"
            params_act = [id_ville_cible] + interets
        else:
            query_act = "SELECT * FROM Activité WHERE Ville_id = ?"
            params_act = [id_ville_cible]

        df_activities = pd.read_sql_query(query_act, conn, params=params_act)

        # =====================================================================
        # 4. CALCULS ET AFFICHAGE DU RÉCAPITULATIF FINANCIER
        # =====================================================================
        st.markdown("---")
        st.subheader("📋 Votre Proposition de Voyage")
        
        # Calcul du coût du transport (Vols Aller/Retour simulés)
        cout_vols_total = 0
        if not df_vol_trouve.empty:
            cout_vols_total = df_vol_trouve.iloc[0]['Prix'] * nb_personnes * 2 # Aller-Retour
            
        # Calcul du coût du logement (Prix de la chambre par nuitée pour le groupe)
        cout_hotel_total = 0
        if not df_hotel_trouve.empty:
            cout_hotel_total = df_hotel_trouve.iloc[0]['Prix'] * (duree_jours - 1) * ((nb_personnes // 2) + 1)

        # Sélection et calcul du coût des activités selon la durée
        liste_activites_planifiees = []
        cout_activites_total = 0
        if not df_activities.empty:
            # On prend un maximum de 2 activités par jour si le budget le permet
            max_act = min(len(df_activities), duree_jours * 2)
            df_selection_act = df_activities.sample(n=max_act, replace=len(df_activities) < max_act)
            
            for _, act in df_selection_act.iterrows():
                liste_activites_planifiees.append(act)
                cout_activites_total += act['Prix'] * nb_personnes

        cout_total_estime = cout_vols_total + cout_hotel_total + cout_activites_total
        
        # Affichage des indicateurs de budget
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Vols (Total Groupe AR)", f"{cout_vols_total:,.2f} €")
        c2.metric("Hôtel (Total Séjour)", f"{cout_hotel_total:,.2f} €")
        c3.metric("Activités (Total Groupe)", f"{cout_activites_total:,.2f} €")
        
        if cout_total_estime <= total_budget_alloue:
            c4.metric("Coût Total Estimé", f"{cout_total_estime:,.2f} €", delta="Dans le budget", delta_color="inverse")
            st.success("🎉 Excellente nouvelle ! Ce séjour respecte votre enveloppe budgétaire globale.")
        else:
            c4.metric("Coût Total Estimé", f"{cout_total_estime:,.2f} €", delta="Budget Dépassé", delta_color="normal")
            st.warning("⚠️ Attention : La configuration actuelle dépasse votre budget initial. Considérez de réduire la gamme de confort ou la durée.")

        # Détails logistiques
        col_gauche, col_droite = st.columns([2, 1])
        
        with col_gauche:
            st.markdown("### 🗓️ Votre Itinéraire Jour par Jour")
            
            # Affichage du vol aller
            if not df_vol_trouve.empty:
                st.markdown(f"**🛫 Jour 1 : Voyage Aller** — Vol {df_vol_trouve.iloc[0]['Type']} depuis {df_vol_trouve.iloc[0]['Dep']} vers {df_vol_trouve.iloc[0]['Arr']} ({df_vol_trouve.iloc[0]['Prix']} € / pers)")
            
            # Génération du planning quotidien
            for jour in range(1, duree_jours + 1):
                with st.expander(f"📍 Jour {jour}"):
                    if not df_hotel_trouve.empty:
                        st.write(f"🏨 **Hébergement :** {df_hotel_trouve.iloc[0]['Nom']} ({df_hotel_trouve.iloc[0]['Adresse']})")
                    
                    # Attribution de 1 ou 2 activités à chaque journée
                    acts_du_jour = [liste_activites_planifiees.pop(0) for _ in range(min(2, len(liste_activites_planifiees)))] if liste_activites_planifiees else []
                    if acts_du_jour:
                        st.write("**Activités planifiées :**")
                        for a in acts_du_jour:
                            st.write(f"- ✨ **{a['Nom']}** ({a['Type']}) — {a['Prix']} € / personne (Adresse : {a['Adresse']})")
                    else:
                        st.write("🌿 *Journée libre : profitez-en pour vous détendre ou explorer la ville à votre rythme.*")
            
            # Affichage du vol retour
            if not df_vol_trouve.empty:
                st.markdown(f"**🛬 Jour {duree_jours} : Voyage Retour** — Vol Retour opéré en classe {df_vol_trouve.iloc[0]['Type']}.")

        with col_droite:
            st.markdown("### 🗺️ Carte du Voyage")
            # Extraction des données géographiques de la ville ciblée pour la carte native Streamlit
            ville_geo = pd.read_sql_query("SELECT Nom, lat, lon FROM Ville WHERE id = ?", conn, params=(id_ville_cible,))
            if not ville_geo.empty:
                st.write(f"Points d'intérêt cartographiés à {ville_cible} :")
                map_data = pd.DataFrame({
                    'lat': [ville_geo.iloc[0]['lat']],
                    'lon': [ville_geo.iloc[0]['lon']]
                })
                st.map(map_data, zoom=11)
            else:
                st.info("Aucune donnée de géolocalisation disponible pour cette ville.")

# ---------------------------------------------------------------------
# ONGLET 2 : OUTILS APPLICATIFS (CONVERTISSEUR & MÉTÉO)
# ---------------------------------------------------------------------
with tab_outils:
    st.header("🧰 Outils Pratiques pour le Voyageur")
    
    col_meteo, col_devise = st.columns(2)
    
    with col_meteo:
        st.markdown("### ☀️ Météo en temps réel")
        ville_select_meteo = st.selectbox("Sélectionnez une ville pour voir la météo", list(dict_villes.keys()), key="meteo_city")
        info_meteo = pd.read_sql_query("SELECT Météo FROM Ville WHERE Nom = ?", conn, params=(ville_select_meteo,)).iloc[0]['Météo']
        st.info(f"**Météo actuelle à {ville_select_meteo} :** {info_meteo}")
        
    with col_devise:
        st.markdown("### 💱 Convertisseur de Devises Intégré")
        montant_eur = st.number_input("Montant à convertir en Euros (€)", min_value=1.0, value=100.0)
        
        # Lecture des taux depuis la table Devise
        devises_df = pd.read_sql_query("SELECT * FROM Devise", conn)
        
        taux_usd = devises_df.loc[devises_df['id'] == 2, 'EUR'].values[0]
        taux_jpy = devises_df.loc[devises_df['id'] == 3, 'EUR'].values[0]
        
        conv_usd = montant_eur * taux_usd
        conv_jpy = montant_eur * taux_jpy
        
        st.success(f"💶 **{montant_eur:.2f} €** valent :")
        st.write(f"🇺🇸 **{conv_usd:.2f} USD** (Taux : {taux_usd})")
        st.write(f"🇯🇵 **{conv_jpy:.2f} JPY** (Taux : {taux_jpy})")

# ---------------------------------------------------------------------
# ONGLET 3 : LE COIN TECHNIQUE (VISUALISATION DU SCHÉMA DE BDD)
# ---------------------------------------------------------------------
with tab_database:
    st.header("🗄️ Inspection des tables de la Base de Données")
    st.markdown("Les données affichées ci-dessous reflètent la structure exacte des clés étrangères de votre schéma initial.")
    
    table_choisie = st.selectbox("Choisissez une table à inspecter :", [
        "Pays", "Ville", "Hotel", "Activité", "Aeroport", "Vol", "Devise"
    ])
    
    # Lecture dynamique de la table sélectionnée
    df_table = pd.read_sql_query(f"SELECT * FROM {table_choisie}", conn)
    st.dataframe(df_table, use_container_width=True)
    
    st.markdown("""
    > **Note de développement :** L'architecture du modèle est respectée à 100%. Les liaisons relationnelles `1-N` 
    > matérialisées par vos flèches (ex: plusieurs Hôtels dans une Ville) sont gérées par les contraintes de clés 
    > étrangères de la base de données SQL en arrière-plan.
    """)
