-- TranspoBot - Version PostgreSQL (apostrophes corrigées)

-- Table chauffeurs
CREATE TABLE chauffeurs (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) NOT NULL,
    prenom VARCHAR(50) NOT NULL,
    telephone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100) UNIQUE,
    numero_permis VARCHAR(30) NOT NULL UNIQUE,
    categorie_permis VARCHAR(5) DEFAULT 'D',
    date_embauche DATE NOT NULL,
    statut VARCHAR(20) DEFAULT 'actif',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO chauffeurs (id, nom, prenom, telephone, email, numero_permis, categorie_permis, date_embauche, statut, created_at) VALUES
(1, 'FALL', 'Ibrahima', '+221771234567', 'ibrahima.fall@transpobot.sn', 'SN-D-001234', 'D', '2018-03-15', 'actif', '2026-04-12 01:57:27'),
(2, 'DIOP', 'Moussa', '+221772345678', 'moussa.diop@transpobot.sn', 'SN-D-002345', 'D', '2019-07-01', 'actif', '2026-04-12 01:57:27'),
(3, 'NDIAYE', 'Fatou', '+221773456789', 'fatou.ndiaye@transpobot.sn', 'SN-D-003456', 'D', '2020-01-10', 'actif', '2026-04-12 01:57:27'),
(4, 'SECK', 'Amadou', '+221774567890', 'amadou.seck@transpobot.sn', 'SN-D-004567', 'D', '2017-11-20', 'actif', '2026-04-12 01:57:27'),
(5, 'BA', 'Ousmane', '+221775678901', 'ousmane.ba@transpobot.sn', 'SN-D-005678', 'D', '2021-04-05', 'actif', '2026-04-12 01:57:27'),
(6, 'MBAYE', 'Cheikh', '+221776789012', 'cheikh.mbaye@transpobot.sn', 'SN-D-006789', 'D', '2022-08-18', 'actif', '2026-04-12 01:57:27'),
(7, 'THIAM', 'Abdoulaye', '+221777890123', 'abdoulaye.thiam@transpobot.sn', 'SN-D-007890', 'D', '2016-05-30', 'en_conge', '2026-04-12 01:57:27'),
(8, 'GUEYE', 'Mariama', '+221778901234', 'mariama.gueye@transpobot.sn', 'SN-D-008901', 'D', '2023-02-14', 'actif', '2026-04-12 01:57:27'),
(9, 'SARR', 'Lamine', '+221779012345', 'lamine.sarr@transpobot.sn', 'SN-D-009012', 'D', '2019-09-09', 'suspendu', '2026-04-12 01:57:27'),
(10, 'DIOUF', 'Seydou', '+221770123456', 'seydou.diouf@transpobot.sn', 'SN-D-010123', 'D', '2020-06-22', 'actif', '2026-04-12 01:57:27');

-- Table vehicules
CREATE TABLE vehicules (
    id SERIAL PRIMARY KEY,
    immatriculation VARCHAR(20) NOT NULL UNIQUE,
    marque VARCHAR(50) NOT NULL,
    modele VARCHAR(50) NOT NULL,
    type_vehicule VARCHAR(20) DEFAULT 'bus',
    capacite INT NOT NULL,
    annee_fabrication INT,
    kilometrage INT DEFAULT 0,
    statut VARCHAR(20) DEFAULT 'actif',
    date_derniere_revision DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO vehicules (id, immatriculation, marque, modele, type_vehicule, capacite, annee_fabrication, kilometrage, statut, date_derniere_revision, created_at) VALUES
(1, 'DK-1234-AB', 'Mercedes', 'Sprinter 516', 'bus', 55, 2018, 45000, 'actif', '2024-11-15', '2026-04-12 01:57:27'),
(2, 'DK-5678-CD', 'Renault', 'Master L3H2', 'minibus', 22, 2019, 38000, 'actif', '2024-10-20', '2026-04-12 01:57:27'),
(3, 'DK-9012-EF', 'Isuzu', 'NQR 75L', 'bus', 60, 2016, 78000, 'en_maintenance', '2024-08-05', '2026-04-12 01:57:27'),
(4, 'DK-3456-GH', 'Toyota', 'Coaster', 'minibus', 30, 2020, 22000, 'actif', '2025-01-10', '2026-04-12 01:57:27'),
(5, 'DK-7890-IJ', 'Tata', 'LP 713', 'bus', 65, 2017, 91000, 'hors_service', '2023-12-01', '2026-04-12 01:57:27'),
(6, 'DK-2345-KL', 'Mercedes', 'Citaro G', 'bus', 80, 2021, 15000, 'actif', '2025-02-28', '2026-04-12 01:57:27'),
(7, 'DK-6789-MN', 'Renault', 'Trafic L2H1', 'minibus', 15, 2022, 8000, 'actif', '2025-03-01', '2026-04-12 01:57:27'),
(8, 'DK-0123-OP', 'Isuzu', 'FVR 34L', 'bus', 55, 2015, 112000, 'en_maintenance', '2024-07-14', '2026-04-12 01:57:27'),
(9, 'DK-4567-QR', 'Toyota', 'Hiace', 'car_rapide', 18, 2019, 51000, 'actif', '2024-12-20', '2026-04-12 01:57:27'),
(10, 'DK-8901-ST', 'Tata', 'Ultra 814', 'bus', 70, 2020, 33000, 'actif', '2025-01-25', '2026-04-12 01:57:27');

-- Table lignes
CREATE TABLE lignes (
    id SERIAL PRIMARY KEY,
    code_ligne VARCHAR(10) NOT NULL UNIQUE,
    nom VARCHAR(100) NOT NULL,
    point_depart VARCHAR(100) NOT NULL,
    point_arrivee VARCHAR(100) NOT NULL,
    distance_km DECIMAL(6,2) NOT NULL,
    duree_estimee_min INT NOT NULL,
    actif INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO lignes (id, code_ligne, nom, point_depart, point_arrivee, distance_km, duree_estimee_min, actif, created_at) VALUES
(1, 'L01', 'Dakar - Pikine', 'Dakar Plateau', 'Pikine Terminus', 12.50, 45, 1, '2026-04-12 01:57:27'),
(2, 'L02', 'Dakar - Guédiawaye', 'Dakar Plateau', 'Guédiawaye Centre', 18.00, 60, 1, '2026-04-12 01:57:27'),
(3, 'L03', 'Dakar - Rufisque', 'Dakar Plateau', 'Rufisque Gare', 28.00, 90, 1, '2026-04-12 01:57:27'),
(4, 'L04', 'Plateau - Parcelles', 'Place de lIndépendance', 'Parcelles Assainies', 9.00, 35, 1, '2026-04-12 01:57:27'),
(5, 'L05', 'Dakar - Thiès Express', 'Gare Routière Dakar', 'Gare Thiès', 70.00, 120, 1, '2026-04-12 01:57:27'),
(6, 'L06', 'Dakar - AIBD', 'Dakar Plateau', 'Aéroport AIBD', 45.00, 75, 1, '2026-04-12 01:57:27');

-- Table tarifs
CREATE TABLE tarifs (
    id SERIAL PRIMARY KEY,
    ligne_id INT REFERENCES lignes(id) ON DELETE CASCADE,
    type_voyageur VARCHAR(20) DEFAULT 'normal',
    prix DECIMAL(8,2) NOT NULL,
    date_application DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ligne_id, type_voyageur)
);

INSERT INTO tarifs (id, ligne_id, type_voyageur, prix, date_application, created_at) VALUES
(1, 1, 'normal', 200.00, '2024-01-01', '2026-04-12 01:57:27'),
(2, 1, 'etudiant', 150.00, '2024-01-01', '2026-04-12 01:57:27'),
(3, 2, 'normal', 250.00, '2024-01-01', '2026-04-12 01:57:27'),
(4, 2, 'etudiant', 175.00, '2024-01-01', '2026-04-12 01:57:27'),
(5, 3, 'normal', 400.00, '2024-01-01', '2026-04-12 01:57:27'),
(6, 3, 'etudiant', 300.00, '2024-01-01', '2026-04-12 01:57:27'),
(7, 4, 'normal', 175.00, '2024-01-01', '2026-04-12 01:57:27'),
(8, 4, 'etudiant', 125.00, '2024-01-01', '2026-04-12 01:57:27'),
(9, 5, 'normal', 1500.00, '2024-01-01', '2026-04-12 01:57:27'),
(10, 5, 'etudiant', 1200.00, '2024-01-01', '2026-04-12 01:57:27'),
(11, 6, 'normal', 800.00, '2024-01-01', '2026-04-12 01:57:27'),
(12, 6, 'etudiant', 600.00, '2024-01-01', '2026-04-12 01:57:27');

-- Table trajets
CREATE TABLE trajets (
    id SERIAL PRIMARY KEY,
    vehicule_id INT REFERENCES vehicules(id),
    chauffeur_id INT REFERENCES chauffeurs(id),
    ligne_id INT REFERENCES lignes(id),
    date_heure_depart TIMESTAMP NOT NULL,
    date_heure_arrivee TIMESTAMP,
    nb_passagers INT DEFAULT 0,
    recette DECIMAL(10,2) DEFAULT 0,
    statut VARCHAR(20) DEFAULT 'planifie',
    observation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO trajets (id, vehicule_id, chauffeur_id, ligne_id, date_heure_depart, date_heure_arrivee, nb_passagers, recette, statut, observation, created_at) VALUES
(1, 1, 1, 1, '2026-04-11 01:57:27', '2026-04-11 02:57:27', 48, 9600.00, 'termine', NULL, '2026-04-12 01:57:27'),
(2, 2, 2, 2, '2026-04-11 01:57:27', '2026-04-11 03:57:27', 20, 5000.00, 'termine', NULL, '2026-04-12 01:57:27'),
(3, 4, 3, 4, '2026-04-10 01:57:27', '2026-04-10 02:57:27', 28, 4900.00, 'termine', NULL, '2026-04-12 01:57:27'),
(4, 6, 4, 1, '2026-04-10 01:57:27', '2026-04-10 03:57:27', 55, 11000.00, 'termine', NULL, '2026-04-12 01:57:27'),
(5, 7, 5, 4, '2026-04-09 01:57:27', '2026-04-09 02:57:27', 14, 2450.00, 'termine', NULL, '2026-04-12 01:57:27'),
(6, 9, 6, 2, '2026-04-09 01:57:27', '2026-04-09 03:57:27', 16, 4000.00, 'termine', NULL, '2026-04-12 01:57:27'),
(7, 1, 1, 3, '2026-04-08 01:57:27', '2026-04-08 03:57:27', 42, 16800.00, 'termine', NULL, '2026-04-12 01:57:27'),
(8, 10, 8, 6, '2026-04-08 01:57:27', '2026-04-08 04:57:27', 35, 28000.00, 'termine', NULL, '2026-04-12 01:57:27'),
(9, 2, 2, 1, '2026-04-07 01:57:27', '2026-04-07 02:57:27', 18, 3600.00, 'termine', NULL, '2026-04-12 01:57:27'),
(10, 4, 3, 5, '2026-04-07 01:57:27', '2026-04-07 04:57:27', 25, 37500.00, 'termine', NULL, '2026-04-12 01:57:27'),
(11, 6, 4, 2, '2026-04-06 01:57:27', '2026-04-06 02:57:27', 60, 15000.00, 'termine', NULL, '2026-04-12 01:57:27'),
(12, 7, 5, 4, '2026-04-06 01:57:27', '2026-04-06 03:57:27', 12, 2100.00, 'termine', NULL, '2026-04-12 01:57:27'),
(13, 1, 1, 1, '2026-04-12 01:57:27', NULL, 0, 0.00, 'en_cours', NULL, '2026-04-12 01:57:27'),
(14, 6, 4, 2, '2026-04-12 01:27:27', NULL, 0, 0.00, 'en_cours', NULL, '2026-04-12 01:57:27'),
(15, 4, 3, 3, '2026-04-12 03:57:27', NULL, 0, 0.00, 'planifie', NULL, '2026-04-12 01:57:27'),
(16, 10, 8, 5, '2026-04-12 05:57:27', NULL, 0, 0.00, 'planifie', NULL, '2026-04-12 01:57:27'),
(17, 2, 2, 2, '2026-04-04 01:57:27', '2026-04-04 02:57:27', 22, 5500.00, 'termine', NULL, '2026-04-12 01:57:27'),
(18, 9, 6, 1, '2026-04-03 01:57:27', '2026-04-03 02:57:27', 50, 10000.00, 'termine', NULL, '2026-04-12 01:57:27'),
(19, 1, 1, 4, '2026-04-02 01:57:27', '2026-04-02 02:57:27', 30, 5250.00, 'termine', NULL, '2026-04-12 01:57:27'),
(20, 7, 5, 3, '2026-04-01 01:57:27', '2026-04-01 03:57:27', 38, 15200.00, 'termine', NULL, '2026-04-12 01:57:27'),
(21, 4, 3, 6, '2026-03-31 01:57:27', '2026-03-31 03:57:27', 28, 22400.00, 'termine', NULL, '2026-04-12 01:57:27'),
(22, 6, 4, 2, '2026-03-30 01:57:27', '2026-03-30 03:57:27', 45, 11250.00, 'termine', NULL, '2026-04-12 01:57:27'),
(23, 3, 7, 1, '2026-04-05 01:57:27', NULL, 0, 0.00, 'annule', NULL, '2026-04-12 01:57:27'),
(24, 8, 9, 3, '2026-03-28 01:57:27', NULL, 0, 0.00, 'annule', NULL, '2026-04-12 01:57:27'),
(25, 10, 8, 5, '2026-03-23 01:57:27', '2026-03-23 03:57:27', 30, 45000.00, 'termine', NULL, '2026-04-12 01:57:27');

-- Table incidents (avec apostrophes échappées)
CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    trajet_id INT REFERENCES trajets(id) ON DELETE CASCADE,
    type_incident VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    date_incident TIMESTAMP NOT NULL,
    gravite VARCHAR(10) DEFAULT 'faible',
    resolu INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO incidents (id, trajet_id, type_incident, description, date_incident, gravite, resolu, created_at) VALUES
(1, 1, 'retard', 'Embouteillage important au niveau de la Corniche. Retard de 25 minutes.', '2026-04-11 01:57:27', 'faible', 1, '2026-04-12 01:57:27'),
(2, 3, 'panne', 'Crevaison d''un pneu avant droit. Réparation sur place en 40 minutes.', '2026-04-10 01:57:27', 'moyen', 1, '2026-04-12 01:57:27'),
(3, 7, 'accident', 'Accrochage léger avec un véhicule particulier au rond-point de l''Échangeur. Dégâts matériels mineurs.', '2026-04-08 01:57:27', 'moyen', 1, '2026-04-12 01:57:27'),
(4, 9, 'retard', 'Attente prolongée au terminus départ. Départ avec 20 minutes de retard.', '2026-04-07 01:57:27', 'faible', 1, '2026-04-12 01:57:27'),
(5, 11, 'panne', 'Problème moteur diagnostiqué en route. Véhicule remorqué au dépôt.', '2026-04-06 01:57:27', 'grave', 1, '2026-04-12 01:57:27'),
(6, 17, 'retard', 'Manifestation sur l''Avenue Cheikh Anta Diop bloquant la circulation pendant 1h.', '2026-04-04 01:57:27', 'faible', 1, '2026-04-12 01:57:27'),
(7, 18, 'agression', 'Tentative d''agression du chauffeur par un passager refusant de payer. Intervention policière.', '2026-04-03 01:57:27', 'grave', 1, '2026-04-12 01:57:27'),
(8, 19, 'panne', 'Défaillance du système de climatisation. Trajet terminé sans climatisation.', '2026-04-02 01:57:27', 'faible', 1, '2026-04-12 01:57:27'),
(9, 20, 'accident', 'Collision avec un moto-taxi à l''entrée de Rufisque. Léger blessé côté moto.', '2026-04-01 01:57:27', 'grave', 0, '2026-04-12 01:57:27'),
(10, 21, 'retard', 'Contrôle de police au niveau de Pikine. Délai supplémentaire de 15 min.', '2026-03-31 01:57:27', 'faible', 1, '2026-04-12 01:57:27'),
(11, 23, 'panne', 'Problème électrique détecté avant le départ. Trajet annulé pour maintenance.', '2026-04-05 01:57:27', 'moyen', 1, '2026-04-12 01:57:27'),
(12, 2, 'retard', 'Surcharge de passagers à l''arrêt Colobane. Attente du prochain bus pour certains passagers.', '2026-04-11 01:57:27', 'faible', 1, '2026-04-12 01:57:27');

-- Mise à jour des séquences
SELECT setval('chauffeurs_id_seq', (SELECT MAX(id) FROM chauffeurs));
SELECT setval('vehicules_id_seq', (SELECT MAX(id) FROM vehicules));
SELECT setval('lignes_id_seq', (SELECT MAX(id) FROM lignes));
SELECT setval('tarifs_id_seq', (SELECT MAX(id) FROM tarifs));
SELECT setval('trajets_id_seq', (SELECT MAX(id) FROM trajets));
SELECT setval('incidents_id_seq', (SELECT MAX(id) FROM incidents));