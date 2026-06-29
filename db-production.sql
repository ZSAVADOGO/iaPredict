
SET FOREIGN_KEY_CHECKS = 0;
DROP DATABASE IF EXISTS db_production;
CREATE DATABASE db_production CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE db_production;

-- ============================================================
-- TABLE 1 : CATEGORIES DE PRODUITS
-- ============================================================
CREATE TABLE categories (
    id_categorie    INT AUTO_INCREMENT PRIMARY KEY,
    code_categorie  VARCHAR(10) NOT NULL UNIQUE,
    nom_categorie   VARCHAR(100) NOT NULL,
    description     VARCHAR(255),
    marge_cible     DECIMAL(5,2) DEFAULT 30.00,  -- % marge visée
    actif           TINYINT(1) DEFAULT 1,
    date_creation   DATE NOT NULL
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 2 : PRODUITS
-- ============================================================
CREATE TABLE produits (
    id_produit      INT AUTO_INCREMENT PRIMARY KEY,
    id_categorie    INT NOT NULL,
    reference       VARCHAR(20) NOT NULL UNIQUE,
    designation     VARCHAR(150) NOT NULL,
    prix_achat      DECIMAL(10,2) NOT NULL,
    prix_vente      DECIMAL(10,2) NOT NULL,
    stock_actuel    INT DEFAULT 0,
    stock_min       INT DEFAULT 10,
    stock_max       INT DEFAULT 500,
    unite           VARCHAR(20) DEFAULT 'pcs',
    actif           TINYINT(1) DEFAULT 1,
    FOREIGN KEY (id_categorie) REFERENCES categories(id_categorie)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 3 : FOURNISSEURS
-- ============================================================
CREATE TABLE fournisseurs (
    id_fournisseur  INT AUTO_INCREMENT PRIMARY KEY,
    code_fournisseur VARCHAR(10) NOT NULL UNIQUE,
    raison_sociale  VARCHAR(150) NOT NULL,
    pays            VARCHAR(60) NOT NULL,
    ville           VARCHAR(80),
    email           VARCHAR(120),
    telephone       VARCHAR(25),
    delai_livraison INT DEFAULT 7,          -- jours
    note_qualite    DECIMAL(3,1) DEFAULT 3.0, -- /5
    actif           TINYINT(1) DEFAULT 1
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 4 : CLIENTS
-- ============================================================
CREATE TABLE clients (
    id_client       INT AUTO_INCREMENT PRIMARY KEY,
    code_client     VARCHAR(10) NOT NULL UNIQUE,
    raison_sociale  VARCHAR(150) NOT NULL,
    segment         ENUM('PME','GE','PARTICULIER','ADMINISTRATION') DEFAULT 'PME',
    pays            VARCHAR(60) DEFAULT 'France',
    ville           VARCHAR(80),
    email           VARCHAR(120),
    telephone       VARCHAR(25),
    limite_credit   DECIMAL(12,2) DEFAULT 50000.00,
    actif           TINYINT(1) DEFAULT 1
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 5 : COMMANDES ACHAT (vers fournisseurs)
-- ============================================================
CREATE TABLE commandes_achat (
    id_commande_achat   INT AUTO_INCREMENT PRIMARY KEY,
    id_fournisseur      INT NOT NULL,
    numero_commande     VARCHAR(20) NOT NULL UNIQUE,
    date_commande       DATE NOT NULL,
    date_livraison_prev DATE,
    date_livraison_reel DATE,
    statut              ENUM('BROUILLON','ENVOYEE','CONFIRMEE','LIVREE','ANNULEE') DEFAULT 'BROUILLON',
    montant_ht          DECIMAL(12,2) DEFAULT 0.00,
    montant_tva         DECIMAL(12,2) DEFAULT 0.00,
    montant_ttc         DECIMAL(12,2) DEFAULT 0.00,
    notes               VARCHAR(500),
    FOREIGN KEY (id_fournisseur) REFERENCES fournisseurs(id_fournisseur)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 6 : LIGNES COMMANDE ACHAT
-- ============================================================
CREATE TABLE lignes_achat (
    id_ligne_achat      INT AUTO_INCREMENT PRIMARY KEY,
    id_commande_achat   INT NOT NULL,
    id_produit          INT NOT NULL,
    quantite_commandee  INT NOT NULL,
    quantite_recue      INT DEFAULT 0,
    prix_unitaire_ht    DECIMAL(10,4) NOT NULL,
    taux_tva            DECIMAL(5,2) DEFAULT 20.00,
    montant_ligne_ht    DECIMAL(12,2),
    FOREIGN KEY (id_commande_achat) REFERENCES commandes_achat(id_commande_achat),
    FOREIGN KEY (id_produit) REFERENCES produits(id_produit)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 7 : COMMANDES VENTE (vers clients)
-- ============================================================
CREATE TABLE commandes_vente (
    id_commande_vente   INT AUTO_INCREMENT PRIMARY KEY,
    id_client           INT NOT NULL,
    numero_commande     VARCHAR(20) NOT NULL UNIQUE,
    date_commande       DATE NOT NULL,
    date_livraison_prev DATE,
    date_livraison_reel DATE,
    statut              ENUM('BROUILLON','CONFIRMEE','EN_COURS','LIVREE','FACTUREE','ANNULEE') DEFAULT 'BROUILLON',
    canal               ENUM('DIRECT','WEB','TELEPHONE','REVENDEUR') DEFAULT 'DIRECT',
    montant_ht          DECIMAL(12,2) DEFAULT 0.00,
    montant_ttc         DECIMAL(12,2) DEFAULT 0.00,
    FOREIGN KEY (id_client) REFERENCES clients(id_client)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 8 : LIGNES COMMANDE VENTE
-- ============================================================
CREATE TABLE lignes_vente (
    id_ligne_vente      INT AUTO_INCREMENT PRIMARY KEY,
    id_commande_vente   INT NOT NULL,
    id_produit          INT NOT NULL,
    quantite            INT NOT NULL,
    prix_unitaire_ht    DECIMAL(10,4) NOT NULL,
    remise_pct          DECIMAL(5,2) DEFAULT 0.00,
    taux_tva            DECIMAL(5,2) DEFAULT 20.00,
    montant_ligne_ht    DECIMAL(12,2),
    FOREIGN KEY (id_commande_vente) REFERENCES commandes_vente(id_commande_vente),
    FOREIGN KEY (id_produit) REFERENCES produits(id_produit)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 9 : MOUVEMENTS DE STOCK
-- ============================================================
CREATE TABLE mouvements_stock (
    id_mouvement        INT AUTO_INCREMENT PRIMARY KEY,
    id_produit          INT NOT NULL,
    type_mouvement      ENUM('ENTREE','SORTIE','AJUSTEMENT','RETOUR') NOT NULL,
    quantite            INT NOT NULL,
    stock_avant         INT,
    stock_apres         INT,
    date_mouvement      DATETIME NOT NULL,
    reference_doc       VARCHAR(30),   -- N° commande liée
    motif               VARCHAR(200),
    FOREIGN KEY (id_produit) REFERENCES produits(id_produit)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 10 : FACTURES
-- ============================================================
CREATE TABLE factures (
    id_facture          INT AUTO_INCREMENT PRIMARY KEY,
    id_commande_vente   INT,
    numero_facture      VARCHAR(20) NOT NULL UNIQUE,
    id_client           INT NOT NULL,
    date_facture        DATE NOT NULL,
    date_echeance       DATE NOT NULL,
    montant_ht          DECIMAL(12,2) NOT NULL,
    montant_tva         DECIMAL(12,2) NOT NULL,
    montant_ttc         DECIMAL(12,2) NOT NULL,
    montant_regle       DECIMAL(12,2) DEFAULT 0.00,
    statut              ENUM('EMISE','PARTIELLEMENT_REGLEE','REGLEE','EN_RETARD','AVOIR') DEFAULT 'EMISE',
    FOREIGN KEY (id_commande_vente) REFERENCES commandes_vente(id_commande_vente),
    FOREIGN KEY (id_client) REFERENCES clients(id_client)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 11 : RÈGLEMENTS (paiements reçus)
-- ============================================================
CREATE TABLE reglements (
    id_reglement        INT AUTO_INCREMENT PRIMARY KEY,
    id_facture          INT NOT NULL,
    date_reglement      DATE NOT NULL,
    montant             DECIMAL(12,2) NOT NULL,
    mode_paiement       ENUM('VIREMENT','CHEQUE','CARTE','ESPECES','PRELEVEMENT') DEFAULT 'VIREMENT',
    reference_paiement  VARCHAR(50),
    FOREIGN KEY (id_facture) REFERENCES factures(id_facture)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE 12 : ALERTES STOCK (pour l'analyse)
-- ============================================================
CREATE TABLE alertes_stock (
    id_alerte           INT AUTO_INCREMENT PRIMARY KEY,
    id_produit          INT NOT NULL,
    type_alerte         ENUM('RUPTURE','STOCK_MIN','SURSTOCK') NOT NULL,
    date_alerte         DATE NOT NULL,
    stock_au_moment     INT,
    traitee             TINYINT(1) DEFAULT 0,
    FOREIGN KEY (id_produit) REFERENCES produits(id_produit)
) ENGINE=InnoDB;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- DONNÉES DE RÉFÉRENCE (fixes)
-- ============================================================

INSERT INTO categories (code_categorie, nom_categorie, description, marge_cible, date_creation) VALUES
('ELEC', 'Électronique', 'Composants et appareils électroniques', 35.00, '2020-01-01'),
('INFO', 'Informatique', 'Matériel et périphériques informatiques', 28.00, '2020-01-01'),
('BURO', 'Bureautique', 'Fournitures et équipements de bureau', 45.00, '2020-01-01'),
('MEUB', 'Mobilier', 'Mobilier professionnel', 40.00, '2020-01-01'),
('CONS', 'Consommables', 'Consommables divers', 55.00, '2020-01-01'),
('SECU', 'Sécurité', 'Équipements de sécurité et surveillance', 38.00, '2021-03-01'),
('RESEAU', 'Réseaux & Télécom', 'Infrastructure réseau et télécommunication', 32.00, '2020-01-01');

INSERT INTO produits (id_categorie, reference, designation, prix_achat, prix_vente, stock_actuel, stock_min, stock_max, unite) VALUES
(1, 'ELEC-001', 'Écran LED 27 pouces 4K', 180.00, 299.00, 85, 20, 200, 'pcs'),
(1, 'ELEC-002', 'Clavier mécanique sans fil', 45.00, 89.00, 120, 30, 300, 'pcs'),
(1, 'ELEC-003', 'Souris ergonomique Bluetooth', 22.00, 49.00, 200, 50, 400, 'pcs'),
(1, 'ELEC-004', 'Casque audio USB-C', 35.00, 79.00, 95, 20, 250, 'pcs'),
(1, 'ELEC-005', 'Webcam HD 1080p', 28.00, 65.00, 110, 25, 300, 'pcs'),
(2, 'INFO-001', 'Laptop Pro 15" i7 16GB', 750.00, 1199.00, 45, 10, 100, 'pcs'),
(2, 'INFO-002', 'PC Bureau Tour i5 8GB', 420.00, 699.00, 30, 8, 80, 'pcs'),
(2, 'INFO-003', 'SSD 1TB NVMe', 65.00, 120.00, 180, 40, 400, 'pcs'),
(2, 'INFO-004', 'Barrette RAM DDR5 32GB', 80.00, 149.00, 160, 35, 350, 'pcs'),
(2, 'INFO-005', 'Disque dur externe 4TB', 70.00, 139.00, 75, 20, 200, 'pcs'),
(3, 'BURO-001', 'Ramette papier A4 500f', 3.50, 8.00, 500, 100, 2000, 'ram'),
(3, 'BURO-002', 'Cartouche encre HP noir', 12.00, 29.00, 300, 80, 1000, 'pcs'),
(3, 'BURO-003', 'Agenda professionnel 2026', 4.50, 12.00, 250, 50, 800, 'pcs'),
(3, 'BURO-004', 'Stylos bille (boîte 50)', 5.00, 14.00, 400, 80, 1500, 'boite'),
(3, 'BURO-005', 'Classeurs A4 (lot 10)', 8.00, 19.00, 300, 60, 1000, 'lot'),
(4, 'MEUB-001', 'Bureau ergonomique réglable', 280.00, 499.00, 25, 5, 60, 'pcs'),
(4, 'MEUB-002', 'Chaise de direction cuir', 180.00, 349.00, 40, 8, 100, 'pcs'),
(4, 'MEUB-003', 'Armoire métallique 2 portes', 220.00, 389.00, 15, 3, 40, 'pcs'),
(4, 'MEUB-004', 'Table de réunion 8 places', 450.00, 799.00, 8, 2, 20, 'pcs'),
(5, 'CONS-001', 'Toner laser noir compatible', 18.00, 45.00, 400, 100, 1200, 'pcs'),
(5, 'CONS-002', 'Papier thermique rouleau', 2.00, 5.50, 800, 200, 3000, 'roul'),
(5, 'CONS-003', 'Étiquettes adhésives (500)', 6.00, 15.00, 600, 120, 2000, 'pqt'),
(6, 'SECU-001', 'Caméra IP intérieure 4MP', 55.00, 99.00, 60, 10, 150, 'pcs'),
(6, 'SECU-002', 'Badge RFID accès', 3.50, 9.00, 500, 100, 2000, 'pcs'),
(6, 'SECU-003', 'Alarme détecteur mouvement', 40.00, 85.00, 45, 10, 120, 'pcs'),
(7, 'RESEAU-001', 'Switch 24 ports Gigabit', 95.00, 179.00, 30, 5, 80, 'pcs'),
(7, 'RESEAU-002', 'Câble RJ45 Cat6 (100m)', 22.00, 49.00, 120, 20, 300, 'bob'),
(7, 'RESEAU-003', 'Routeur WiFi 6 AX3000', 75.00, 149.00, 55, 10, 150, 'pcs'),
(7, 'RESEAU-004', 'Point d''accès WiFi Pro', 85.00, 165.00, 40, 8, 100, 'pcs'),
(2, 'INFO-006', 'Imprimante laser couleur A4', 210.00, 389.00, 22, 5, 60, 'pcs');

INSERT INTO fournisseurs (code_fournisseur, raison_sociale, pays, ville, email, telephone, delai_livraison, note_qualite) VALUES
('FOURN-01', 'TechSupply Europe SAS', 'France', 'Lyon', 'commandes@techsupply.fr', '04 72 00 11 22', 5, 4.5),
('FOURN-02', 'GlobalComponents GmbH', 'Allemagne', 'Munich', 'orders@globalcomp.de', '+49 89 000 111', 8, 4.2),
('FOURN-03', 'MobilierPro SARL', 'France', 'Paris', 'achat@mobilierpro.fr', '01 44 55 66 77', 12, 4.0),
('FOURN-04', 'AsiaElec Co. Ltd', 'Chine', 'Shenzhen', 'sales@asiaelec.cn', '+86 755 0000', 21, 3.8),
('FOURN-05', 'OfficeStock SAS', 'France', 'Marseille', 'pro@officestock.fr', '04 91 22 33 44', 3, 4.7),
('FOURN-06', 'NetEquip SA', 'Belgique', 'Bruxelles', 'sales@netequip.be', '+32 2 000 111', 7, 4.3),
('FOURN-07', 'SecuriTech SARL', 'France', 'Bordeaux', 'info@securitech.fr', '05 56 00 11 22', 6, 4.1);

INSERT INTO clients (code_client, raison_sociale, segment, pays, ville, email, telephone, limite_credit) VALUES
('CLI-001', 'Groupe Aéronautique Sud', 'GE', 'France', 'Toulouse', 'achat@groupeaero.fr', '05 61 00 11 22', 500000.00),
('CLI-002', 'Cabinet Martin & Associés', 'PME', 'France', 'Paris', 'compta@cabinetmartin.fr', '01 42 33 44 55', 30000.00),
('CLI-003', 'Mairie de Bordeaux', 'ADMINISTRATION', 'France', 'Bordeaux', 'informatique@mairie-bdx.fr', '05 56 10 20 30', 100000.00),
('CLI-004', 'StartupTech SASU', 'PME', 'France', 'Nantes', 'cto@startuptech.fr', '02 40 00 11 22', 15000.00),
('CLI-005', 'Hôpital Saint-Louis', 'ADMINISTRATION', 'France', 'Paris', 'logistique@hsl.fr', '01 42 49 00 00', 200000.00),
('CLI-006', 'Retail Express SA', 'GE', 'France', 'Lyon', 'appro@retailexpress.fr', '04 72 11 22 33', 300000.00),
('CLI-007', 'École Supérieure ESIN', 'ADMINISTRATION', 'France', 'Grenoble', 'informatique@esin.fr', '04 76 00 11 22', 50000.00),
('CLI-008', 'PME Industrie Rhône', 'PME', 'France', 'Valence', 'achats@pmerhone.fr', '04 75 44 55 66', 20000.00),
('CLI-009', 'Bureau Étude Conseil', 'PME', 'France', 'Nice', 'direction@bec-conseil.fr', '04 93 00 11 22', 25000.00),
('CLI-010', 'LogisTrans International', 'GE', 'France', 'Le Havre', 'it@logistrans.fr', '02 35 00 11 22', 400000.00),
('CLI-011', 'Agence Créative Design', 'PME', 'France', 'Montpellier', 'studio@acdesign.fr', '04 67 00 11 22', 18000.00),
('CLI-012', 'Pharmacie Centrale Groupe', 'GE', 'France', 'Strasbourg', 'it@pharmaciecentrale.fr', '03 88 00 11 22', 80000.00);




 
-- ============================================================
-- PROCÉDURE : GÉNÉRATION DE ~600 LIGNES DE DONNÉES
-- sur 5 ans en arrière depuis aujourd'hui (2021-06-27 → 2026-06-27)
-- ============================================================
 
DELIMITER $$
 
DROP PROCEDURE IF EXISTS generer_donnees_erp$$
 
CREATE PROCEDURE generer_donnees_erp()
BEGIN
    -- Variables de boucle
    DECLARE v_i             INT DEFAULT 1;
    DECLARE v_j             INT DEFAULT 1;
 
    -- Variables commandes achat
    DECLARE v_nb_ca         INT DEFAULT 120;   -- commandes achat
    DECLARE v_id_fourn      INT;
    DECLARE v_date_cmd      DATE;
    DECLARE v_date_liv_prev DATE;
    DECLARE v_date_liv_reel DATE;
    DECLARE v_statut_ca     VARCHAR(20);
    DECLARE v_ht_ca         DECIMAL(12,2);
    DECLARE v_num_ca        VARCHAR(20);
    DECLARE v_id_ca         INT;
    DECLARE v_nb_lignes_ca  INT;
    DECLARE v_id_prod       INT;
    DECLARE v_qte           INT;
    DECLARE v_pu            DECIMAL(10,4);
    DECLARE v_mht           DECIMAL(12,2);
    DECLARE v_total_ht_ca   DECIMAL(12,2);
 
    -- Variables commandes vente
    DECLARE v_nb_cv         INT DEFAULT 150;  -- commandes vente
    DECLARE v_id_client     INT;
    DECLARE v_statut_cv     VARCHAR(20);
    DECLARE v_canal         VARCHAR(20);
    DECLARE v_num_cv        VARCHAR(20);
    DECLARE v_id_cv         INT;
    DECLARE v_nb_lignes_cv  INT;
    DECLARE v_pu_vente      DECIMAL(10,4);
    DECLARE v_remise        DECIMAL(5,2);
    DECLARE v_total_ht_cv   DECIMAL(12,2);
    DECLARE v_total_ttc_cv  DECIMAL(12,2);
 
    -- Variables factures / règlements
    DECLARE v_num_fact      VARCHAR(20);
    DECLARE v_id_fact       INT;
    DECLARE v_echeance      DATE;
    DECLARE v_tva_fact      DECIMAL(12,2);
    DECLARE v_ttc_fact      DECIMAL(12,2);
    DECLARE v_statut_fact   VARCHAR(30);
    DECLARE v_nb_regl       INT;
    DECLARE v_montant_regl  DECIMAL(12,2);
    DECLARE v_mode_pmt      VARCHAR(20);
 
    -- Variables stock
    DECLARE v_stock_avant   INT;
    DECLARE v_stock_apres   INT;
 
    -- Date de base : 5 ans en arrière (2021-06-27)
    DECLARE v_date_base     DATE DEFAULT DATE_SUB(CURDATE(), INTERVAL 5 YEAR);
    DECLARE v_offset_jours  INT;
    DECLARE v_jours_total   INT DEFAULT 1826; -- ~5 ans
 
    -- Seed aléatoire
    SET @seed = 42;
 
    -- -------------------------------------------------------
    -- BLOC 1 : COMMANDES ACHAT (120 commandes)
    -- -------------------------------------------------------
    SET v_i = 1;
    WHILE v_i <= v_nb_ca DO
 
        -- Date aléatoire sur 5 ans
        SET v_offset_jours  = FLOOR(RAND() * v_jours_total);
        SET v_date_cmd      = DATE_ADD(v_date_base, INTERVAL v_offset_jours DAY);
        SET v_id_fourn      = FLOOR(1 + RAND() * 7);   -- 7 fournisseurs
 
        -- Statut selon âge de la commande
        SET v_statut_ca = CASE
            WHEN v_offset_jours < 30   THEN ELT(1 + FLOOR(RAND()*3), 'BROUILLON','ENVOYEE','CONFIRMEE')
            WHEN v_offset_jours < 180  THEN ELT(1 + FLOOR(RAND()*2), 'CONFIRMEE','LIVREE')
            ELSE                             'LIVREE'
        END;
 
        SET v_date_liv_prev = DATE_ADD(v_date_cmd, INTERVAL (5 + FLOOR(RAND()*20)) DAY);
        SET v_date_liv_reel = IF(v_statut_ca = 'LIVREE',
                                 DATE_ADD(v_date_liv_prev, INTERVAL (FLOOR(RAND()*10)-3) DAY),
                                 NULL);
 
        SET v_num_ca = CONCAT('CA-', YEAR(v_date_cmd), '-', LPAD(v_i, 5, '0'));
 
        INSERT INTO commandes_achat
            (id_fournisseur, numero_commande, date_commande, date_livraison_prev, date_livraison_reel, statut, montant_ht, montant_tva, montant_ttc)
        VALUES
            (v_id_fourn, v_num_ca, v_date_cmd, v_date_liv_prev, v_date_liv_reel, v_statut_ca, 0, 0, 0);
 
        SET v_id_ca = LAST_INSERT_ID();
 
        -- Lignes achat (2 à 5 produits par commande)
        SET v_nb_lignes_ca = 2 + FLOOR(RAND() * 4);
        SET v_total_ht_ca  = 0;
        SET v_j = 1;
 
        WHILE v_j <= v_nb_lignes_ca DO
            SET v_id_prod = 1 + FLOOR(RAND() * 30);
            SET v_qte     = 5 + FLOOR(RAND() * 100);
 
            SELECT prix_achat INTO v_pu FROM produits WHERE id_produit = v_id_prod LIMIT 1;
            -- Légère variation prix achat (-5% à +5%)
            SET v_pu  = v_pu * (0.95 + RAND() * 0.10);
            SET v_mht = ROUND(v_qte * v_pu, 2);
            SET v_total_ht_ca = v_total_ht_ca + v_mht;
 
            INSERT INTO lignes_achat
                (id_commande_achat, id_produit, quantite_commandee, quantite_recue, prix_unitaire_ht, taux_tva, montant_ligne_ht)
            VALUES
                (v_id_ca, v_id_prod,
                 v_qte,
                 IF(v_statut_ca = 'LIVREE', v_qte, IF(v_statut_ca='CONFIRMEE', FLOOR(v_qte*0.5), 0)),
                 ROUND(v_pu, 4), 20.00, v_mht);
 
            -- Mouvement stock (entrée) si livré
            IF v_statut_ca = 'LIVREE' THEN
                SELECT stock_actuel INTO v_stock_avant FROM produits WHERE id_produit = v_id_prod;
                SET v_stock_apres = v_stock_avant + v_qte;
                UPDATE produits SET stock_actuel = v_stock_apres WHERE id_produit = v_id_prod;
 
                INSERT INTO mouvements_stock
                    (id_produit, type_mouvement, quantite, stock_avant, stock_apres, date_mouvement, reference_doc, motif)
                VALUES
                    (v_id_prod, 'ENTREE', v_qte, v_stock_avant, v_stock_apres,
                     CONCAT(v_date_liv_reel, ' ', LPAD(FLOOR(RAND()*24),2,'0'), ':',
                                                  LPAD(FLOOR(RAND()*60),2,'0'), ':00'),
                     v_num_ca, 'Réception commande achat');
            END IF;
 
            SET v_j = v_j + 1;
        END WHILE;
 
        -- Mise à jour totaux commande achat
        UPDATE commandes_achat SET
            montant_ht  = ROUND(v_total_ht_ca, 2),
            montant_tva = ROUND(v_total_ht_ca * 0.20, 2),
            montant_ttc = ROUND(v_total_ht_ca * 1.20, 2)
        WHERE id_commande_achat = v_id_ca;
 
        SET v_i = v_i + 1;
    END WHILE;
 
    -- -------------------------------------------------------
    -- BLOC 2 : COMMANDES VENTE (150 commandes)
    -- -------------------------------------------------------
    SET v_i = 1;
    WHILE v_i <= v_nb_cv DO
 
        SET v_offset_jours  = FLOOR(RAND() * v_jours_total);
        SET v_date_cmd      = DATE_ADD(v_date_base, INTERVAL v_offset_jours DAY);
        SET v_id_client     = 1 + FLOOR(RAND() * 12);  -- 12 clients
 
        SET v_canal = ELT(1 + FLOOR(RAND()*4), 'DIRECT','WEB','TELEPHONE','REVENDEUR');
 
        SET v_statut_cv = CASE
            WHEN v_offset_jours < 15   THEN ELT(1 + FLOOR(RAND()*2), 'BROUILLON','CONFIRMEE')
            WHEN v_offset_jours < 60   THEN ELT(1 + FLOOR(RAND()*2), 'CONFIRMEE','EN_COURS')
            WHEN v_offset_jours < 180  THEN ELT(1 + FLOOR(RAND()*2), 'LIVREE','FACTUREE')
            ELSE                            'FACTUREE'
        END;
 
        SET v_date_liv_prev = DATE_ADD(v_date_cmd, INTERVAL (3 + FLOOR(RAND()*14)) DAY);
        SET v_date_liv_reel = IF(v_statut_cv IN ('LIVREE','FACTUREE'),
                                 DATE_ADD(v_date_liv_prev, INTERVAL (FLOOR(RAND()*7)-2) DAY),
                                 NULL);
 
        SET v_num_cv = CONCAT('CV-', YEAR(v_date_cmd), '-', LPAD(v_i, 5, '0'));
 
        INSERT INTO commandes_vente
            (id_client, numero_commande, date_commande, date_livraison_prev, date_livraison_reel, statut, canal, montant_ht, montant_ttc)
        VALUES
            (v_id_client, v_num_cv, v_date_cmd, v_date_liv_prev, v_date_liv_reel, v_statut_cv, v_canal, 0, 0);
 
        SET v_id_cv = LAST_INSERT_ID();
 
        -- Lignes vente (1 à 6 produits par commande)
        SET v_nb_lignes_cv = 1 + FLOOR(RAND() * 6);
        SET v_total_ht_cv  = 0;
        SET v_j = 1;
 
        WHILE v_j <= v_nb_lignes_cv DO
            SET v_id_prod  = 1 + FLOOR(RAND() * 30);
            SET v_qte      = 1 + FLOOR(RAND() * 30);
            SET v_remise   = ELT(1 + FLOOR(RAND()*5), 0, 0, 0, 5.00, 10.00); -- 60% sans remise
 
            SELECT prix_vente INTO v_pu_vente FROM produits WHERE id_produit = v_id_prod LIMIT 1;
            SET v_pu_vente = v_pu_vente * (1 - v_remise/100);
            SET v_mht      = ROUND(v_qte * v_pu_vente, 2);
            SET v_total_ht_cv = v_total_ht_cv + v_mht;
 
            INSERT INTO lignes_vente
                (id_commande_vente, id_produit, quantite, prix_unitaire_ht, remise_pct, taux_tva, montant_ligne_ht)
            VALUES
                (v_id_cv, v_id_prod, v_qte, ROUND(v_pu_vente, 4), v_remise, 20.00, v_mht);
 
            -- Mouvement stock (sortie) si livré
            IF v_statut_cv IN ('LIVREE','FACTUREE') THEN
                SELECT stock_actuel INTO v_stock_avant FROM produits WHERE id_produit = v_id_prod;
                SET v_stock_apres = GREATEST(0, v_stock_avant - v_qte);
                UPDATE produits SET stock_actuel = v_stock_apres WHERE id_produit = v_id_prod;
 
                INSERT INTO mouvements_stock
                    (id_produit, type_mouvement, quantite, stock_avant, stock_apres, date_mouvement, reference_doc, motif)
                VALUES
                    (v_id_prod, 'SORTIE', v_qte, v_stock_avant, v_stock_apres,
                     CONCAT(COALESCE(v_date_liv_reel, v_date_cmd), ' ',
                            LPAD(FLOOR(RAND()*24),2,'0'), ':', LPAD(FLOOR(RAND()*60),2,'0'), ':00'),
                     v_num_cv, 'Expédition commande vente');
 
                -- Alerte si stock passe sous le minimum
                IF v_stock_apres < (SELECT stock_min FROM produits WHERE id_produit = v_id_prod) THEN
                    INSERT IGNORE INTO alertes_stock (id_produit, type_alerte, date_alerte, stock_au_moment, traitee)
                    VALUES (v_id_prod,
                            IF(v_stock_apres = 0, 'RUPTURE', 'STOCK_MIN'),
                            COALESCE(v_date_liv_reel, v_date_cmd),
                            v_stock_apres,
                            IF(v_offset_jours > 60, 1, 0));
                END IF;
            END IF;
 
            SET v_j = v_j + 1;
        END WHILE;
 
        SET v_total_ttc_cv = ROUND(v_total_ht_cv * 1.20, 2);
 
        UPDATE commandes_vente SET
            montant_ht  = ROUND(v_total_ht_cv, 2),
            montant_ttc = v_total_ttc_cv
        WHERE id_commande_vente = v_id_cv;
 
        -- -------------------------------------------------------
        -- FACTURE liée à la commande vente (si FACTUREE)
        -- -------------------------------------------------------
        IF v_statut_cv = 'FACTUREE' THEN
            SET v_num_fact   = CONCAT('FACT-', YEAR(v_date_cmd), '-', LPAD(v_i, 5, '0'));
            SET v_echeance   = DATE_ADD(v_date_cmd, INTERVAL 30 DAY);
            SET v_tva_fact   = ROUND(v_total_ht_cv * 0.20, 2);
            SET v_ttc_fact   = ROUND(v_total_ht_cv * 1.20, 2);
 
            -- Statut paiement réaliste
            SET v_statut_fact = CASE
                WHEN v_offset_jours > 180 THEN ELT(1 + FLOOR(RAND()*10),
                    'REGLEE','REGLEE','REGLEE','REGLEE','REGLEE','REGLEE',
                    'PARTIELLEMENT_REGLEE','EN_RETARD','REGLEE','REGLEE')
                WHEN v_offset_jours > 60  THEN ELT(1 + FLOOR(RAND()*4),
                    'REGLEE','REGLEE','PARTIELLEMENT_REGLEE','EN_RETARD')
                ELSE 'EMISE'
            END;
 
            INSERT INTO factures
                (id_commande_vente, numero_facture, id_client, date_facture, date_echeance,
                 montant_ht, montant_tva, montant_ttc, montant_regle, statut)
            VALUES
                (v_id_cv, v_num_fact, v_id_client, v_date_cmd, v_echeance,
                 ROUND(v_total_ht_cv, 2), v_tva_fact, v_ttc_fact,
                 CASE v_statut_fact
                     WHEN 'REGLEE'                THEN v_ttc_fact
                     WHEN 'PARTIELLEMENT_REGLEE'  THEN ROUND(v_ttc_fact * (0.3 + RAND()*0.5), 2)
                     ELSE 0
                 END,
                 v_statut_fact);
 
            SET v_id_fact = LAST_INSERT_ID();
 
            -- Règlement(s) si payé
            IF v_statut_fact IN ('REGLEE','PARTIELLEMENT_REGLEE') THEN
                SET v_nb_regl   = IF(v_statut_fact='REGLEE' AND RAND()>0.7, 2, 1);
                SET v_mode_pmt  = ELT(1 + FLOOR(RAND()*5), 'VIREMENT','VIREMENT','VIREMENT','CHEQUE','PRELEVEMENT');
 
                SELECT montant_regle INTO v_montant_regl FROM factures WHERE id_facture = v_id_fact;
 
                INSERT INTO reglements (id_facture, date_reglement, montant, mode_paiement, reference_paiement)
                VALUES (v_id_fact,
                        DATE_ADD(v_echeance, INTERVAL (FLOOR(RAND()*20)-5) DAY),
                        ROUND(v_montant_regl / v_nb_regl, 2),
                        v_mode_pmt,
                        CONCAT('REF-', LPAD(FLOOR(RAND()*999999), 6, '0')));
 
                IF v_nb_regl = 2 THEN
                    INSERT INTO reglements (id_facture, date_reglement, montant, mode_paiement, reference_paiement)
                    VALUES (v_id_fact,
                            DATE_ADD(v_echeance, INTERVAL (15 + FLOOR(RAND()*15)) DAY),
                            ROUND(v_montant_regl - (v_montant_regl / 2), 2),
                            v_mode_pmt,
                            CONCAT('REF-', LPAD(FLOOR(RAND()*999999), 6, '0')));
                END IF;
            END IF;
        END IF;
 
        SET v_i = v_i + 1;
    END WHILE;
 
    -- -------------------------------------------------------
    -- BLOC 3 : AJUSTEMENTS STOCK PÉRIODIQUES (30 ajustements)
    -- Simule les inventaires annuels
    -- -------------------------------------------------------
    SET v_i = 1;
    WHILE v_i <= 30 DO
        SET v_id_prod    = 1 + FLOOR(RAND() * 30);
        SET v_offset_jours = FLOOR(RAND() * v_jours_total);
        SET v_date_cmd   = DATE_ADD(v_date_base, INTERVAL v_offset_jours DAY);
 
        SELECT stock_actuel INTO v_stock_avant FROM produits WHERE id_produit = v_id_prod;
        SET v_qte        = FLOOR(RAND() * 10) - 5;  -- -5 à +5
        SET v_stock_apres = GREATEST(0, v_stock_avant + v_qte);
        UPDATE produits SET stock_actuel = v_stock_apres WHERE id_produit = v_id_prod;
 
        INSERT INTO mouvements_stock
            (id_produit, type_mouvement, quantite, stock_avant, stock_apres, date_mouvement, motif)
        VALUES
            (v_id_prod, 'AJUSTEMENT', ABS(v_qte), v_stock_avant, v_stock_apres,
             CONCAT(v_date_cmd, ' 08:00:00'), 'Inventaire périodique');
 
        SET v_i = v_i + 1;
    END WHILE;
 
    SELECT CONCAT(
        '✅ Génération terminée. ',
        (SELECT COUNT(*) FROM commandes_achat), ' commandes achat | ',
        (SELECT COUNT(*) FROM lignes_achat), ' lignes achat | ',
        (SELECT COUNT(*) FROM commandes_vente), ' commandes vente | ',
        (SELECT COUNT(*) FROM lignes_vente), ' lignes vente | ',
        (SELECT COUNT(*) FROM factures), ' factures | ',
        (SELECT COUNT(*) FROM reglements), ' règlements | ',
        (SELECT COUNT(*) FROM mouvements_stock), ' mouvements stock | ',
        (SELECT COUNT(*) FROM alertes_stock), ' alertes stock'
    ) AS resultat;
 
END$$
 
DELIMITER ;
 
-- ============================================================
-- EXÉCUTION DE LA PROCÉDURE
-- ============================================================
CALL generer_donnees_erp();
 

-- ============================================================
-- INDEX POUR PERFORMANCES D'ANALYSE
-- ============================================================
CREATE INDEX idx_ca_date    ON commandes_achat(date_commande);
CREATE INDEX idx_ca_statut  ON commandes_achat(statut);
CREATE INDEX idx_cv_date    ON commandes_vente(date_commande);
CREATE INDEX idx_cv_statut  ON commandes_vente(statut);
CREATE INDEX idx_cv_client  ON commandes_vente(id_client);
CREATE INDEX idx_fact_date  ON factures(date_facture);
CREATE INDEX idx_fact_stat  ON factures(statut);
CREATE INDEX idx_mvt_date   ON mouvements_stock(date_mouvement);
CREATE INDEX idx_mvt_prod   ON mouvements_stock(id_produit);
CREATE INDEX idx_la_prod    ON lignes_achat(id_produit);
CREATE INDEX idx_lv_prod    ON lignes_vente(id_produit);
 
-- ============================================================
-- VUES D'ANALYSE PRÊTES À L'EMPLOI
-- ============================================================
 
-- Vue 1 : CA mensuel par canal et segment client
CREATE OR REPLACE VIEW v_ca_mensuel AS
SELECT
    DATE_FORMAT(cv.date_commande, '%Y-%m') AS mois,
    YEAR(cv.date_commande)                 AS annee,
    MONTH(cv.date_commande)                AS num_mois,
    cv.canal,
    cl.segment,
    COUNT(DISTINCT cv.id_commande_vente)   AS nb_commandes,
    ROUND(SUM(cv.montant_ht), 2)           AS ca_ht,
    ROUND(SUM(cv.montant_ttc), 2)          AS ca_ttc,
    ROUND(AVG(cv.montant_ht), 2)           AS panier_moyen_ht
FROM commandes_vente cv
JOIN clients cl ON cl.id_client = cv.id_client
WHERE cv.statut IN ('LIVREE','FACTUREE')
GROUP BY DATE_FORMAT(cv.date_commande, '%Y-%m'), cv.canal, cl.segment
ORDER BY mois;
 
-- Vue 2 : Performance produits (ventes vs achats)
CREATE OR REPLACE VIEW v_perf_produits AS
SELECT
    p.id_produit,
    p.reference,
    p.designation,
    cat.nom_categorie,
    p.prix_achat,
    p.prix_vente,
    ROUND((p.prix_vente - p.prix_achat) / p.prix_vente * 100, 1) AS marge_pct,
    COALESCE(ventes.qte_vendue, 0)        AS qte_vendue,
    COALESCE(ventes.ca_ht, 0)             AS ca_vente_ht,
    COALESCE(achats.qte_achetee, 0)       AS qte_achetee,
    COALESCE(achats.cout_achat, 0)        AS cout_achat_total,
    p.stock_actuel,
    p.stock_min
FROM produits p
JOIN categories cat ON cat.id_categorie = p.id_categorie
LEFT JOIN (
    SELECT lv.id_produit,
           SUM(lv.quantite) AS qte_vendue,
           SUM(lv.montant_ligne_ht) AS ca_ht
    FROM lignes_vente lv
    JOIN commandes_vente cv ON cv.id_commande_vente = lv.id_commande_vente
    WHERE cv.statut IN ('LIVREE','FACTUREE')
    GROUP BY lv.id_produit
) ventes ON ventes.id_produit = p.id_produit
LEFT JOIN (
    SELECT la.id_produit,
           SUM(la.quantite_commandee) AS qte_achetee,
           SUM(la.montant_ligne_ht) AS cout_achat
    FROM lignes_achat la
    JOIN commandes_achat ca ON ca.id_commande_achat = la.id_commande_achat
    WHERE ca.statut = 'LIVREE'
    GROUP BY la.id_produit
) achats ON achats.id_produit = p.id_produit
ORDER BY COALESCE(ventes.ca_ht, 0) DESC;
 
-- Vue 3 : Tableau de bord financier (factures + recouvrement)
CREATE OR REPLACE VIEW v_dashboard_financier AS
SELECT
    DATE_FORMAT(f.date_facture, '%Y-%m') AS mois,
    YEAR(f.date_facture)                 AS annee,
    cl.segment,
    COUNT(f.id_facture)                  AS nb_factures,
    ROUND(SUM(f.montant_ht), 2)          AS total_facture_ht,
    ROUND(SUM(f.montant_ttc), 2)         AS total_facture_ttc,
    ROUND(SUM(f.montant_regle), 2)       AS total_regle,
    ROUND(SUM(f.montant_ttc) - SUM(f.montant_regle), 2) AS encours_client,
    ROUND(SUM(f.montant_regle) / NULLIF(SUM(f.montant_ttc),0) * 100, 1) AS taux_recouvrement_pct,
    SUM(CASE WHEN f.statut = 'EN_RETARD' THEN 1 ELSE 0 END) AS nb_retard
FROM factures f
JOIN clients cl ON cl.id_client = f.id_client
GROUP BY DATE_FORMAT(f.date_facture, '%Y-%m'), cl.segment
ORDER BY mois;
 
-- Vue 4 : Analyse achats fournisseurs (coûts, délais, qualité)
CREATE OR REPLACE VIEW v_analyse_fournisseurs AS
SELECT
    fo.id_fournisseur,
    fo.code_fournisseur,
    fo.raison_sociale,
    fo.pays,
    fo.note_qualite,
    fo.delai_livraison AS delai_contractuel_j,
    COUNT(ca.id_commande_achat)           AS nb_commandes,
    ROUND(SUM(ca.montant_ht), 2)          AS volume_achat_ht,
    ROUND(AVG(ca.montant_ht), 2)          AS panier_moyen_ht,
    ROUND(AVG(DATEDIFF(ca.date_livraison_reel, ca.date_commande)), 1) AS delai_reel_moyen_j,
    SUM(CASE WHEN ca.date_livraison_reel > ca.date_livraison_prev THEN 1 ELSE 0 END) AS nb_retards
FROM fournisseurs fo
LEFT JOIN commandes_achat ca ON ca.id_fournisseur = fo.id_fournisseur AND ca.statut = 'LIVREE'
GROUP BY fo.id_fournisseur
ORDER BY volume_achat_ht DESC;
 
-- Vue 5 : Alertes et ruptures de stock (pour prédiction)
CREATE OR REPLACE VIEW v_alertes_et_stock AS
SELECT
    p.reference,
    p.designation,
    cat.nom_categorie,
    p.stock_actuel,
    p.stock_min,
    p.stock_max,
    ROUND(p.stock_actuel / NULLIF(p.stock_max,0) * 100, 1) AS taux_remplissage_pct,
    CASE
        WHEN p.stock_actuel = 0                THEN '🔴 RUPTURE'
        WHEN p.stock_actuel <= p.stock_min     THEN '🟠 STOCK MIN'
        WHEN p.stock_actuel >= p.stock_max*0.9 THEN '🟡 SURSTOCK'
        ELSE                                        '🟢 OK'
    END AS etat_stock,
    COUNT(al.id_alerte)                    AS nb_alertes_5ans,
    MAX(al.date_alerte)                    AS derniere_alerte
FROM produits p
JOIN categories cat ON cat.id_categorie = p.id_categorie
LEFT JOIN alertes_stock al ON al.id_produit = p.id_produit
GROUP BY p.id_produit
ORDER BY p.stock_actuel ASC;
 
-- ============================================================
-- REQUÊTES D'ANALYSE PRÊTES À L'EMPLOI (exemples)
-- ============================================================
 
-- Q1 : Tendance CA annuelle
SELECT annee, ROUND(SUM(ca_ht),2) AS ca_annuel_ht,
       ROUND(SUM(nb_commandes),0) AS total_commandes
FROM v_ca_mensuel GROUP BY annee ORDER BY annee;
 
-- Q2 : Top 5 produits les plus vendus (CA)
SELECT reference, designation, nom_categorie, ca_vente_ht, qte_vendue, marge_pct
FROM v_perf_produits LIMIT 5;
 
-- Q3 : Taux de recouvrement par an
SELECT annee, ROUND(SUM(total_facture_ttc),2) AS facture,
       ROUND(SUM(total_regle),2) AS regle,
       ROUND(SUM(total_regle)/NULLIF(SUM(total_facture_ttc),0)*100,1) AS taux_pct
FROM v_dashboard_financier GROUP BY annee ORDER BY annee;
