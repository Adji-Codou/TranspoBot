-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1
-- Généré le : dim. 12 avr. 2026 à 04:22
-- Version du serveur : 10.4.32-MariaDB
-- Version de PHP : 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `transpobot`
--

-- --------------------------------------------------------

--
-- Structure de la table `chauffeurs`
--

CREATE TABLE `chauffeurs` (
  `id` int(11) NOT NULL,
  `nom` varchar(50) NOT NULL,
  `prenom` varchar(50) NOT NULL,
  `telephone` varchar(20) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `numero_permis` varchar(30) NOT NULL,
  `categorie_permis` varchar(5) NOT NULL DEFAULT 'D' COMMENT 'Catégorie du permis (D = bus)',
  `date_embauche` date NOT NULL,
  `statut` enum('actif','en_conge','suspendu') NOT NULL DEFAULT 'actif',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Chauffeurs employés par la société';

--
-- Déchargement des données de la table `chauffeurs`
--

INSERT INTO `chauffeurs` (`id`, `nom`, `prenom`, `telephone`, `email`, `numero_permis`, `categorie_permis`, `date_embauche`, `statut`, `created_at`) VALUES
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

-- --------------------------------------------------------

--
-- Structure de la table `incidents`
--

CREATE TABLE `incidents` (
  `id` int(11) NOT NULL,
  `trajet_id` int(11) NOT NULL,
  `type_incident` enum('accident','panne','retard','agression','autre') NOT NULL,
  `description` text NOT NULL,
  `date_incident` datetime NOT NULL,
  `gravite` enum('faible','moyen','grave') NOT NULL DEFAULT 'faible',
  `resolu` tinyint(1) NOT NULL DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Incidents survenus durant les trajets';

--
-- Déchargement des données de la table `incidents`
--

INSERT INTO `incidents` (`id`, `trajet_id`, `type_incident`, `description`, `date_incident`, `gravite`, `resolu`, `created_at`) VALUES
(1, 1, 'retard', 'Embouteillage important au niveau de la Corniche. Retard de 25 minutes.', '2026-04-11 01:57:27', 'faible', 1, '2026-04-12 01:57:27'),
(2, 3, 'panne', 'Crevaison d\'un pneu avant droit. Réparation sur place en 40 minutes.', '2026-04-10 01:57:27', 'moyen', 1, '2026-04-12 01:57:27'),
(3, 7, 'accident', 'Accrochage léger avec un véhicule particulier au rond-point de l\'Échangeur. Dégâts matériels mineurs.', '2026-04-08 01:57:27', 'moyen', 1, '2026-04-12 01:57:27'),
(4, 9, 'retard', 'Attente prolongée au terminus départ. Départ avec 20 minutes de retard.', '2026-04-07 01:57:27', 'faible', 1, '2026-04-12 01:57:27'),
(5, 11, 'panne', 'Problème moteur diagnostiqué en route. Véhicule remorqué au dépôt.', '2026-04-06 01:57:27', 'grave', 1, '2026-04-12 01:57:27'),
(6, 17, 'retard', 'Manifestation sur l\'Avenue Cheikh Anta Diop bloquant la circulation pendant 1h.', '2026-04-04 01:57:27', 'faible', 1, '2026-04-12 01:57:27'),
(7, 18, 'agression', 'Tentative d\'agression du chauffeur par un passager refusant de payer. Intervention policière.', '2026-04-03 01:57:27', 'grave', 1, '2026-04-12 01:57:27'),
(8, 19, 'panne', 'Défaillance du système de climatisation. Trajet terminé sans climatisation.', '2026-04-02 01:57:27', 'faible', 1, '2026-04-12 01:57:27'),
(9, 20, 'accident', 'Collision avec un moto-taxi à l\'entrée de Rufisque. Léger blessé côté moto.', '2026-04-01 01:57:27', 'grave', 0, '2026-04-12 01:57:27'),
(10, 21, 'retard', 'Contrôle de police au niveau de Pikine. Délai supplémentaire de 15 min.', '2026-03-31 01:57:27', 'faible', 1, '2026-04-12 01:57:27'),
(11, 23, 'panne', 'Problème électrique détecté avant le départ. Trajet annulé pour maintenance.', '2026-04-05 01:57:27', 'moyen', 1, '2026-04-12 01:57:27'),
(12, 2, 'retard', 'Surcharge de passagers à l\'arrêt Colobane. Attente du prochain bus pour certains passagers.', '2026-04-11 01:57:27', 'faible', 1, '2026-04-12 01:57:27');

-- --------------------------------------------------------

--
-- Structure de la table `lignes`
--

CREATE TABLE `lignes` (
  `id` int(11) NOT NULL,
  `code_ligne` varchar(10) NOT NULL COMMENT 'Ex: L01, L02',
  `nom` varchar(100) NOT NULL,
  `point_depart` varchar(100) NOT NULL,
  `point_arrivee` varchar(100) NOT NULL,
  `distance_km` decimal(6,2) NOT NULL,
  `duree_estimee_min` int(11) NOT NULL COMMENT 'Durée estimée en minutes',
  `actif` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Lignes de transport desservies';

--
-- Déchargement des données de la table `lignes`
--

INSERT INTO `lignes` (`id`, `code_ligne`, `nom`, `point_depart`, `point_arrivee`, `distance_km`, `duree_estimee_min`, `actif`, `created_at`) VALUES
(1, 'L01', 'Dakar - Pikine', 'Dakar Plateau', 'Pikine Terminus', 12.50, 45, 1, '2026-04-12 01:57:27'),
(2, 'L02', 'Dakar - Guédiawaye', 'Dakar Plateau', 'Guédiawaye Centre', 18.00, 60, 1, '2026-04-12 01:57:27'),
(3, 'L03', 'Dakar - Rufisque', 'Dakar Plateau', 'Rufisque Gare', 28.00, 90, 1, '2026-04-12 01:57:27'),
(4, 'L04', 'Plateau - Parcelles', 'Place de lIndépendance', 'Parcelles Assainies', 9.00, 35, 1, '2026-04-12 01:57:27'),
(5, 'L05', 'Dakar - Thiès Express', 'Gare Routière Dakar', 'Gare Thiès', 70.00, 120, 1, '2026-04-12 01:57:27'),
(6, 'L06', 'Dakar - AIBD', 'Dakar Plateau', 'Aéroport AIBD', 45.00, 75, 1, '2026-04-12 01:57:27');

-- --------------------------------------------------------

--
-- Structure de la table `tarifs`
--

CREATE TABLE `tarifs` (
  `id` int(11) NOT NULL,
  `ligne_id` int(11) NOT NULL,
  `type_voyageur` enum('normal','etudiant','senior','enfant') NOT NULL DEFAULT 'normal',
  `prix` decimal(8,2) NOT NULL COMMENT 'Prix en FCFA',
  `date_application` date NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tarifs appliqués par ligne et type de voyageur';

--
-- Déchargement des données de la table `tarifs`
--

INSERT INTO `tarifs` (`id`, `ligne_id`, `type_voyageur`, `prix`, `date_application`, `created_at`) VALUES
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

-- --------------------------------------------------------

--
-- Structure de la table `trajets`
--

CREATE TABLE `trajets` (
  `id` int(11) NOT NULL,
  `vehicule_id` int(11) NOT NULL,
  `chauffeur_id` int(11) NOT NULL,
  `ligne_id` int(11) NOT NULL,
  `date_heure_depart` datetime NOT NULL,
  `date_heure_arrivee` datetime DEFAULT NULL COMMENT 'NULL si trajet non terminé',
  `nb_passagers` int(11) NOT NULL DEFAULT 0,
  `recette` decimal(10,2) NOT NULL DEFAULT 0.00 COMMENT 'Recette en FCFA',
  `statut` enum('planifie','en_cours','termine','annule') NOT NULL DEFAULT 'planifie',
  `observation` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Trajets effectués ou planifiés';

--
-- Déchargement des données de la table `trajets`
--

INSERT INTO `trajets` (`id`, `vehicule_id`, `chauffeur_id`, `ligne_id`, `date_heure_depart`, `date_heure_arrivee`, `nb_passagers`, `recette`, `statut`, `observation`, `created_at`) VALUES
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

-- --------------------------------------------------------

--
-- Structure de la table `vehicules`
--

CREATE TABLE `vehicules` (
  `id` int(11) NOT NULL,
  `immatriculation` varchar(20) NOT NULL,
  `marque` varchar(50) NOT NULL,
  `modele` varchar(50) NOT NULL,
  `type_vehicule` enum('bus','minibus','car_rapide') NOT NULL DEFAULT 'bus',
  `capacite` int(11) NOT NULL COMMENT 'Nombre de places assises',
  `annee_fabrication` year(4) NOT NULL,
  `kilometrage` int(11) NOT NULL DEFAULT 0 COMMENT 'Kilométrage total parcouru',
  `statut` enum('actif','en_maintenance','hors_service') NOT NULL DEFAULT 'actif',
  `date_derniere_revision` date DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Flotte de véhicules de la société de transport';

--
-- Déchargement des données de la table `vehicules`
--

INSERT INTO `vehicules` (`id`, `immatriculation`, `marque`, `modele`, `type_vehicule`, `capacite`, `annee_fabrication`, `kilometrage`, `statut`, `date_derniere_revision`, `created_at`) VALUES
(1, 'DK-1234-AB', 'Mercedes', 'Sprinter 516', 'bus', 55, '2018', 45000, 'actif', '2024-11-15', '2026-04-12 01:57:27'),
(2, 'DK-5678-CD', 'Renault', 'Master L3H2', 'minibus', 22, '2019', 38000, 'actif', '2024-10-20', '2026-04-12 01:57:27'),
(3, 'DK-9012-EF', 'Isuzu', 'NQR 75L', 'bus', 60, '2016', 78000, 'en_maintenance', '2024-08-05', '2026-04-12 01:57:27'),
(4, 'DK-3456-GH', 'Toyota', 'Coaster', 'minibus', 30, '2020', 22000, 'actif', '2025-01-10', '2026-04-12 01:57:27'),
(5, 'DK-7890-IJ', 'Tata', 'LP 713', 'bus', 65, '2017', 91000, 'hors_service', '2023-12-01', '2026-04-12 01:57:27'),
(6, 'DK-2345-KL', 'Mercedes', 'Citaro G', 'bus', 80, '2021', 15000, 'actif', '2025-02-28', '2026-04-12 01:57:27'),
(7, 'DK-6789-MN', 'Renault', 'Trafic L2H1', 'minibus', 15, '2022', 8000, 'actif', '2025-03-01', '2026-04-12 01:57:27'),
(8, 'DK-0123-OP', 'Isuzu', 'FVR 34L', 'bus', 55, '2015', 112000, 'en_maintenance', '2024-07-14', '2026-04-12 01:57:27'),
(9, 'DK-4567-QR', 'Toyota', 'Hiace', 'car_rapide', 18, '2019', 51000, 'actif', '2024-12-20', '2026-04-12 01:57:27'),
(10, 'DK-8901-ST', 'Tata', 'Ultra 814', 'bus', 70, '2020', 33000, 'actif', '2025-01-25', '2026-04-12 01:57:27');

-- --------------------------------------------------------

--
-- Doublure de structure pour la vue `v_kpis`
-- (Voir ci-dessous la vue réelle)
--
CREATE TABLE `v_kpis` (
`vehicules_actifs` bigint(21)
,`vehicules_maintenance` bigint(21)
,`chauffeurs_actifs` bigint(21)
,`trajets_en_cours` bigint(21)
,`trajets_semaine` bigint(21)
,`recettes_mois` decimal(32,2)
,`incidents_mois` bigint(21)
,`incidents_non_resolus` bigint(21)
);

-- --------------------------------------------------------

--
-- Doublure de structure pour la vue `v_stats_chauffeurs`
-- (Voir ci-dessous la vue réelle)
--
CREATE TABLE `v_stats_chauffeurs` (
`id` int(11)
,`chauffeur` varchar(101)
,`statut` enum('actif','en_conge','suspendu')
,`nb_trajets` bigint(21)
,`trajets_termines` decimal(22,0)
,`total_passagers` decimal(32,0)
,`total_recettes` decimal(32,2)
,`nb_incidents` bigint(21)
);

-- --------------------------------------------------------

--
-- Doublure de structure pour la vue `v_trajets_detail`
-- (Voir ci-dessous la vue réelle)
--
CREATE TABLE `v_trajets_detail` (
`id` int(11)
,`date_heure_depart` datetime
,`date_heure_arrivee` datetime
,`nb_passagers` int(11)
,`recette` decimal(10,2)
,`statut` enum('planifie','en_cours','termine','annule')
,`immatriculation` varchar(20)
,`marque` varchar(50)
,`modele` varchar(50)
,`chauffeur` varchar(101)
,`code_ligne` varchar(10)
,`ligne` varchar(100)
,`point_depart` varchar(100)
,`point_arrivee` varchar(100)
);

-- --------------------------------------------------------

--
-- Structure de la vue `v_kpis`
--
DROP TABLE IF EXISTS `v_kpis`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_kpis`  AS SELECT (select count(0) from `vehicules` where `vehicules`.`statut` = 'actif') AS `vehicules_actifs`, (select count(0) from `vehicules` where `vehicules`.`statut` = 'en_maintenance') AS `vehicules_maintenance`, (select count(0) from `chauffeurs` where `chauffeurs`.`statut` = 'actif') AS `chauffeurs_actifs`, (select count(0) from `trajets` where `trajets`.`statut` = 'en_cours') AS `trajets_en_cours`, (select count(0) from `trajets` where `trajets`.`statut` = 'termine' and `trajets`.`date_heure_depart` >= current_timestamp() - interval 7 day) AS `trajets_semaine`, (select ifnull(sum(`trajets`.`recette`),0) from `trajets` where `trajets`.`statut` = 'termine' and `trajets`.`date_heure_depart` >= current_timestamp() - interval 30 day) AS `recettes_mois`, (select count(0) from `incidents` where `incidents`.`date_incident` >= current_timestamp() - interval 30 day) AS `incidents_mois`, (select count(0) from `incidents` where `incidents`.`resolu` = 0) AS `incidents_non_resolus` ;

-- --------------------------------------------------------

--
-- Structure de la vue `v_stats_chauffeurs`
--
DROP TABLE IF EXISTS `v_stats_chauffeurs`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_stats_chauffeurs`  AS SELECT `c`.`id` AS `id`, concat(`c`.`prenom`,' ',`c`.`nom`) AS `chauffeur`, `c`.`statut` AS `statut`, count(`t`.`id`) AS `nb_trajets`, sum(case when `t`.`statut` = 'termine' then 1 else 0 end) AS `trajets_termines`, sum(`t`.`nb_passagers`) AS `total_passagers`, sum(`t`.`recette`) AS `total_recettes`, count(`i`.`id`) AS `nb_incidents` FROM ((`chauffeurs` `c` left join `trajets` `t` on(`t`.`chauffeur_id` = `c`.`id`)) left join `incidents` `i` on(`i`.`trajet_id` = `t`.`id`)) GROUP BY `c`.`id` ;

-- --------------------------------------------------------

--
-- Structure de la vue `v_trajets_detail`
--
DROP TABLE IF EXISTS `v_trajets_detail`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_trajets_detail`  AS SELECT `t`.`id` AS `id`, `t`.`date_heure_depart` AS `date_heure_depart`, `t`.`date_heure_arrivee` AS `date_heure_arrivee`, `t`.`nb_passagers` AS `nb_passagers`, `t`.`recette` AS `recette`, `t`.`statut` AS `statut`, `v`.`immatriculation` AS `immatriculation`, `v`.`marque` AS `marque`, `v`.`modele` AS `modele`, concat(`c`.`prenom`,' ',`c`.`nom`) AS `chauffeur`, `l`.`code_ligne` AS `code_ligne`, `l`.`nom` AS `ligne`, `l`.`point_depart` AS `point_depart`, `l`.`point_arrivee` AS `point_arrivee` FROM (((`trajets` `t` join `vehicules` `v` on(`t`.`vehicule_id` = `v`.`id`)) join `chauffeurs` `c` on(`t`.`chauffeur_id` = `c`.`id`)) join `lignes` `l` on(`t`.`ligne_id` = `l`.`id`)) ;

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `chauffeurs`
--
ALTER TABLE `chauffeurs`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `telephone` (`telephone`),
  ADD UNIQUE KEY `numero_permis` (`numero_permis`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Index pour la table `incidents`
--
ALTER TABLE `incidents`
  ADD PRIMARY KEY (`id`),
  ADD KEY `trajet_id` (`trajet_id`);

--
-- Index pour la table `lignes`
--
ALTER TABLE `lignes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `code_ligne` (`code_ligne`);

--
-- Index pour la table `tarifs`
--
ALTER TABLE `tarifs`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_tarif` (`ligne_id`,`type_voyageur`);

--
-- Index pour la table `trajets`
--
ALTER TABLE `trajets`
  ADD PRIMARY KEY (`id`),
  ADD KEY `vehicule_id` (`vehicule_id`),
  ADD KEY `chauffeur_id` (`chauffeur_id`),
  ADD KEY `ligne_id` (`ligne_id`);

--
-- Index pour la table `vehicules`
--
ALTER TABLE `vehicules`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `immatriculation` (`immatriculation`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `chauffeurs`
--
ALTER TABLE `chauffeurs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT pour la table `incidents`
--
ALTER TABLE `incidents`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT pour la table `lignes`
--
ALTER TABLE `lignes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT pour la table `tarifs`
--
ALTER TABLE `tarifs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT pour la table `trajets`
--
ALTER TABLE `trajets`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=26;

--
-- AUTO_INCREMENT pour la table `vehicules`
--
ALTER TABLE `vehicules`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `incidents`
--
ALTER TABLE `incidents`
  ADD CONSTRAINT `incidents_ibfk_1` FOREIGN KEY (`trajet_id`) REFERENCES `trajets` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `tarifs`
--
ALTER TABLE `tarifs`
  ADD CONSTRAINT `tarifs_ibfk_1` FOREIGN KEY (`ligne_id`) REFERENCES `lignes` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `trajets`
--
ALTER TABLE `trajets`
  ADD CONSTRAINT `trajets_ibfk_1` FOREIGN KEY (`vehicule_id`) REFERENCES `vehicules` (`id`),
  ADD CONSTRAINT `trajets_ibfk_2` FOREIGN KEY (`chauffeur_id`) REFERENCES `chauffeurs` (`id`),
  ADD CONSTRAINT `trajets_ibfk_3` FOREIGN KEY (`ligne_id`) REFERENCES `lignes` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
