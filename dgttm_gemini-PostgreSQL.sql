-- En tant qu'expert, on nettoie d'abord l'existant pour les tests
DROP TABLE IF EXISTS taxe_annuelle CASCADE;
DROP TABLE IF EXISTS carte_grise CASCADE;
DROP TABLE IF EXISTS engin CASCADE;
DROP TABLE IF EXISTS personne CASCADE;

-- 1. Table des Propriétaires (Physique ou Moral)
CREATE TABLE personne (
    id_personne SERIAL PRIMARY KEY,
    type_personne VARCHAR(10) NOT NULL CHECK (type_personne IN ('PHYSIQUE', 'MORALE')),
    nom_raison_sociale VARCHAR(150),
	nom VARCHAR(100), 
    prenom VARCHAR(100), -- Peut être NULL pour une personne morale
    numero_cnib VARCHAR(50) UNIQUE, -- CNIB pour physique, NIF pour morale
    telephone VARCHAR(20),
    ville VARCHAR(100) DEFAULT 'Ouagadougou',
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Table des Engins (Optimisée pour le contexte burkinabè : Véhicules & Deux-roues)
CREATE TABLE engin (
    id_engin SERIAL PRIMARY KEY,
    type_engin VARCHAR(15) NOT NULL CHECK (type_engin IN ('MOTO', 'VEHICULE')),
    marque VARCHAR(50) NOT NULL, -- ex: Yamaha, Toyota, Kaizer, Rambo
    modele VARCHAR(50) NOT NULL, -- ex: Crypton, Hilux, Sirius
    numero_chassis VARCHAR(50) UNIQUE NOT NULL, -- Numéro de série obligatoire
    cylindree_cc INT, -- Très important pour les motos (ex: 110cc, 125cc)
    puissance_fiscale INT, -- Plus adapté aux voitures (ex: 7 CV)
    couleur VARCHAR(30)
);

-- 3. Table Principale : Cartes Grises
CREATE TABLE carte_grise (
    numero_carte_grise VARCHAR(50) PRIMARY KEY, -- Identifiant unique (ex: CG-BF-XXXXX)
    numero_immatriculation VARCHAR(20) UNIQUE NOT NULL, -- ex: 11 SJ 1234 ou 11 G 1234
    id_personne INT REFERENCES personne(id_personne) ON DELETE RESTRICT,
    id_engin INT REFERENCES engin(id_engin) ON DELETE RESTRICT,
    date_emission DATE NOT NULL DEFAULT CURRENT_DATE,
    centre_dgttm VARCHAR(50) DEFAULT 'Ouagadougou', -- Centre émetteur (Bobo, Koudougou, etc.)
    statut VARCHAR(20) DEFAULT 'ACTIF' CHECK (statut IN ('ACTIF', 'SUSPENDU', 'DUPLICATA'))
);

-- 4. Table Connexe Importante : Suivi des Vignettes / Taxes
CREATE TABLE taxe_annuelle (
    id_taxe SERIAL PRIMARY KEY,
    numero_carte_grise VARCHAR(50) REFERENCES carte_grise(numero_carte_grise) ON DELETE CASCADE,
    annee_fiscale INT NOT NULL,
    montant_paye DECIMAL(10,2) NOT NULL,
    date_paiement DATE NOT NULL DEFAULT CURRENT_DATE
);

-- Nettoyage préalable des données pour vos tests
TRUNCATE taxe_annuelle, carte_grise, engin, personne RESTART IDENTITY CASCADE;

-- 1. Insertion des Personnes (Physiques alignées sur l'ONI, et Morales pour les entreprises)
INSERT INTO personne (type_personne, nom_raison_sociale, nom, prenom, numero_cnib, telephone, ville) VALUES
-- Les 10 travailleurs issus des données ONI
('PHYSIQUE', NULL, 'OUEDRAOGO', 'Ibrahim', 'B00000001', '+22670111111', 'Ouagadougou'),
('PHYSIQUE', NULL, 'TRAORE', 'Fatoumata', 'B00000002', '+22676222222', 'Bobo-Dioulasso'),
('PHYSIQUE', NULL, 'SANON', 'Pierre', 'B00000003', '+22665333333', 'Koudougou'),
('PHYSIQUE', NULL, 'ZOUNDI', 'Mariam', 'B00000004', '+22670444444', 'Ouahigouya'),
('PHYSIQUE', NULL, 'KABORE', 'Seydou', 'B00000005', '+22678555555', 'Ouagadougou'),
('PHYSIQUE', NULL, 'CONOMBO', 'Adama', 'B00000006', '+22671666666', 'Kaya'),
('PHYSIQUE', NULL, 'SOME', 'Clarisse', 'B00000007', '+22662777777', 'Gaoua'),
('PHYSIQUE', NULL, 'TIENDREBEOGO', 'Pascal', 'B00000008', '+22670888888', 'Fada N''Gourma'),
('PHYSIQUE', NULL, 'DIALLO', 'Hama', 'B00000009', '+22676999999', 'Dori'),
('PHYSIQUE', NULL, 'YAMEOGO', 'Chantal', 'B00000010', '+22660101010', 'Koudougou'),
-- Personnes Morales (Entreprises/Employeurs de la CNSS)
('MORALE', 'TELECOM BURKINA SA', NULL, NULL, 'NIF99988877A', '+22625300001', 'Ouagadougou'),
('MORALE', 'MINES DU FASO SARL', NULL, NULL, 'NIF55544433B', '+22620970002', 'Bobo-Dioulasso'),
('MORALE', 'BANQUE COMMERCIALE DU SAHEL', NULL, NULL, 'NIF11122233C', '+22625490003', 'Ouagadougou');

-- 2. Insertion des Engins (Forte dominance de motos à deux roues, réalité du Burkina)
INSERT INTO engin (type_engin, marque, modele, numero_chassis, cylindree_cc, puissance_fiscale, couleur) VALUES
('MOTO', 'YAMAHA', 'Crypton FI', 'CHASSIS-MOTO-00001', 115, NULL, 'Rouge'),   -- Moto Ibrahim
('MOTO', 'KAIZER', 'Rambo', 'CHASSIS-MOTO-00002', 125, NULL, 'Noir'),        -- Moto Fatoumata
('VEHICULE', 'TOYOTA', 'Hilux', 'CHASSIS-AUTO-00003', NULL, 10, 'Blanc'),     -- Auto Sté Telecom
('MOTO', 'APSION', 'Sirius', 'CHASSIS-MOTO-00004', 110, NULL, 'Bleu'),        -- Moto Mariam
('VEHICULE', 'MERCEDES', 'C200', 'CHASSIS-AUTO-00005', NULL, 9, 'Gris'),       -- Auto Pierre
('MOTO', 'YAMAHA', 'Sirius', 'CHASSIS-MOTO-00006', 110, NULL, 'Noir'),       -- Moto Seydou
('MOTO', 'KAWASAKI', 'Ninja', 'CHASSIS-MOTO-00007', 300, NULL, 'Vert'),      -- Moto Adama
('VEHICULE', 'PEUGEOT', '3008', 'CHASSIS-AUTO-00008', NULL, 7, 'Bleu'),        -- Auto Clarisse
('MOTO', 'HAOUJUE', '110-5', 'CHASSIS-MOTO-00009', 110, NULL, 'Rouge'),       -- Moto Pascal
('VEHICULE', 'NISSAN', 'Patrol', 'CHASSIS-AUTO-00010', NULL, 14, 'Noir');     -- Auto Mines du Faso

-- 3. Insertion des Cartes Grises (Liaison Personnes et Engins)
INSERT INTO carte_grise (numero_carte_grise, numero_immatriculation, id_personne, id_engin, date_emission, centre_dgttm, statut) VALUES
('CG-BF-2026-00001', '11 SJ 4512', 1, 1, '2026-01-10', 'Ouagadougou', 'ACTIF'),   -- Ibrahim (Moto)
('CG-BF-2026-00002', '02 LL 9988', 2, 2, '2026-02-15', 'Bobo-Dioulasso', 'ACTIF'),-- Fatoumata (Moto)
('CG-BF-2026-00003', '11 G 5000',  11, 3, '2026-03-01', 'Ouagadougou', 'ACTIF'),  -- Telecom BF (Hilux)
('CG-BF-2026-00004', '10 KM 1414', 4, 4, '2026-03-20', 'Ouahigouya', 'ACTIF'),    -- Mariam (Moto)
('CG-BF-2026-00005', '11 SJ 0077', 3, 5, '2026-04-05', 'Koudougou', 'ACTIF'),     -- Pierre (Mercedes)
('CG-BF-2026-00006', '11 SJ 8833', 5, 6, '2026-04-12', 'Ouagadougou', 'ACTIF'),   -- Seydou (Moto)
('CG-BF-2026-00007', '09 MT 7766', 6, 7, '2026-04-28', 'Kaya', 'ACTIF'),          -- Adama (Moto)
('CG-BF-2026-00008', '05 LL 1122', 7, 8, '2026-05-02', 'Gaoua', 'ACTIF'),         -- Clarisse (Peugeot)
('CG-BF-2026-00009', '11 SJ 9900', 8, 9, '2026-05-18', 'Ouagadougou', 'ACTIF'),   -- Pascal (Moto)
('CG-BF-2026-00010', '02 LL 0001', 12, 10, '2026-06-01', 'Bobo-Dioulasso', 'ACTIF');-- Mines du Faso (Nissan)

-- 4. Insertion du suivi des Vignettes (Taxes annuelles de circulation)
INSERT INTO taxe_annuelle (numero_carte_grise, annee_fiscale, montant_paye, date_paiement) VALUES
('CG-BF-2026-00001', 2026, 2000.00, '2026-01-12'),  -- Moto Ibrahim
('CG-BF-2026-00002', 2026, 2000.00, '2026-02-17'),  -- Moto Fatoumata
('CG-BF-2026-00003', 2026, 30000.00, '2026-03-02'), -- Véhicule de société (Telecom)
('CG-BF-2026-00004', 2026, 2000.00, '2026-03-22'),  -- Moto Mariam
('CG-BF-2026-00005', 2026, 15000.00, '2026-04-06'), -- Mercedes Pierre
('CG-BF-2026-00006', 2026, 2000.00, '2026-04-15'),  -- Moto Seydou
('CG-BF-2026-00007', 2026, 3000.00, '2026-05-01'),  -- Grosse cylindrée Adama
('CG-BF-2026-00008', 2026, 10000.00, '2026-05-04'), -- Peugeot Clarisse
('CG-BF-2026-00009', 2026, 2000.00, '2026-05-19');  -- Moto Pascal
-- Note: La carte 'CG-BF-2026-00010' (Mines du Faso) est laissée sans taxe payée exprès pour simuler un défaut de paiement