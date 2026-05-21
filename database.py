import sqlite3
import os
import pandas as pd

DB_FILE = "voyage.db"

def get_connection():
    """Retourne une connexion à la base de données avec les clés étrangères activées."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Crée les tables et génère un volume très important de données géolocalisées."""
    # Force la réinitialisation pour charger le nouveau schéma
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # --- 1. CRÉATION DES TABLES ---
    cursor.execute("CREATE TABLE Devise (id INTEGER PRIMARY KEY AUTOINCREMENT, EUR REAL);")
    cursor.execute("""
        CREATE TABLE Pays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Nom TEXT,
            Devise INTEGER,
            FOREIGN KEY(Devise) REFERENCES Devise(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE Ville (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Nom TEXT,
            Météo TEXT,
            Pays_id INTEGER,
            lat REAL,
            lon REAL,
            FOREIGN KEY(Pays_id) REFERENCES Pays(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE Aeroport (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Nom TEXT,
            Adresse_Ville INTEGER,
            FOREIGN KEY(Adresse_Ville) REFERENCES Ville(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE Hotel (
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
        CREATE TABLE Activité (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Nom TEXT,
            Type TEXT,
            Prix REAL,
            Ville_id INTEGER,
            lat REAL, -- NOUVEAU SCHÉMA
            lon REAL, -- NOUVEAU SCHÉMA
            FOREIGN KEY(Ville_id) REFERENCES Ville(id)
        );
    """)
    cursor.execute("""
        CREATE TABLE Vol (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Aéroport_de_départ INTEGER,
            Aéroport_d_arrivée INTEGER,
            Type TEXT,
            Prix REAL,
            FOREIGN KEY(Aéroport_de_départ) REFERENCES Aeroport(id),
            FOREIGN KEY(Aéroport_d_arrivée) REFERENCES Aeroport(id)
        );
    """)
    
    # --- 2. INSERTION DEVISES & PAYS ---
    cursor.execute("INSERT INTO Devise (id, EUR) VALUES (1, 1.0), (2, 1.09), (3, 152.4);") # EUR, USD, JPY
    cursor.execute("INSERT INTO Pays (id, Nom, Devise) VALUES (1, 'France', 1), (2, 'USA', 2), (3, 'Japon', 3);")
    
    # --- 3. INSERTION VILLES (Coordonnées du centre pour le zoom initial) ---
    cursor.execute("INSERT INTO Ville VALUES (1, 'Paris', 'Soleil, 22°C', 1, 48.8566, 2.3522);")
    cursor.execute("INSERT INTO Ville VALUES (2, 'New York', 'Nuageux, 19°C', 2, 40.7128, -74.0060);")
    
    # --- 4. INSERTION HOTELS (Gamme de confort) ---
    hotels = [
        # Paris
        ('Hostel Generator Paris', 'Économique', 45.0, 'Place du Colonel Fabien', 1),
        ('Hôtel Standard design Paris', 'Normal', 140.0, 'Rue des Taillandiers', 1),
        ('The Ritz Paris', 'Luxe', 1100.0, 'Place Vendôme', 1),
        # New York
        ('HI New York City Hostel', 'Économique', 70.0, 'Amsterdam Ave', 2),
        ('CitizenM Times Square', 'Normal', 220.0, '218 W 50th St', 2),
        ('The Plaza Hotel NY', 'Luxe', 980.0, '768 5th Ave', 2)
    ]
    cursor.executemany("INSERT INTO Hotel (Nom, Type, Prix, Adresse, Ville_id) VALUES (?, ?, ?, ?, ?);", hotels)
        
    # --- 5. ÉNORME INJECTION D'ACTIVITÉS GÉOLOCALISÉES ---
    # Nous ajoutons de nombreux points précis pour voir des clusters sur la carte.
    activites = [
        # PARIS (Ville_id = 1)
        # Culture
        ('Musée du Louvre (Entrée Pyramide)', 'Culture', 22.0, 1, 48.8610, 2.3358),
        ('Musée d''Orsay (Entrée Principale)', 'Culture', 18.0, 1, 48.8599, 2.3265),
        ('Cathédrale Notre-Dame (Parvis)', 'Culture', 0.0, 1, 48.8530, 2.3499),
        ('Sainte-Chapelle', 'Culture', 11.5, 1, 48.8555, 2.3450),
        ('Centre Pompidou (Place Georges Pompidou)', 'Culture', 15.0, 1, 48.8606, 2.3522),
        ('Panthéon (Place du Panthéon)', 'Culture', 11.5, 1, 48.8462, 2.3464),
        # Aventure / Vues
        ('Tour Eiffel (Pilier Nord)', 'Aventure', 28.0, 1, 48.8584, 2.2945),
        ('Arc de Triomphe (Haut de l''avenue Champs-Élysées)', 'Aventure', 13.0, 1, 48.8738, 2.2950),
        ('Catacombes de Paris (Entrée)', 'Aventure', 29.0, 1, 48.8338, 2.3324),
        # Détente
        ('Jardin des Tuileries (Allée Centrale)', 'Détente', 0.0, 1, 48.8635, 2.3275),
        ('Jardin du Luxembourg (Fontaine Médicis)', 'Détente', 0.0, 1, 48.8462, 2.3372),
        ('Parc des Buttes-Chaumont (Île du Belvédère)', 'Détente', 0.0, 1, 48.8800, 2.3830),
        # Shopping / Balade
        ('Dégustation Macarons Pierre Hermé', 'Shopping', 25.0, 1, 48.8502, 2.3320),
        ('Balade guidée du Marais (Place des Vosges)', 'Culture', 20.0, 1, 48.8555, 2.3655),
        ('Shopping Galeries Lafayette (Coupole)', 'Shopping', 0.0, 1, 48.8732, 2.3321),
        
        # NEW YORK (Ville_id = 2)
        # Culture
        ('MoMA (Museum of Modern Art)', 'Culture', 25.0, 2, 40.7614, -73.9776),
        ('Metropolitan Museum of Art (The Met)', 'Culture', 30.0, 2, 40.7794, -73.9632),
        ('Guggenheim Museum', 'Culture', 25.0, 2, 40.7830, -73.9590),
        ('Mémorial du 9/11 (Bassin Sud)', 'Culture', 0.0, 2, 40.7115, -74.0132),
        ('Spectacle Broadway (Majestic Theatre)', 'Culture', 120.0, 2, 40.7584, -73.9880),
        # Aventure / Vues
        ('Empire State Building (Observatoire 86e)', 'Aventure', 44.0, 2, 40.7484, -73.9857),
        ('Top of the Rock (Rockefeller Center)', 'Aventure', 40.0, 2, 40.7587, -73.9787),
        ('Observatoire Edge Hudson Yards', 'Aventure', 38.0, 2, 40.7538, -74.0010),
        ('Survol Hélicoptère (Downtown Heliport)', 'Aventure', 260.0, 2, 40.7011, -74.0100),
        ('Traversée du Brooklyn Bridge (Départ Manhattan)', 'Aventure', 0.0, 2, 40.7100, -74.0000),
        # Détente
        ('Central Park (Bethesda Terrace)', 'Détente', 0.0, 2, 40.7738, -73.9708),
        ('Balade sur la High Line (Gansevoort St)', 'Détente', 0.0, 2, 40.7395, -74.0080),
        ('Croisière Statue de la Liberté (Départ Battery Park)', 'Détente', 24.0, 2, 40.7033, -74.0170),
        # Shopping / Balade
        ('Times Square (Marches Rouges)', 'Shopping', 0.0, 2, 40.7580, -73.9855),
        ('Shopping 5th Avenue (Apple Store Cube)', 'Shopping', 0.0, 2, 40.7635, -73.9722),
        ('Grand Central Terminal (Main Concourse)', 'Culture', 0.0, 2, 40.7527, -73.9772),
        ('Marché de Chelsea Market', 'Shopping', 0.0, 2, 40.7420, -74.0060)
    ]
    cursor.executemany("INSERT INTO Activité (Nom, Type, Prix, Ville_id, lat, lon) VALUES (?, ?, ?, ?, ?, ?);", activites)
    
    conn.commit()
    conn.close()

def exec_query(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df
