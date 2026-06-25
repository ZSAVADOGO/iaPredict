-- Nettoyage de la base de données de test
DROP DATABASE IF EXISTS db_cnss;
CREATE DATABASE db_cnss CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE db_cnss;

-- 1. Table Employeur (Informations administratives et statut de cotisation)
CREATE TABLE employeur (
    id_employeur INT AUTO_INCREMENT PRIMARY KEY,
    numero_employeur VARCHAR(20) UNIQUE NOT NULL, -- Numéro d'immatriculation CNSS
    raison_sociale VARCHAR(150) NOT NULL,
    dirigeant_legal VARCHAR(100) NOT NULL,
    situation_cotisant VARCHAR(30) NOT NULL COMMENT 'A_JOUR, EN_RETARD, CONTENTIEUX',
    telephone VARCHAR(20),
    ville VARCHAR(50) DEFAULT 'Ouagadougou',
    date_immatriculation DATE NOT NULL
);

-- 2. Table Travailleur (Assuré principal de la CNSS)
CREATE TABLE travailleur (
    numero_assure VARCHAR(13) PRIMARY KEY, -- Contrainte : 12 chiffres + 1 lettre
    nom VARCHAR(50) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    date_naissance DATE NOT NULL,
	numero_cnib VARCHAR(100) NOT NULL,
    sexe CHAR(1) NOT NULL CHECK (sexe IN ('M', 'F')),
    situation_matrimoniale VARCHAR(20) DEFAULT 'CELIBATAIRE',
    telephone VARCHAR(20),
    date_immatriculation DATE NOT NULL,
    CONSTRAINT chk_numero_assure CHECK (numero_assure REGEXP '^[0-9]{12}[A-Z]$')
);

-- 3. Table Emploi (Historique des postes, salaires et lien avec l'employeur)
CREATE TABLE emploi (
    id_emploi INT AUTO_INCREMENT PRIMARY KEY,
    numero_assure VARCHAR(13) NOT NULL,
    id_employeur INT NOT NULL,
    poste VARCHAR(100) NOT NULL,
    salaire_de_base DECIMAL(12,2) NOT NULL,
    indemnites DECIMAL(12,2) DEFAULT 0.00,
    date_debut DATE NOT NULL,
    date_fin DATE NULL, -- NULL si emploi actuel
    statut_emploi VARCHAR(20) DEFAULT 'ACTIF',
    FOREIGN KEY (numero_assure) REFERENCES travailleur(numero_assure) ON DELETE CASCADE,
    FOREIGN KEY (id_employeur) REFERENCES employeur(id_employeur) ON DELETE RESTRICT
);

-- 4. Table Ayant-Droit (Conjoints et Enfants rattachés pour les prestations)
CREATE TABLE ayant_droit (
    id_ayant_droit INT AUTO_INCREMENT PRIMARY KEY,
    numero_assure VARCHAR(13) NOT NULL,
    type_ayant_droit VARCHAR(10) NOT NULL CHECK (type_ayant_droit IN ('CONJOINT', 'ENFANT')),
    nom VARCHAR(50) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    date_naissance DATE NOT NULL,
    sexe CHAR(1) NOT NULL CHECK (sexe IN ('M', 'F')),
    date_rattachement DATE NOT NULL,
    FOREIGN KEY (numero_assure) REFERENCES travailleur(numero_assure) ON DELETE CASCADE
);

-- 5. Table Cotisation (Calculée mensuellement sur la base du salaire déclaré)
CREATE TABLE cotisation (
    id_cotisation INT AUTO_INCREMENT PRIMARY KEY,
    id_emploi INT NOT NULL,
    periode_mois_annee VARCHAR(7) NOT NULL, -- Format 'MM-YYYY'
    assiette_cotisable DECIMAL(12,2) NOT NULL, -- Salaire brut plafonné ou non
    part_ouvriere DECIMAL(12,2) NOT NULL, -- Part prélevée sur le salarié
    part_patronale DECIMAL(12,2) NOT NULL, -- Part payée par l'employeur
    date_versement DATE NULL,
    FOREIGN KEY (id_emploi) REFERENCES emploi(id_emploi) ON DELETE CASCADE
);



-- 1. Insertion de 5 Employeurs (5 lignes)
INSERT INTO employeur (numero_employeur, raison_sociale, dirigeant_legal, situation_cotisant, telephone, ville, date_immatriculation) VALUES
('EMP001-BF', 'TELECOM BURKINA SA', 'Lassane SAWADOGO', 'A_JOUR', '+22625300001', 'Ouagadougou', '2010-05-12'),
('EMP002-BF', 'MINES DU FASO SARL', 'John DOE', 'EN_RETARD', '+22620970002', 'Bobo-Dioulasso', '2015-08-24'),
('EMP003-BF', 'BANQUE COMMERCIALE DU SAHEL', 'Awa DIALLO', 'A_JOUR', '+22625490003', 'Ouagadougou', '2008-01-15'),
('EMP004-BF', 'BTP DU CENTRE SAS', 'Ousmane COMPAORE', 'CONTENTIEUX', '+22624400004', 'Koudougou', '2019-11-02'),
('EMP005-BF', 'CLINIQUE INTERNATIONALE PAIX', 'Dr Sali SANOU', 'A_JOUR', '+22625360005', 'Ouagadougou', '2012-03-20');

-- 2. Insertion de 10 Travailleurs avec l'identifiant strict CNSS (10 lignes)
INSERT INTO travailleur (numero_assure, numero_cnib, nom, prenom, date_naissance, sexe, situation_matrimoniale, telephone, date_immatriculation) VALUES
('100000000001A', 'B00000001', 'OUEDRAOGO', 'Ibrahim', '1982-04-14', 'M', 'MARIE', '+22670111111', '2010-06-01'),
('100000000002B', 'B00000002', 'TRAORE', 'Fatoumata', '1988-09-23', 'F', 'MARIE', '+22676222222', '2012-04-01'),
('100000000003C', 'B00000003', 'SANON', 'Pierre', '1975-12-05', 'M', 'MARIE', '+22665333333', '2008-02-01'),
('100000000004D', 'B00000004', 'ZOUNDI', 'Mariam', '1993-01-19', 'F', 'CELIBATAIRE', '+22670444444', '2019-12-01'),
('100000000005E', 'B00000005', 'KABORE', 'Seydou', '1980-07-30', 'M', 'MARIE', '+22678555555', '2015-09-01'),
('100000000006F', 'B00000006', 'CONOMBO', 'Adama', '1985-03-11', 'M', 'CELIBATAIRE', '+22671666666', '2011-01-15'),
('100000000007G', 'B00000007', 'SOME', 'Clarisse', '1990-11-02', 'F', 'MARIE', '+22662777777', '2013-05-10'),
('100000000008H', 'B00000008', 'TIENDREBEOGO', 'Pascal', '1978-06-25', 'M', 'MARIE', '+22670888888', '2009-10-20'),
('100000000009I', 'B00000009', 'DIALLO', 'Hama', '1983-02-28', 'M', 'MARIE', '+22676999999', '2016-02-01'),
('100000000010J', 'B00000010', 'YAMEOGO', 'Chantal', '1995-08-14', 'F', 'CELIBATAIRE', '+22660101010', '2020-03-01');

-- 3. Insertion de 10 Emplois reliés (10 lignes)
INSERT INTO emploi (numero_assure, id_employeur, poste, salaire_de_base, indemnites, date_debut, date_fin, statut_emploi) VALUES
('100000000001A', 1, 'Ingénieur Télécom', 450000.00, 75000.00, '2010-06-01', NULL, 'ACTIF'),
('100000000002B', 5, 'Infirmière Major', 250000.00, 30000.00, '2012-04-01', NULL, 'ACTIF'),
('100000000003C', 3, 'Analyste Financier', 600000.00, 120000.00, '2008-02-01', NULL, 'ACTIF'),
('100000000004D', 4, 'Conducteur de Travaux', 180000.00, 20000.00, '2019-12-01', '2022-05-31', 'TERMINE'),
('100000000005E', 2, 'Géologue senior', 850000.00, 150000.00, '2015-09-01', NULL, 'ACTIF'),
('100000000006F', 1, 'Technicien Réseau', 220000.00, 25000.00, '2011-01-15', NULL, 'ACTIF'),
('100000000007G', 3, 'Guichetière', 300000.00, 40000.00, '2013-05-10', NULL, 'ACTIF'),
('100000000008H', 1, 'Comptable', 400000.00, 50000.00, '2009-10-20', NULL, 'ACTIF'),
('100000000009I', 2, 'Opérateur d\'Engins', 350000.00, 60000.00, '2016-02-01', NULL, 'ACTIF'),
('100000000010J', 4, 'Secrétaire Comptable', 150000.00, 15000.00, '2020-03-01', NULL, 'ACTIF');

-- 4. Insertion de 15 Ayants-droit (Conjoints et Enfants) (15 lignes)
INSERT INTO ayant_droit (numero_assure, type_ayant_droit, nom, prenom, date_naissance, sexe, date_rattachement) VALUES
('100000000001A', 'CONJOINT', 'OUEDRAOGO', 'Nafissatou', '1987-05-20', 'F', '2012-02-14'),
('100000000001A', 'ENFANT', 'OUEDRAOGO', 'Kader', '2014-08-11', 'M', '2014-09-01'),
('100000000001A', 'ENFANT', 'OUEDRAOGO', 'Sali', '2018-03-02', 'F', '2018-04-01'),
('100000000002B', 'CONJOINT', 'TRAORE', 'Moussa', '1984-11-30', 'M', '2013-06-10'),
('100000000002B', 'ENFANT', 'TRAORE', 'Alima', '2016-01-15', 'F', '2016-02-01'),
('100000000003C', 'CONJOINT', 'SANON', 'Marie', '1980-04-04', 'F', '2008-05-20'),
('100000000003C', 'ENFANT', 'SANON', 'Jean', '2010-09-18', 'M', '2010-10-01'),
('100000000003C', 'ENFANT', 'SANON', 'Marc', '2013-11-22', 'M', '2013-12-01'),
('100000000005E', 'CONJOINT', 'KABORE', 'Minata', '1985-02-27', 'F', '2016-01-10'),
('100000000005E', 'ENFANT', 'KABORE', 'Latifa', '2017-07-07', 'F', '2017-08-01'),
('100000000007G', 'CONJOINT', 'BARRO', 'Oumar', '1987-10-12', 'M', '2014-10-10'),
('100000000007G', 'ENFANT', 'BARRO', 'Ines', '2015-12-25', 'F', '2016-01-15'),
('100000000008H', 'CONJOINT', 'TIENDREBEOGO', 'Alice', '1982-01-01', 'F', '2010-04-12'),
('100000000009I', 'CONJOINT', 'DIALLO', 'Fatou', '1990-06-18', 'F', '2017-05-01'),
('100000000009I', 'ENFANT', 'DIALLO', 'Amadou', '2019-09-09', 'M', '2019-10-01');

-- 5. Insertion de 10 Cotisations mensuelles (Historique de paie CNSS) (10 lignes)
INSERT INTO cotisation (id_emploi, periode_mois_annee, assiette_cotisable, part_ouvriere, part_patronale, date_versement) VALUES
(1, '05-2026', 525000.00, 28875.00, 84000.00, '2026-06-05'),
(2, '05-2026', 280000.00, 15400.00, 44800.00, '2026-06-08'),
(3, '05-2026', 720000.00, 39600.00, 115200.00, '2026-06-04'),
(5, '05-2026', 1000000.00, 55000.00, 160000.00, '2026-06-10'),
(6, '05-2026', 245000.00, 13475.00, 39200.00, '2026-06-05'),
(7, '05-2026', 340000.00, 18700.00, 54400.00, '2026-06-04'),
(8, '05-2026', 450000.00, 24750.00, 72000.00, '2026-06-05'),
(9, '05-2026', 410000.00, 22550.00, 65600.00, '2026-06-12'),
(10, '05-2026', 165000.00, 9075.00, 26400.00, '2026-06-07'),
(1, '04-2026', 525000.00, 28875.00, 84000.00, '2026-05-05');