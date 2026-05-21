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
    """Crée les tables et insère les données initiales si la BDD n'existe pas."""
    # Si la base de données existe déjà, on ne la réinitialise pas
    if os.path.exists(DB_FILE):
        return
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # Création des tables selon votre schéma
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
    
    # Insertion des données de test
    cursor.execute("INSERT INTO Devise (id, EUR) VALUES (1, 1.0), (2, 1.09), (3, 152.4);")
    cursor.execute("INSERT INTO Pays (id, Villes, Aerorports, Devise) VALUES (1, 'France', 1, 1), (2, 'USA', 2, 2), (3, 'Japon', 3, 3);")
    
    villes_data = [
        (1, 'Paris', 'Ensoleillé, 21°C', 1, 48.8566, 2.3522),
        (2, 'Nice', 'Beau temps, 24°C', 1, 43.7102, 7.2620),
        (3, 'New York', 'Nuageux, 18°C', 2, 40.7128, -74.0060),
        (4, 'Tokyo', 'Pluie légère, 16°C', 3, 35.6762, 139.6503)
    ]
    for v in villes_data:
        cursor.execute("INSERT INTO Ville (id, Nom, Météo, Pays_id, lat, lon) VALUES (?, ?, ?, ?, ?, ?);", v)
        
    cursor.execute("INSERT INTO Aeroport (id, Nom, Adresse) VALUES (1, 'Paris CDG', 1), (2, 'Nice Côte dAzur', 2), (3, 'New York JFK', 3), (4, 'Tokyo Haneda', 4);")
    
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
        
    vols = [
        (1, 3, 'Économique', 450.0, '2026-06-15'), (1, 3, 'Normal', 850.0, '2026-06-15'), (1, 3, 'Luxe', 3500.0, '2026-06-15'),
        (1, 4, 'Économique', 700.0, '2026-06-15'), (1, 4, 'Normal', 1200.0, '2026-06-15'), (1, 4, 'Luxe', 5500.0, '2026-06-15'),
        (1, 2, 'Économique', 45.0, '2026-06-15'), (1, 2, 'Normal', 90.0, '2026-06-15'), (1, 2, 'Luxe', 250.0, '2026-06-15')
    ]
    for v in vols:
        cursor.execute("INSERT INTO Vol (Aéroport_de_départ, Aéroport_d_arrivée, Type, Prix, Date) VALUES (?, ?, ?, ?, ?);", v)
        
    conn.commit()
    conn.close()

# Fonctions de requêtage pour simplifier le code de l'application Streamlit
def exec_query(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df
