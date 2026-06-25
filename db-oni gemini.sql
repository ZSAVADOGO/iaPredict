DROP DATABASE IF EXISTS db_oni;
CREATE DATABASE db_oni CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE db_oni;

-- 1. Table Principale : Individu (Données d'identification de base)
CREATE TABLE individu (
    numero_cnib VARCHAR(9) PRIMARY KEY, -- Contrainte strict : B + 8 chiffres (ex: B12345678)
    nom VARCHAR(50) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    date_naissance DATE NOT NULL,
    lieu_naissance VARCHAR(100) NOT NULL,
    taille_cm INT NOT NULL COMMENT 'Taille en centimètres',
    profession VARCHAR(100) DEFAULT 'Sans profession',
    CONSTRAINT chk_numero_cnib CHECK (numero_cnib REGEXP '^B[0-9]{8}$')
);

-- 2. Table des Contacts d'Urgence (Personnes à prévenir - Relation 1:N pour la flexibilité)
CREATE TABLE personne_a_prevenir (
    id_contact INT AUTO_INCREMENT PRIMARY KEY,
    numero_cnib_individu VARCHAR(9) NOT NULL,
    nom_complet VARCHAR(150) NOT NULL,
    lien_parente VARCHAR(50) NOT NULL COMMENT 'CONJOINT, PERE, MERE, FRERE, ONCLE, etc.',
    telephone VARCHAR(20) NOT NULL,
    ville_residence VARCHAR(50) DEFAULT 'Ouagadougou',
    FOREIGN KEY (numero_cnib_individu) REFERENCES individu(numero_cnib) ON DELETE CASCADE
);

-- 3. Table des Documents CNIB (Suivi des cartes émises, dates de validité)
CREATE TABLE carte_identite (
    id_carte INT AUTO_INCREMENT PRIMARY KEY,
    numero_cnib VARCHAR(9) NOT NULL,
    date_etablissement DATE NOT NULL,
    date_expiration DATE NOT NULL,
    centre_collecte VARCHAR(100) NOT NULL COMMENT 'Commissariat, Mairie, etc.',
    statut_carte VARCHAR(20) DEFAULT 'VALIDE' CHECK (statut_carte IN ('VALIDE', 'EXPIRE', 'PERDU')),
    FOREIGN KEY (numero_cnib) REFERENCES individu(numero_cnib) ON DELETE CASCADE
);


-- Insertion des 10 Individus (Identités  croisées avec le format CNIB de l'ONI)
INSERT INTO individu (numero_cnib, nom, prenom, date_naissance, lieu_naissance, taille_cm, profession) VALUES
('B00000001', 'OUEDRAOGO', 'Ibrahim', '1982-04-14', 'Ouagadougou', 175, 'Ingénieur Télécom'),
('B00000002', 'TRAORE', 'Fatoumata', '1988-09-23', 'Bobo-Dioulasso', 168, 'Infirmière'),
('B00000003', 'SANON', 'Pierre', '1975-12-05', 'Koudougou', 182, 'Analyste Financier'),
('B00000004', 'ZOUNDI', 'Mariam', '1993-01-19', 'Ouahigouya', 165, 'Conducteur de Travaux'),
('B00000005', 'KABORE', 'Seydou', '1980-07-30', 'Tenkodogo', 178, 'Géologue'),
('B00000006', 'CONOMBO', 'Adama', '1985-03-11', 'Kaya', 170, 'Technicien Réseau'),
('B00000007', 'SOME', 'Clarisse', '1990-11-02', 'Gaoua', 162, 'Guichetière'),
('B00000008', 'TIENDREBEOGO', 'Pascal', '1978-06-25', 'Fada N\'Gourma', 174, 'Comptable'),
('B00000009', 'DIALLO', 'Hama', '1983-02-28', 'Dori', 180, 'Opérateur d\'Engins'),
('B00000010', 'YAMEOGO', 'Chantal', '1995-08-14', 'Koudougou', 167, 'Secrétaire');

-- Insertion des Personnes à prévenir (Liées aux CNIB)
INSERT INTO personne_a_prevenir (numero_cnib_individu, nom_complet, lien_parente, telephone, ville_residence) VALUES
('B00000001', 'OUEDRAOGO Nafissatou', 'CONJOINT', '+22670223344', 'Ouagadougou'),
('B00000002', 'TRAORE Moussa', 'CONJOINT', '+22676889900', 'Bobo-Dioulasso'),
('B00000003', 'SANON Marie', 'CONJOINT', '+22665112233', 'Koudougou'),
('B00000004', 'ZOUNDI Alassane', 'PERE', '+22670556677', 'Ouahigouya'),
('B00000005', 'KABORE Minata', 'CONJOINT', '+22678990011', 'Ouagadougou'),
('B00000006', 'CONOMBO Philippe', 'FRERE', '+22671445566', 'Kaya'),
('B00000007', 'BARRO Oumar', 'CONJOINT', '+22662112233', 'Ouagadougou'),
('B00000008', 'TIENDREBEOGO Alice', 'CONJOINT', '+22670443322', 'Ouagadougou'),
('B00000009', 'DIALLO Fatou', 'CONJOINT', '+22676112233', 'Dori'),
('B00000010', 'YAMEOGO Antoine', 'PERE', '+22660554433', 'Koudougou');

-- Insertion de l'historique des cartes CNIB émanant de l'ONI
INSERT INTO carte_identite (numero_cnib, date_etablissement, date_expiration, centre_collecte) VALUES
('B00000001', '2020-05-10', '2030-05-10', 'Commissariat Central Ouaga'),
('B00000002', '2021-08-15', '2031-08-15', 'Mairie de Bobo Hues'),
('B00000003', '2019-02-20', '2029-02-20', 'Commissariat Koudougou'),
('B00000004', '2022-11-02', '2032-11-02', 'Centre ONI Ouahigouya'),
('B00000005', '2020-01-14', '2030-01-14', 'Commissariat Tenkodogo'),
('B00000006', '2023-04-18', '2033-04-18', 'Mairie de Kaya'),
('B00000007', '2021-06-05', '2031-06-05', 'Centre ONI Gaoua'),
('B00000008', '2018-09-12', '2028-09-12', 'Commissariat Fada'),
('B00000009', '2022-03-25', '2032-03-25', 'Commissariat Dori'),
('B00000010', '2024-07-01', '2034-07-01', 'Mairie Koudougou');