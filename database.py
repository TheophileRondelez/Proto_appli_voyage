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
    """Crée les tables et génère un volume important de données réalistes."""
    # Force la réinitialisation pour charger les nouvelles données volumineuses
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # --- CRÉATION DES TABLES ---
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
    
    # --- 1. INSERTION DEVISES & PAYS ---
    cursor.execute("INSERT INTO Devise (id, EUR) VALUES (1, 1.0), (2, 1.09), (3, 152.4), (4, 1.48);") # EUR, USD, JPY, CAD
    cursor.execute("""
        INSERT INTO Pays (id, Villes, Aerorports, Devise) VALUES 
        (1, 'France', 1, 1), 
        (2, 'USA', 2, 2), 
        (3, 'Japon', 3, 3),
        (4, 'Canada', 4, 4);
    """)
    
    # --- 2. INSERTION VILLES (Avec coordonnées géographiques exactes) ---
    villes_data = [
        (1, 'Paris', 'Ensoleillé, 21°C', 1, 48.8566, 2.3522),
        (2, 'Nice', 'Ciel dégagé, 24°C', 1, 43.7102, 7.2620),
        (3, 'New York', 'Nuageux, 18°C', 2, 40.7128, -74.0060),
        (4, 'Tokyo', 'Pluie légère, 16°C', 3, 35.6762, 139.6503),
        (5, 'Montréal', 'Vent dous, 19°C', 4, 45.5017, -73.5673),
        (6, 'Kyoto', 'Beau soleil, 22°C', 3, 35.0116, 135.7681)
    ]
    for v in villes_data:
        cursor.execute("INSERT INTO Ville (id, Nom, Météo, Pays_id, lat, lon) VALUES (?, ?, ?, ?, ?, ?);", v)
        
    # --- 3. INSERTION AÉROPORTS ---
    cursor.execute("""
        INSERT INTO Aeroport (id, Nom, Adresse) VALUES 
        (1, 'Paris CDG (LFPG)', 1), 
        (2, 'Nice Côte dAzur (LFMN)', 2), 
        (3, 'New York JFK (KJFK)', 3), 
        (4, 'Tokyo Haneda (RJTT)', 4),
        (5, 'Montréal-Trudeau (CYUL)', 5),
        (6, 'Osaka Itami (RJOO) - Proche Kyoto', 6);
    """)
    
    # --- 4. INSERTION HOTELS (Économique, Normal, Luxe pour chaque destination) ---
    hotels = [
        # Paris (Ville 1)
        ('Hostel Les Piaules Belleville', 'Économique', 38.0, '59 Boulevard de Belleville, Paris', 1),
        ('Generator Paris', 'Économique', 42.0, '9 Place du Colonel Fabien, Paris', 1),
        ('Hôtel Standard design Paris', 'Normal', 135.0, '29 Rue Taillandiers, Paris', 1),
        ('Hôtel API Voyageur Paris', 'Normal', 110.0, '14 Rue de la Bourse, Paris', 1),
        ('The Ritz Paris', 'Luxe', 1100.0, '15 Place Vendôme, Paris', 1),
        ('Le Bristol Paris', 'Luxe', 980.0, '112 Rue du Faubourg Saint-Honoré, Paris', 1),
        
        # Nice (Ville 2)
        ('Meyerbeer Beach Hostel', 'Économique', 30.0, '15 Rue Meyerbeer, Nice', 2),
        ('Hôtel Windsor', 'Normal', 115.0, '11 Rue Dalpozzo, Nice', 2),
        ('Hôtel Aston La Scala', 'Normal', 140.0, '12 Avenue Félix Faure, Nice', 2),
        ('Nice Negresco', 'Luxe', 520.0, '37 Promenade des Anglais, Nice', 2),
        ('Hyatt Regency Palais de la Méditerranée', 'Luxe', 460.0, '13 Promenade des Anglais, Nice', 2),
        
        # New York (Ville 3)
        ('HI New York City Hostel', 'Économique', 65.0, '891 Amsterdam Ave, NY', 3),
        ('Pod 39 Hotel Manhattan', 'Économique', 95.0, '145 E 39th St, NY', 3),
        ('CitizenM New York Times Square', 'Normal', 210.0, '218 W 50th St, NY', 3),
        ('Arlo NoMad', 'Normal', 185.0, '11 E 31st St, NY', 3),
        ('The Plaza Hotel NY', 'Luxe', 990.0, '768 5th Ave, NY', 3),
        ('The Mandarin Oriental', 'Luxe', 1250.0, '80 Columbus Circle, NY', 3),
        
        # Tokyo (Ville 4)
        ('Nine Hours Capsule Shinjuku', 'Économique', 28.0, 'Shinjuku 1-1, Tokyo', 4),
        ('Book and Bed Tokyo Shinjuku', 'Économique', 35.0, 'Kabukicho, Tokyo', 4),
        ('Keio Plaza Hotel Tokyo', 'Normal', 190.0, 'Nishi-Shinjuku, Tokyo', 4),
        ('Shiba Park Hotel', 'Normal', 145.0, 'Minato-ku, Tokyo', 4),
        ('Aman Tokyo', 'Luxe', 1350.0, 'Chiyoda-ku, Tokyo', 4),
        ('The Ritz-Carlton Tokyo', 'Luxe', 1100.0, 'Akasaka, Tokyo', 4),

        # Montréal (Ville 5)
        ('M Montreal Hostel', 'Économique', 32.0, '1245 Rue Saint-André, Montréal', 5),
        ('Samesun Montreal Central', 'Économique', 29.0, '1586 St Denis St, Montréal', 5),
        ('Hôtel Monville', 'Normal', 160.0, '1041 Rue de Bleury, Montréal', 5),
        ('Alt Hôtel Montréal', 'Normal', 145.0, '120 Peel St, Montréal', 5),
        ('Ritz-Carlton Montréal', 'Luxe', 550.0, '1228 Sherbrooke St W, Montréal', 5),
        ('Hôtel William Gray', 'Luxe', 380.0, '421 Rue Saint Vincent, Montréal', 5),

        # Kyoto (Ville 6)
        ('Piece Hostel Kyoto', 'Économique', 25.0, 'Minami-ku, Kyoto', 6),
        ('Kyoto Granbell Hotel', 'Normal', 130.0, 'Gionmachi, Kyoto', 6),
        ('The Thousand Kyoto', 'Luxe', 420.0, 'Shimogyo-ku, Kyoto', 6)
    ]
    for h in hotels:
        cursor.execute("INSERT INTO Hotel (Nom, Type, Prix, Adresse, Ville_id) VALUES (?, ?, ?, ?, ?);", h)
        
    # --- 5. INSERTION ACTIVITÉS (Très variées par goûts) ---
    activites = [
        # Paris
        ('Musée du Louvre', 'Palais Royal', 'Culture', 22.0, 1),
        ('Tour Eiffel (Sommet)', 'Champ de Mars', 'Culture', 29.0, 1),
        ('Balade guidée Street-Art', 'Butte-aux-Cailles', 'Culture', 15.0, 1),
        ('Bateaux Mouches romantiques', 'Pont de lAlma', 'Détente', 16.0, 1),
        ('Escape Game Panique à lOpéra', 'Opéra Garnier', 'Aventure', 35.0, 1),
        ('Session Shopping Printemps', 'Boulevard Haussmann', 'Shopping', 0.0, 1),
        ('Dégustation Fromage & Vin', 'Le Marais', 'Détente', 55.0, 1),
        
        # Nice
        ('Plongée sous-marine / Baptême', 'Port de Nice', 'Aventure', 80.0, 2),
        ('Musée Marc Chagall', 'Avenue Docteur Ménard', 'Culture', 10.0, 2),
        ('Canyoning dans larrière-pays', 'Gorges du Loup', 'Aventure', 65.0, 2),
        ('Chasse aux trésors Vieux-Nice', 'Place Masséna', 'Culture', 12.0, 2),
        ('Location de Transat privé + Cocktail', 'Promenade des Anglais', 'Détente', 45.0, 2),
        ('Shopping Cours Saleya', 'Vieux Nice', 'Shopping', 0.0, 2),
        
        # New York
        ('Survol de NYC en hélicoptère', 'Manhattan Heliport', 'Aventure', 260.0, 3),
        ('MoMA (Museum of Modern Art)', '11 W 53rd St', 'Culture', 25.0, 3),
        ('Observatoire Edge Hudson Yards', '30 Hudson Yards', 'Aventure', 42.0, 3),
        ('Spectacle de Broadway (Roi Lion)', 'Times Square', 'Culture', 110.0, 3),
        ('Balade guidée dans Central Park', 'Central Park', 'Détente', 20.0, 3),
        ('Shopping Outlets Woodbury', 'Bus depuis Port Authority', 'Shopping', 40.0, 3),
        ('Croisière Statue de la Liberté', 'Battery Park', 'Culture', 30.0, 3),
        
        # Tokyo
        ('Excursion d''une journée au Mont Fuji', 'Départ Shinjuku', 'Aventure', 95.0, 4),
        ('Quartier Geek & Robotique Akihabara', 'Akihabara Station', 'Shopping', 0.0, 4),
        ('Cérémonie du Thé Traditionnelle', 'Asakusa', 'Culture', 45.0, 4),
        ('Bains thermaux de style Edo', 'Odaiba', 'Détente', 30.0, 4),
        ('Karting en ville déguisé (Street Go-Kart)', 'Shibuya', 'Aventure', 75.0, 4),
        ('Musée d''art numérique teamLab Planets', 'Toyosu', 'Culture', 26.0, 4),
        ('Shopping de mode alternative', 'Harajuku Takeshita St', 'Shopping', 0.0, 4),

        # Montréal
        ('Randonnée guidée du Mont-Royal', 'Parc du Mont-Royal', 'Détente', 15.0, 5),
        ('Visite de la Basilique Notre-Dame', 'Vieux-Montréal', 'Culture', 14.0, 5),
        ('Saut à l''élastique / Tyrolienne', 'Vieux-Port', 'Aventure', 25.0, 5),
        ('Dégustation culinaire (Poutine & Bagels)', 'Plateau Mont-Royal', 'Détente', 40.0, 5),
        ('Shopping souterrain (RÉSO)', 'Centre-ville', 'Shopping', 0.0, 5),
        ('Musée des Beaux-Arts de Montréal', 'Sherbrooke St W', 'Culture', 24.0, 5),

        # Kyoto
        ('Sanctuaire Fushimi Inari (Mille Toris)', 'Fushimi-ku', 'Culture', 0.0, 6),
        ('Forêt de Bambous d''Arashiyama', 'Arashiyama', 'Détente', 0.0, 6),
        ('Cours de cuisine de sushis traditionnels', 'Gion', 'Aventure', 60.0, 6)
    ]
    for a in activites:
        cursor.execute("INSERT INTO Activité (Nom, Adresse, Type, Prix, Ville_id) VALUES (?, ?, ?, ?, ?);", a)
        
    # --- 6. INSERTION VOLS ALLER-RETOUR ---
    # Pour chaque destination lointaine (3, 4, 5) et proche (2), on génère des vols Éco, Normal et Luxe.
    # Aéroport de départ = 1 (Paris CDG)
    vols_catalogue = [
        # Vols vers Nice (Arrêt 2)
        (1, 2, 'Économique', 49.0, '2026-06-15'),
        (1, 2, 'Normal', 110.0, '2026-06-15'),
        (1, 2, 'Luxe', 290.0, '2026-06-15'),
        
        # Vols vers New York (Arrêt 3)
        (1, 3, 'Économique', 420.0, '2026-06-15'),
        (1, 3, 'Normal', 790.0, '2026-06-15'),
        (1, 3, 'Luxe', 3400.0, '2026-06-15'),
        
        # Vols vers Tokyo (Arrêt 4)
        (1, 4, 'Économique', 680.0, '2026-06-15'),
        (1, 4, 'Normal', 1250.0, '2026-06-15'),
        (1, 4, 'Luxe', 5200.0, '2026-06-15'),

        # Vols vers Montréal (Arrêt 5)
        (1, 5, 'Économique', 390.0, '2026-06-15'),
        (1, 5, 'Normal', 720.0, '2026-06-15'),
        (1, 5, 'Luxe', 2800.0, '2026-06-15'),

        # Vols vers Kyoto/Osaka (Arrêt 6)
        (1, 6, 'Économique', 710.0, '2026-06-15'),
        (1, 6, 'Normal', 1300.0, '2026-06-15'),
        (1, 6, 'Luxe', 5400.0, '2026-06-15')
    ]
    for v in vols_catalogue:
        cursor.execute("INSERT INTO Vol (Aéroport_de_départ, Aéroport_d_arrivée, Type, Prix, Date) VALUES (?, ?, ?, ?, ?);", v)
        
    conn.commit()
    conn.close()

def exec_query(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df
