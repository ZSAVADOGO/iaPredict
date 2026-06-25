DROP DATABASE IF EXISTS db_MSECU;
CREATE DATABASE db_MSECU CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE db_MSECU;

-- 1. Table Centrale : Personne (Physique ou Morale - Référence ONI/NIF)
CREATE TABLE personne (
    id_personne INT AUTO_INCREMENT PRIMARY KEY,
    type_personne VARCHAR(10) NOT NULL CHECK (type_personne IN ('PHYSIQUE', 'MORALE')),
    nom_raison_sociale VARCHAR(150),
    nom VARCHAR(100), 
    prenom VARCHAR(100),
    numero_cnib VARCHAR(50) UNIQUE, -- CNIB si Physique, NIF si Morale
    telephone VARCHAR(20),
    ville VARCHAR(100) DEFAULT 'Ouagadougou'
);

-- 2. Table des Infractions (Liée à la personne et/ou au véhicule via l'immatriculation)
CREATE TABLE infraction (
    id_infraction INT AUTO_INCREMENT PRIMARY KEY,
    id_personne INT NOT NULL,
    type_infraction VARCHAR(100) NOT NULL, -- ex: Excès de vitesse, Conduite sans casque, Vol
    degre_infraction VARCHAR(20) NOT NULL CHECK (degre_infraction IN ('CONTRAVENTION', 'DELIT', 'CRIME')),
    plaque_vehicule_associe VARCHAR(20) NULL, -- Lien logique facultatif avec la DGTTM
    montant_amende DECIMAL(10,2) NULL,
    statut_paiement VARCHAR(20) DEFAULT 'NON_PAYE' CHECK (statut_paiement IN ('PAYE', 'NON_PAYE', 'ANNULE')),
    date_infraction DATETIME NOT NULL,
    lieu_infraction VARCHAR(100) NOT NULL,
    FOREIGN KEY (id_personne) REFERENCES personne(id_personne) ON DELETE RESTRICT
);

-- 3. Table des Personnes Recherchées (Avis de recherche / Mandats d'arrêt)
CREATE TABLE personne_recherchee (
    id_recherche INT AUTO_INCREMENT PRIMARY KEY,
    id_personne INT NULL, -- NULL si l'identité exacte n'est pas encore connue (X)
    alias_pseudonyme VARCHAR(100),
    motif_recherche TEXT NOT NULL,
    niveau_dangerosite VARCHAR(20) NOT NULL CHECK (niveau_dangerosite IN ('FAIBLE', 'MOYEN', 'CRITIQUE')),
    date_avis DATE NOT NULL,
    statut_recherche VARCHAR(20) DEFAULT 'ACTIF' CHECK (statut_recherche IN ('ACTIF', 'INTERPELLE', 'ARCHIVE')),
    unite_enquetrice VARCHAR(100) NOT NULL, -- ex: BCRC, Commissariat Central
    FOREIGN KEY (id_personne) REFERENCES personne(id_personne) ON DELETE SET NULL
);

-- 4. Table Supplémentaire 1 : Agents de Police (Gestion du personnel)
CREATE TABLE agent_police (
    id_agent INT AUTO_INCREMENT PRIMARY KEY,
    matricule_police VARCHAR(20) UNIQUE NOT NULL,
    nom VARCHAR(50) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    grade VARCHAR(50) NOT NULL, -- ex: Sergent, Lieutenant, Commissaire
    affectation_commissariat VARCHAR(100) NOT NULL,
    telephone VARCHAR(20)
);

-- 5. Table Supplémentaire 2 : Plaintes et Mains Courantes
CREATE TABLE plainte (
    id_plainte INT AUTO_INCREMENT PRIMARY KEY,
    numero_procès_verbal VARCHAR(50) UNIQUE NOT NULL,
    id_plaignant INT NOT NULL,
    id_suspect INT NULL,
    description_faits TEXT NOT NULL,
    date_depot DATETIME NOT NULL,
    id_agent_charge INT NOT NULL,
    statut_plainte VARCHAR(30) DEFAULT 'EN_COURS' CHECK (statut_plainte IN ('EN_COURS', 'CLASSEE_SANS_SUITE', 'DEFEREE')),
    FOREIGN KEY (id_plaignant) REFERENCES personne(id_personne) ON DELETE RESTRICT,
    FOREIGN KEY (id_suspect) REFERENCES personne(id_personne) ON DELETE SET NULL,
    FOREIGN KEY (id_agent_charge) REFERENCES agent_police(id_agent) ON DELETE RESTRICT
);

-- 6. Table Supplémentaire 3 : Gardes à Vue (Suivi des libertés)
CREATE TABLE garde_a_vue (
    id_gav INT AUTO_INCREMENT PRIMARY KEY,
    id_personne INT NOT NULL,
    motif_arrestation TEXT NOT NULL,
    date_debut DATETIME NOT NULL,
    date_fin_prevue DATETIME NOT NULL,
    date_liberation_effective DATETIME NULL,
    lieu_detention VARCHAR(100) NOT NULL, -- Quel violon (ex: Wemtenga, Paspanga)
    decision_magistrat VARCHAR(50) DEFAULT 'EN_COURS' COMMENT 'LIBERE, DEFERE, PROLONGE',
    FOREIGN KEY (id_personne) REFERENCES personne(id_personne) ON DELETE RESTRICT
);

-- 7. Table Supplémentaire 4 : Autorisations et Permis (Port d'arme civile)
CREATE TABLE permis_port_arme (
    id_permis INT AUTO_INCREMENT PRIMARY KEY,
    numero_permis VARCHAR(30) UNIQUE NOT NULL,
    id_titulaire INT NOT NULL,
    type_arme VARCHAR(50) NOT NULL, -- ex: Pistolet automatique, Fusil de chasse
    numero_serie_arme VARCHAR(50) UNIQUE NOT NULL,
    date_delivrance DATE NOT NULL,
    date_expiration DATE NOT NULL,
    statut_permis VARCHAR(20) DEFAULT 'VALIDE' CHECK (statut_permis IN ('VALIDE', 'REVOQUE', 'EXPIRE')),
    FOREIGN KEY (id_titulaire) REFERENCES personne(id_personne) ON DELETE RESTRICT
);


-- 1. Insertion des Personnes (Alignées rigoureusement sur l'ONI/CNSS/DGTTM)
INSERT INTO personne (type_personne, nom_raison_sociale, nom, prenom, numero_cnib, telephone, ville) VALUES
('PHYSIQUE', NULL, 'OUEDRAOGO', 'Ibrahim', 'B00000001', '+22670111111', 'Ouagadougou'),
('PHYSIQUE', NULL, 'TRAORE', 'Fatoumata', 'B00000002', '+22676222222', 'Bobo-Dioulasso'),
('PHYSIQUE', NULL, 'SANON', 'Pierre', 'B00000003', '+22665333333', 'Koudougou'),
('PHYSIQUE', NULL, 'ZOUNDI', 'Mariam', 'B00000004', '+22670444444', 'Ouahigouya'),
('PHYSIQUE', NULL, 'KABORE', 'Seydou', 'B00000005', '+22678555555', 'Ouagadougou'),
('PHYSIQUE', NULL, 'CONOMBO', 'Adama', 'B00000006', '+22671666666', 'Kaya'),
('PHYSIQUE', NULL, 'SOME', 'Clarisse', 'B00000007', '+22662777777', 'Gaoua'),
('PHYSIQUE', NULL, 'TIENDREBEOGO', 'Pascal', 'B00000008', '+22670888888', 'Fada N\'Gourma'),
('PHYSIQUE', NULL, 'DIALLO', 'Hama', 'B00000009', '+22676999999', 'Dori'),
('PHYSIQUE', NULL, 'YAMEOGO', 'Chantal', 'B00000010', '+22660101010', 'Koudougou'),
('MORALE', 'TELECOM BURKINA SA', NULL, NULL, 'NIF99988877A', '+22625300001', 'Ouagadougou'),
('MORALE', 'MINES DU FASO SARL', NULL, NULL, 'NIF55544433B', '+22620970002', 'Bobo-Dioulasso');

-- 2. Insertion des infractions pour 4 entités (les autres restent vierges)
INSERT INTO infraction (id_personne, type_infraction, degre_infraction, plaque_vehicule_associe, montant_amende, statut_paiement, date_infraction, lieu_infraction) VALUES
(1, 'Conduite de motocyclette sans casque protecteur', 'CONTRAVENTION', '11 SJ 4512', 3000.00, 'PAYE', '2026-03-12 08:30:00', 'Rond-point des Nations Unies, Ouaga'),
(2, 'Excès de vitesse en agglomération (> 50 km/h)', 'CONTRAVENTION', '02 LL 9988', 6000.00, 'NON_PAYE', '2026-04-05 15:45:00', 'Avenue Châlons-en-Champagne, Bobo'),
(3, 'Abus de confiance et fraude fiscale', 'DELIT', NULL, 500000.00, 'NON_PAYE', '2026-01-20 10:00:00', 'Zone Industrielle, Koudougou'),
(12, 'Non-respect des normes environnementales et minières', 'CRIME', '02 LL 0001', 5000000.00, 'NON_PAYE', '2026-05-14 11:15:00', 'Site minier, Houndé');

-- 3. Insertion dans la table Personnes Recherchées
INSERT INTO personne_recherchee (id_personne, alias_pseudonyme, motif_recherche, niveau_dangerosite, date_avis, statut_recherche, unite_enquetrice) VALUES
(3, 'Le Financier', 'Mandat d\'arrêt requis pour fraude financière majeure et fuite de capitaux', 'MOYEN', '2026-02-01', 'ACTIF', 'Brigade Centrale de Répression des Crimes Économiques'),
(NULL, 'Le Chacal', 'Auteur présumé de multiples braquages à main armée sur l\'axe Ouaga-Dori', 'CRITIQUE', '2026-05-20', 'ACTIF', 'Unité d\'Intervention Polyvalente de la Police Nationale');

-- 4. Insertion des Agents de Police
INSERT INTO agent_police (matricule_police, nom, prenom, grade, affectation_commissariat) VALUES
('POL-9912A', 'SANON', 'Jean-Baptiste', 'Commissaire', 'Commissariat Central de Ouagadougou'),
('POL-4451B', 'ZONGO', 'Moussa', 'Lieutenant', 'Commissariat de l\'Arrondissement 2, Bobo');

-- 5. Insertion des Plaintes
INSERT INTO plainte (numero_procès_verbal, id_plaignant, id_suspect, description_faits, date_depot, id_agent_charge, statut_plainte) VALUES
('PV-2026-0089', 4, 3, 'Plainte pour escroquerie sur l\'achat de matériaux de construction routiers', '2026-01-25 14:00:00', 1, 'DEFEREE');

-- 6. Insertion des Gardes à Vue
INSERT INTO garde_a_vue (id_personne, motif_arrestation, date_debut, date_fin_prevue, lieu_detention, decision_magistrat) VALUES
(1, 'Ivresse publique manifeste et refus d\'obtempérer lors d\'un contrôle routier à moto', '2026-03-12 09:00:00', '2026-03-14 09:00:00', 'Violon Commissariat Central Ouaga', 'LIBERE');

-- 7. Insertion des Permis de Port d'arme
INSERT INTO permis_port_arme (numero_permis, id_titulaire, type_arme, numero_serie_arme, date_delivrance, date_expiration) VALUES
('PA-CIV-2026-88', 5, 'Pistolet Automatique (Glock 19)', 'GLOCK-S-99210', '2026-02-10', '2029-02-10');



