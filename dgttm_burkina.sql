-- =============================================================
--  BASE DE DONNÉES DGTTM — BURKINA FASO
--  Direction Générale des Transports Terrestres et Maritimes
--  PostgreSQL — Schéma complet avec données de test
-- =============================================================

-- Nettoyage propre avant création
DROP SCHEMA IF EXISTS dgttm CASCADE;
CREATE SCHEMA dgttm;
SET search_path TO dgttm;

-- =============================================================
--  EXTENSIONS
-- =============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS unaccent;

-- =============================================================
-- 1. TABLE : REGION
-- =============================================================
CREATE TABLE region (
    id_region       SERIAL PRIMARY KEY,
    code_region     VARCHAR(10)  NOT NULL UNIQUE,
    nom_region      VARCHAR(100) NOT NULL
);

-- =============================================================
-- 2. TABLE : PROVINCE
-- =============================================================
CREATE TABLE province (
    id_province     SERIAL PRIMARY KEY,
    code_province   VARCHAR(10)  NOT NULL UNIQUE,
    nom_province    VARCHAR(100) NOT NULL,
    id_region       INT NOT NULL REFERENCES region(id_region)
);

-- =============================================================
-- 3. TABLE : COMMUNE
-- =============================================================
CREATE TABLE commune (
    id_commune      SERIAL PRIMARY KEY,
    code_commune    VARCHAR(10)  NOT NULL UNIQUE,
    nom_commune     VARCHAR(100) NOT NULL,
    id_province     INT NOT NULL REFERENCES province(id_province)
);

-- =============================================================
-- 4. TABLE : PERSONNE
--    type_personne : 'PHYSIQUE' | 'MORALE'
--    Les champs spécifiques morale/physique cohabitent,
--    des contraintes CHECK garantissent la cohérence.
-- =============================================================
CREATE TABLE personne (
    id_personne         SERIAL PRIMARY KEY,
    type_personne       VARCHAR(10) NOT NULL CHECK (type_personne IN ('PHYSIQUE','MORALE')),

    -- Personne physique
    nom                 VARCHAR(100),
    prenom              VARCHAR(100),
    date_naissance      DATE,
    lieu_naissance      VARCHAR(100),
    sexe                CHAR(1) CHECK (sexe IN ('M','F')),
    nationalite         VARCHAR(50) DEFAULT 'Burkinabè',
    num_cni             VARCHAR(30) UNIQUE,      -- Carte Nationale d'Identité
    num_passeport       VARCHAR(30) UNIQUE,

    -- Personne morale
    raison_sociale      VARCHAR(200),
    numero_rccm         VARCHAR(50) UNIQUE,      -- Registre du Commerce
    numero_ifu          VARCHAR(30) UNIQUE,      -- Identifiant Fiscal Unique
    forme_juridique     VARCHAR(50),             -- SA, SARL, GIE, Association…
    representant_legal  VARCHAR(200),

    -- Coordonnées communes
    telephone           VARCHAR(20),
    telephone2          VARCHAR(20),
    email               VARCHAR(150),
    adresse             TEXT,
    id_commune          INT REFERENCES commune(id_commune),

    date_creation       TIMESTAMP DEFAULT NOW(),
    actif               BOOLEAN DEFAULT TRUE,

    -- Contraintes de cohérence
    CONSTRAINT chk_physique CHECK (
        type_personne <> 'PHYSIQUE' OR (nom IS NOT NULL AND prenom IS NOT NULL)
    ),
    CONSTRAINT chk_morale CHECK (
        type_personne <> 'MORALE' OR (raison_sociale IS NOT NULL AND numero_rccm IS NOT NULL)
    )
);

-- =============================================================
-- 5. TABLE : CATEGORIE_ENGIN
--    Référentiel des catégories d'engins (A, B, C, D…)
-- =============================================================
CREATE TABLE categorie_engin (
    id_categorie    SERIAL PRIMARY KEY,
    code_categorie  VARCHAR(5)   NOT NULL UNIQUE,  -- A, B, C, D, E…
    libelle         VARCHAR(100) NOT NULL,
    description     TEXT
);

-- =============================================================
-- 6. TABLE : TYPE_ENGIN
--    MOTO_2_ROUES, TRICYCLE, VEHICULE_LEGER, VEHICULE_LOURD,
--    BUS_MINIBUS, ENGIN_AGRICOLE, BATEAU…
-- =============================================================
CREATE TABLE type_engin (
    id_type_engin   SERIAL PRIMARY KEY,
    code_type       VARCHAR(30)  NOT NULL UNIQUE,
    libelle         VARCHAR(100) NOT NULL,
    id_categorie    INT REFERENCES categorie_engin(id_categorie)
);

-- =============================================================
-- 7. TABLE : MARQUE
-- =============================================================
CREATE TABLE marque (
    id_marque   SERIAL PRIMARY KEY,
    nom_marque  VARCHAR(100) NOT NULL UNIQUE,
    pays_origine VARCHAR(60)
);

-- =============================================================
-- 8. TABLE : MODELE
-- =============================================================
CREATE TABLE modele (
    id_modele   SERIAL PRIMARY KEY,
    nom_modele  VARCHAR(100) NOT NULL,
    id_marque   INT NOT NULL REFERENCES marque(id_marque),
    annee_debut SMALLINT,
    annee_fin   SMALLINT,
    UNIQUE(nom_modele, id_marque)
);

-- =============================================================
-- 9. TABLE : ENGIN
--    Représente le véhicule/moto physique
-- =============================================================
CREATE TABLE engin (
    id_engin            SERIAL PRIMARY KEY,
    numero_chassis      VARCHAR(50)  NOT NULL UNIQUE,  -- VIN/NIV
    numero_moteur       VARCHAR(50),
    id_type_engin       INT NOT NULL REFERENCES type_engin(id_type_engin),
    id_modele           INT REFERENCES modele(id_modele),
    annee_fabrication   SMALLINT,
    couleur             VARCHAR(40),
    puissance_fiscale   SMALLINT,                      -- chevaux fiscaux
    cylindree           INT,                           -- cm³ (crucial pour motos)
    nombre_places       SMALLINT DEFAULT 2,
    poids_vide          NUMERIC(8,2),                  -- kg
    charge_utile        NUMERIC(8,2),                  -- kg (camions)
    energie             VARCHAR(20) CHECK (energie IN ('ESSENCE','DIESEL','ELECTRIQUE','HYBRIDE','GPL')),
    usage               VARCHAR(30) CHECK (usage IN ('PERSONNEL','COMMERCIAL','TRANSPORT_COMMUN','AGRICOLE','SPECIAL')),
    importateur         VARCHAR(200),
    date_mise_circulation DATE,
    actif               BOOLEAN DEFAULT TRUE,
    date_creation       TIMESTAMP DEFAULT NOW()
);

-- =============================================================
-- 10. TABLE : CARTE_GRISE
--     Table principale — identifiée par numéro de carte grise
-- =============================================================
CREATE TABLE carte_grise (
    id_carte_grise      SERIAL PRIMARY KEY,
    numero_cg           VARCHAR(30)  NOT NULL UNIQUE,  -- ex: BF-CG-2024-000123
    id_engin            INT NOT NULL REFERENCES engin(id_engin),
    id_proprietaire     INT NOT NULL REFERENCES personne(id_personne),
    id_commune_emission INT REFERENCES commune(id_commune),  -- bureau émetteur

    -- Immatriculation
    immatriculation     VARCHAR(20) NOT NULL UNIQUE,   -- ex: 11A5432 BF
    date_immatriculation DATE NOT NULL,
    type_immatriculation VARCHAR(30) CHECK (type_immatriculation IN
        ('PREMIERE_MISE','MUTATION','DUPLICATA','REIMMATRICULATION')),

    -- Validité
    date_emission       DATE NOT NULL DEFAULT CURRENT_DATE,
    date_expiration     DATE,                          -- NULL = illimité (carte grise permanente)
    statut              VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
                        CHECK (statut IN ('ACTIVE','SUSPENDUE','ANNULEE','PERDUE','VOLEE')),

    -- Usage / affectation
    usage_declare       VARCHAR(30),
    zone_circulation    VARCHAR(50) DEFAULT 'NATIONALE',

    -- Traçabilité
    agent_emetteur      VARCHAR(100),
    observations        TEXT,
    date_creation       TIMESTAMP DEFAULT NOW(),
    date_modification   TIMESTAMP DEFAULT NOW()
);

-- Index sur immatriculation (recherche fréquente)
CREATE INDEX idx_cg_immatriculation ON carte_grise(immatriculation);
CREATE INDEX idx_cg_proprietaire    ON carte_grise(id_proprietaire);
CREATE INDEX idx_cg_engin           ON carte_grise(id_engin);

-- =============================================================
-- 11. TABLE : HISTORIQUE_CARTE_GRISE
--     Traçe chaque mutation / changement de propriétaire
-- =============================================================
CREATE TABLE historique_carte_grise (
    id_historique       SERIAL PRIMARY KEY,
    id_carte_grise      INT NOT NULL REFERENCES carte_grise(id_carte_grise),
    id_ancien_proprietaire INT REFERENCES personne(id_personne),
    id_nouveau_proprietaire INT REFERENCES personne(id_personne),
    motif               VARCHAR(50) CHECK (motif IN
        ('VENTE','DONATION','HERITAGE','SAISIE','MUTATION_ADMINISTRATIVE')),
    date_mutation       DATE NOT NULL DEFAULT CURRENT_DATE,
    acte_notarie        VARCHAR(100),
    agent_traitant      VARCHAR(100),
    observations        TEXT,
    date_creation       TIMESTAMP DEFAULT NOW()
);

-- =============================================================
-- 12. TABLE : VISITE_TECHNIQUE
-- =============================================================
CREATE TABLE visite_technique (
    id_visite           SERIAL PRIMARY KEY,
    id_engin            INT NOT NULL REFERENCES engin(id_engin),
    id_carte_grise      INT REFERENCES carte_grise(id_carte_grise),
    date_visite         DATE NOT NULL,
    date_expiration     DATE NOT NULL,
    resultat            VARCHAR(20) NOT NULL CHECK (resultat IN ('FAVORABLE','DEFAVORABLE','CONTRE_VISITE')),
    centre_controle     VARCHAR(150),
    numero_vignette     VARCHAR(30) UNIQUE,
    controleur          VARCHAR(100),
    observations        TEXT,
    date_creation       TIMESTAMP DEFAULT NOW()
);

-- =============================================================
-- 13. TABLE : ASSURANCE
-- =============================================================
CREATE TABLE assurance (
    id_assurance        SERIAL PRIMARY KEY,
    id_engin            INT NOT NULL REFERENCES engin(id_engin),
    compagnie           VARCHAR(150) NOT NULL,
    numero_police       VARCHAR(50)  NOT NULL UNIQUE,
    type_assurance      VARCHAR(30) CHECK (type_assurance IN
        ('RESPONSABILITE_CIVILE','TOUS_RISQUES','TIERCE_COLLISION')),
    date_debut          DATE NOT NULL,
    date_fin            DATE NOT NULL,
    montant_prime       NUMERIC(12,2),
    statut              VARCHAR(20) DEFAULT 'ACTIVE' CHECK (statut IN ('ACTIVE','EXPIREE','RESILIEE')),
    date_creation       TIMESTAMP DEFAULT NOW()
);

-- =============================================================
-- 14. TABLE : PERMIS_CONDUIRE
-- =============================================================
CREATE TABLE permis_conduire (
    id_permis           SERIAL PRIMARY KEY,
    numero_permis       VARCHAR(30) NOT NULL UNIQUE,
    id_personne         INT NOT NULL REFERENCES personne(id_personne),
    date_obtention      DATE NOT NULL,
    date_expiration     DATE,
    categories          VARCHAR(30),               -- A, B, C, D, E
    lieu_delivrance     VARCHAR(100),
    statut              VARCHAR(20) DEFAULT 'VALIDE' CHECK (statut IN
        ('VALIDE','EXPIRE','SUSPENDU','ANNULE','PERDU')),
    date_creation       TIMESTAMP DEFAULT NOW()
);

-- =============================================================
-- 15. TABLE : INFRACTION
-- =============================================================
CREATE TABLE infraction (
    id_infraction       SERIAL PRIMARY KEY,
    id_engin            INT REFERENCES engin(id_engin),
    id_conducteur       INT REFERENCES personne(id_personne),
    id_carte_grise      INT REFERENCES carte_grise(id_carte_grise),
    date_infraction     TIMESTAMP NOT NULL,
    lieu                VARCHAR(200),
    nature_infraction   VARCHAR(100),              -- excès de vitesse, défaut d'assurance…
    montant_amende      NUMERIC(10,2),
    statut_paiement     VARCHAR(20) DEFAULT 'EN_ATTENTE' CHECK (statut_paiement IN
        ('EN_ATTENTE','PAYE','CONTESTE','ANNULE')),
    agent_verbalisant   VARCHAR(100),
    date_creation       TIMESTAMP DEFAULT NOW()
);

-- =============================================================
--  DONNÉES DE TEST
-- =============================================================

-- --- Régions ---
INSERT INTO region (code_region, nom_region) VALUES
('CENTRE',    'Centre'),
('HAUTS_B',   'Hauts-Bassins'),
('SAHEL',     'Sahel'),
('EST',       'Est'),
('SUD_OUEST', 'Sud-Ouest'),
('BOUCLE_M',  'Boucle du Mouhoun');

-- --- Provinces ---
INSERT INTO province (code_province, nom_province, id_region) VALUES
('KADIOGO',   'Kadiogo',        1),
('HOUET',     'Houet',          2),
('OUDALAN',   'Oudalan',        3),
('GNAGNA',    'Gnagna',         4),
('PONI',      'Poni',           5),
('MOUHOUN',   'Mouhoun',        6);

-- --- Communes ---
INSERT INTO commune (code_commune, nom_commune, id_province) VALUES
('OUAGA',     'Ouagadougou',    1),
('BOULMI',    'Boulmiougou',    1),
('NONGR',     'Nongremassom',   1),
('BOBO',      'Bobo-Dioulasso', 2),
('GOROM',     'Gorom-Gorom',    3),
('BOGANDE',   'Bogandé',        4),
('GAOUA',     'Gaoua',          5),
('DEDOUGOU',  'Dédougou',       6);

-- --- Catégories engins ---
INSERT INTO categorie_engin (code_categorie, libelle, description) VALUES
('A',  'Motocycles',         'Motos 2 roues et tricycles motorisés'),
('B',  'Véhicules légers',   'Voitures particulières jusqu''à 3,5 T'),
('C',  'Véhicules lourds',   'Camions et poids lourds > 3,5 T'),
('D',  'Transport commun',   'Bus, minibus, transport de personnes'),
('E',  'Engins spéciaux',    'Engins agricoles, de chantier'),
('F',  'Embarcations',       'Pirogues et bateaux à moteur');

-- --- Types engin ---
INSERT INTO type_engin (code_type, libelle, id_categorie) VALUES
('MOTO_2_ROUES',      'Moto 2 roues',              1),
('TRICYCLE_MOTO',     'Tricycle motorisé (Keke)',   1),
('SCOOTER',           'Scooter',                    1),
('MOTO_TAXI',         'Moto-taxi (Zémidjan)',       1),
('VOITURE_PART',      'Voiture particulière',       2),
('TAXI_VILLE',        'Taxi ville',                 2),
('PICKUP',            'Pick-up / 4x4',              2),
('MINIBUS',           'Minibus (14-30 places)',      4),
('BUS',               'Bus (> 30 places)',           4),
('CAMION_LEGER',      'Camion léger (< 7,5 T)',      3),
('CAMION_LOURD',      'Camion lourd (>= 7,5 T)',     3),
('TRACTEUR_AGRI',     'Tracteur agricole',           5),
('PIROGUE_MOTEUR',    'Pirogue à moteur',            6);

-- --- Marques ---
INSERT INTO marque (nom_marque, pays_origine) VALUES
('Honda',       'Japon'),
('Yamaha',      'Japon'),
('Suzuki',      'Japon'),
('TVS',         'Inde'),
('Bajaj',       'Inde'),
('Hero',        'Inde'),
('Lifan',       'Chine'),
('Jincheng',    'Chine'),
('Toyota',      'Japon'),
('Isuzu',       'Japon'),
('Mercedes',    'Allemagne'),
('Renault',     'France'),
('Peugeot',     'France'),
('Mitsubishi',  'Japon');

-- --- Modèles (motos dominants au Burkina) ---
INSERT INTO modele (nom_modele, id_marque, annee_debut, annee_fin) VALUES
-- Honda
('CG 125',          1, 1976, NULL),
('CB 125',          1, 2000, NULL),
('Wave 110',        1, 2005, NULL),
('XR 125',          1, 2003, NULL),
-- Yamaha
('YBR 125',         2, 2005, NULL),
('FZ 125',          2, 2012, NULL),
('CRUX 110',        2, 2003, NULL),
-- TVS
('Apache 150',      4, 2006, NULL),
('Star City 110',   4, 2005, NULL),
-- Bajaj
('Boxer 100',       5, 2000, NULL),
('Pulsar 135',      5, 2009, NULL),
-- Lifan
('LF 125',          7, 2008, NULL),
-- Jincheng
('JC 125',          8, 2005, NULL),
-- Toyota
('Hilux',           9, 1968, NULL),
('Land Cruiser',    9, 1951, NULL),
-- Isuzu
('D-Max',          10, 2002, NULL),
-- Renault
('Kangoo',         12, 1997, NULL);

-- =============================================================
--  PERSONNES — Physiques
-- =============================================================
INSERT INTO personne (type_personne, nom, prenom, date_naissance, lieu_naissance,
    sexe, nationalite, num_cni, telephone, email, adresse, id_commune) VALUES
('PHYSIQUE', 'OUEDRAOGO', 'Issouf',     '1985-03-14', 'Ouagadougou', 'M', 'Burkinabè', 'CNI-BF-001234', '70112233', 'issouf.ouedraogo@gmail.com',    'Secteur 15, Ouagadougou', 1),
('PHYSIQUE', 'SAWADOGO',  'Mariam',     '1990-07-22', 'Koudougou',   'F', 'Burkinabè', 'CNI-BF-005678', '76543210', 'mariam.sawadogo@yahoo.fr',       'Secteur 22, Ouagadougou', 2),
('PHYSIQUE', 'TRAORE',    'Souleymane', '1978-11-05', 'Bobo-Dioulasso','M','Burkinabè','CNI-BF-009012', '65778899', NULL,                              'Quartier Bindougousso, Bobo', 4),
('PHYSIQUE', 'ZONGO',     'Aminata',    '1995-01-30', 'Ouagadougou', 'F', 'Burkinabè', 'CNI-BF-012345', '77889900', 'aminata.zongo@outlook.com',      'Secteur 30, Ouagadougou', 3),
('PHYSIQUE', 'KABORE',    'Jean-Paul',  '1970-06-18', 'Kaya',        'M', 'Burkinabè', 'CNI-BF-023456', '70001122', 'jp.kabore@dgttm.bf',             'Secteur 4, Ouagadougou',  1),
('PHYSIQUE', 'COMPAORE',  'Fatoumata',  '1988-09-25', 'Gorom-Gorom', 'F', 'Burkinabè', 'CNI-BF-034567', '76223344', NULL,                              'Gorom-Gorom, Oudalan',    5),
('PHYSIQUE', 'BARRY',     'Moussa',     '1982-04-12', 'Dédougou',    'M', 'Burkinabè', 'CNI-BF-045678', '65334455', 'moussa.barry@bf.com',            'Dédougou, Mouhoun',       8),
('PHYSIQUE', 'SOME',      'Céline',     '1993-12-08', 'Gaoua',       'F', 'Burkinabè', 'CNI-BF-056789', '70556677', 'celine.some@gmail.com',          'Gaoua, Poni',             7),
('PHYSIQUE', 'DIALLO',    'Ibrahim',    '1975-08-20', 'Bobo-Dioulasso','M','Burkinabè','CNI-BF-067890', '76667788', 'ibrahim.diallo@transpbf.com',    'Secteur 8, Bobo',         4),
('PHYSIQUE', 'NIKIEMA',   'Pascal',     '2000-02-14', 'Ouagadougou', 'M', 'Burkinabè', 'CNI-BF-078901', '70778899', NULL,                              'Secteur 12, Ouagadougou', 1);

-- Personnes morales (entreprises)
INSERT INTO personne (type_personne, raison_sociale, numero_rccm, numero_ifu,
    forme_juridique, representant_legal, telephone, email, adresse, id_commune) VALUES
('MORALE', 'TRANSPORT EXPRESS BURKINA SARL', 'BF-OUA-2015-B-1234', 'IFU-00112233',
    'SARL', 'OUEDRAOGO Karim', '25312233', 'contact@teb.bf', 'Avenue Kwame Nkrumah, Ouagadougou', 1),
('MORALE', 'SOCIETE BURKINABE DE TRANSIT SAS', 'BF-OUA-2010-A-5678', 'IFU-00445566',
    'SAS',  'SAWADOGO Issa',   '25334455', 'info@sbt.bf',     'Zone Industrielle, Ouagadougou', 1),
('MORALE', 'MOTO TAXI ASSOCIATION BOBO', 'BF-BOB-2018-C-9012', 'IFU-00778899',
    'GIE',  'TRAORE Mamadou',  '70991122', 'mtab@gmail.com',  'Secteur 2, Bobo-Dioulasso', 4);

-- =============================================================
--  ENGINS
-- =============================================================
INSERT INTO engin (numero_chassis, numero_moteur, id_type_engin, id_modele,
    annee_fabrication, couleur, puissance_fiscale, cylindree, nombre_places,
    energie, usage, date_mise_circulation) VALUES
-- Motos 2 roues (dominantes)
('JH2PC35CCPM100001', 'PC35E-100001', 1,  1,  2020, 'Rouge',   2,  125, 2, 'ESSENCE', 'PERSONNEL',         '2020-03-15'),
('JH2PC35CCPM100002', 'PC35E-100002', 4,  1,  2019, 'Bleu',    2,  125, 2, 'ESSENCE', 'COMMERCIAL',        '2019-06-01'),  -- Zémidjan
('JH2PC35CCPM100003', 'PC35E-100003', 1,  3,  2021, 'Noir',    2,  110, 2, 'ESSENCE', 'PERSONNEL',         '2021-01-20'),
('JH2PC35CCPM100004', 'PC35E-100004', 1,  5,  2018, 'Gris',    2,  125, 2, 'ESSENCE', 'PERSONNEL',         '2018-09-10'),
('JH2PC35CCPM100005', 'PC35E-100005', 3,  3,  2022, 'Blanc',   2,  110, 2, 'ESSENCE', 'PERSONNEL',         '2022-02-28'),
('TVS001BFKADI2023',  'TVS001-2023',  1,  8,  2023, 'Orange',  2,  150, 2, 'ESSENCE', 'COMMERCIAL',        '2023-05-10'),  -- Moto taxi
('BAJ001BFBOBO2021',  'BAJ001-2021',  1,  10, 2021, 'Vert',    2,  100, 2, 'ESSENCE', 'PERSONNEL',         '2021-07-15'),
('LIF001BFSAHEL2020', 'LIF001-2020',  1,  12, 2020, 'Jaune',   2,  125, 2, 'ESSENCE', 'PERSONNEL',         '2020-11-03'),
-- Tricycle / Keke Napep
('TRI001BFOUAG2022',  'TRI001-2022',  2,  11, 2022, 'Jaune',   3,  200, 3, 'ESSENCE', 'TRANSPORT_COMMUN',  '2022-04-18'),
-- Véhicules légers
('JTFBT22P100123456', 'GRJ200-123456',5,  14, 2018, 'Blanc',   7,  2700,5, 'DIESEL',  'PERSONNEL',         '2018-12-01'),
('JTFBT22P100234567', 'GRJ200-234567',6,  14, 2016, 'Jaune',   7,  2700,5, 'DIESEL',  'COMMERCIAL',        '2016-08-20'),  -- Taxi
('JTFBT22P100345678', 'GRJ200-345678',7,  15, 2019, 'Blanc',   9,  4000,5, 'DIESEL',  'PERSONNEL',         '2019-03-05'),
-- Minibus / transport commun
('MB001BFTRANSP2017', 'MB001-2017',   8,  NULL,2017,'Blanc',   14, 2500,25,'DIESEL',  'TRANSPORT_COMMUN',  '2017-01-10'),
-- Camion
('CAMION001BF2015',   'CAM001-2015',  11, NULL,2015,'Blanc',   25,NULL, 3, 'DIESEL',  'COMMERCIAL',        '2015-06-01');

-- =============================================================
--  CARTES GRISES
-- =============================================================
INSERT INTO carte_grise (numero_cg, id_engin, id_proprietaire, id_commune_emission,
    immatriculation, date_immatriculation, type_immatriculation,
    date_emission, date_expiration, statut, usage_declare, agent_emetteur) VALUES
('BF-CG-2020-000001', 1,  1,  1, '11A5432 BF', '2020-03-16', 'PREMIERE_MISE',      '2020-03-16', NULL, 'ACTIVE',    'PERSONNEL',        'Agent KABORÉ T.'),
('BF-CG-2019-000045', 2,  2,  1, '09Z1234 BF', '2019-06-02', 'PREMIERE_MISE',      '2019-06-02', NULL, 'ACTIVE',    'TRANSPORT_COMMUN', 'Agent SAWADOGO A.'),
('BF-CG-2021-000102', 3,  3,  4, '21B7890 BF', '2021-01-21', 'PREMIERE_MISE',      '2021-01-21', NULL, 'ACTIVE',    'PERSONNEL',        'Agent TRAORE S.'),
('BF-CG-2018-000233', 4,  4,  1, '18C3456 BF', '2018-09-11', 'PREMIERE_MISE',      '2018-09-11', NULL, 'ACTIVE',    'PERSONNEL',        'Agent ZONGO M.'),
('BF-CG-2022-000301', 5,  5,  3, '22D9012 BF', '2022-03-01', 'PREMIERE_MISE',      '2022-03-01', NULL, 'ACTIVE',    'PERSONNEL',        'Agent KABORÉ T.'),
('BF-CG-2023-000412', 6,  6,  1, '23E4567 BF', '2023-05-11', 'PREMIERE_MISE',      '2023-05-11', NULL, 'ACTIVE',    'TRANSPORT_COMMUN', 'Agent COMPAORE R.'),
('BF-CG-2021-000533', 7,  7,  4, '21F8901 BF', '2021-07-16', 'PREMIERE_MISE',      '2021-07-16', NULL, 'ACTIVE',    'PERSONNEL',        'Agent BARRY K.'),
('BF-CG-2020-000601', 8,  8,  8, '20G2345 BF', '2020-11-04', 'PREMIERE_MISE',      '2020-11-04', NULL, 'ACTIVE',    'PERSONNEL',        'Agent SOME L.'),
-- Tricycle entreprise
('BF-CG-2022-000750', 9,  11, 4, '22H6789 BF', '2022-04-19', 'PREMIERE_MISE',      '2022-04-19', NULL, 'ACTIVE',    'TRANSPORT_COMMUN', 'Agent DIALLO F.'),
-- Véhicules
('BF-CG-2018-001001', 10, 9,  1, '18K1111 BF', '2018-12-02', 'PREMIERE_MISE',      '2018-12-02', NULL, 'ACTIVE',    'PERSONNEL',        'Agent NIKIEMA O.'),
('BF-CG-2016-001045', 11, 10, 1, '16L2222 BF', '2016-08-21', 'PREMIERE_MISE',      '2016-08-21', NULL, 'ACTIVE',    'COMMERCIAL',       'Agent KABORÉ T.'),
-- Mutation (changement de propriétaire)
('BF-CG-2023-001200', 12, 5,  1, '19M3333 BF', '2023-06-01', 'MUTATION',           '2023-06-01', NULL, 'ACTIVE',    'PERSONNEL',        'Agent SAWADOGO A.'),
-- Minibus société
('BF-CG-2017-002001', 13, 11, 1, '17N4444 BF', '2017-01-11', 'PREMIERE_MISE',      '2017-01-11', NULL, 'ACTIVE',    'TRANSPORT_COMMUN', 'Agent TRAORE S.'),
-- Camion société
('BF-CG-2015-003001', 14, 12, 1, '15P5555 BF', '2015-06-02', 'PREMIERE_MISE',      '2015-06-02', NULL, 'ACTIVE',    'COMMERCIAL',       'Agent COMPAORE R.');

-- =============================================================
--  HISTORIQUE — Mutation de la carte grise 12 (ancien proprio = personne 3)
-- =============================================================
INSERT INTO historique_carte_grise (id_carte_grise, id_ancien_proprietaire,
    id_nouveau_proprietaire, motif, date_mutation, agent_traitant, observations) VALUES
(12, 3, 5, 'VENTE', '2023-06-01', 'Agent SAWADOGO A.', 'Vente de gré à gré, acte sous seing privé');

-- =============================================================
--  VISITES TECHNIQUES
-- =============================================================
INSERT INTO visite_technique (id_engin, id_carte_grise, date_visite, date_expiration,
    resultat, centre_controle, numero_vignette, controleur) VALUES
(1,  1,  '2024-01-10', '2025-01-10', 'FAVORABLE',    'Centre VT Ouagadougou Nord',  'VT-2024-00123', 'Tech. OUEDRAOGO B.'),
(2,  2,  '2024-02-05', '2025-02-05', 'FAVORABLE',    'Centre VT Ouagadougou Sud',   'VT-2024-00234', 'Tech. SAWADOGO C.'),
(10, 10, '2023-11-20', '2024-11-20', 'FAVORABLE',    'Centre VT Ouagadougou Nord',  'VT-2023-00890', 'Tech. TRAORE D.'),
(11, 11, '2023-06-15', '2024-06-15', 'DEFAVORABLE',  'Centre VT Ouagadougou Sud',   NULL,             'Tech. ZONGO F.'),
(11, 11, '2023-07-10', '2024-07-10', 'FAVORABLE',    'Centre VT Ouagadougou Sud',   'VT-2023-00901', 'Tech. ZONGO F.'),
(13, 13, '2024-03-01', '2025-03-01', 'FAVORABLE',    'Centre VT Bobo-Dioulasso',    'VT-2024-00456', 'Tech. KABORÉ H.'),
(14, 14, '2023-09-18', '2024-09-18', 'CONTRE_VISITE','Centre VT Ouagadougou Nord',  NULL,             'Tech. NIKIEMA P.');

-- =============================================================
--  ASSURANCES
-- =============================================================
INSERT INTO assurance (id_engin, compagnie, numero_police, type_assurance,
    date_debut, date_fin, montant_prime, statut) VALUES
(1,  'ALLIANZ Burkina',       'ALL-2024-001234', 'RESPONSABILITE_CIVILE', '2024-01-01', '2024-12-31', 15000,  'ACTIVE'),
(2,  'UAB Assurance',         'UAB-2024-005678', 'RESPONSABILITE_CIVILE', '2024-01-01', '2024-12-31', 15000,  'ACTIVE'),
(3,  'SONAR Assurance',       'SON-2024-009012', 'RESPONSABILITE_CIVILE', '2024-01-01', '2024-12-31', 15000,  'ACTIVE'),
(4,  'ALLIANZ Burkina',       'ALL-2023-003456', 'RESPONSABILITE_CIVILE', '2023-06-01', '2024-05-31', 15000,  'EXPIREE'),
(5,  'ASS Burkina Assurance', 'ASS-2024-007890', 'RESPONSABILITE_CIVILE', '2024-03-01', '2025-02-28', 15000,  'ACTIVE'),
(10, 'ALLIANZ Burkina',       'ALL-2024-010001', 'TOUS_RISQUES',          '2024-01-01', '2024-12-31', 250000, 'ACTIVE'),
(11, 'UAB Assurance',         'UAB-2023-010002', 'RESPONSABILITE_CIVILE', '2023-01-01', '2023-12-31', 80000,  'EXPIREE'),
(13, 'SONAR Assurance',       'SON-2024-010003', 'RESPONSABILITE_CIVILE', '2024-01-01', '2024-12-31', 120000, 'ACTIVE'),
(14, 'ASS Burkina Assurance', 'ASS-2024-010004', 'TOUS_RISQUES',          '2024-01-01', '2024-12-31', 350000, 'ACTIVE');

-- =============================================================
--  PERMIS DE CONDUIRE
-- =============================================================
INSERT INTO permis_conduire (numero_permis, id_personne, date_obtention,
    date_expiration, categories, lieu_delivrance, statut) VALUES
('PC-BF-2015-001234', 1,  '2015-05-20', NULL,         'A,B',   'DGTTM Ouagadougou', 'VALIDE'),
('PC-BF-2018-005678', 2,  '2018-08-14', NULL,         'A',     'DGTTM Ouagadougou', 'VALIDE'),
('PC-BF-2010-009012', 3,  '2010-03-02', NULL,         'A,B,C', 'DGTTM Bobo-Dioulasso','VALIDE'),
('PC-BF-2019-012345', 4,  '2019-11-30', NULL,         'A',     'DGTTM Ouagadougou', 'VALIDE'),
('PC-BF-2005-023456', 5,  '2005-07-12', NULL,         'B,C,D', 'DGTTM Ouagadougou', 'VALIDE'),
('PC-BF-2020-034567', 7,  '2020-04-05', NULL,         'A,B',   'DGTTM Dédougou',    'VALIDE'),
('PC-BF-2016-045678', 9,  '2016-09-22', NULL,         'A,B,C,D','DGTTM Bobo-Dioulasso','VALIDE'),
('PC-BF-2022-056789', 10, '2022-06-18', NULL,         'A',     'DGTTM Ouagadougou', 'VALIDE');

-- =============================================================
--  INFRACTIONS
-- =============================================================
INSERT INTO infraction (id_engin, id_conducteur, id_carte_grise,
    date_infraction, lieu, nature_infraction, montant_amende,
    statut_paiement, agent_verbalisant) VALUES
(2,  2,  2,  '2024-03-15 08:30', 'Carrefour Nation, Ouagadougou',      'Défaut de casque',              2500,  'PAYE',      'Agent OUEDRAOGO R.'),
(4,  4,  4,  '2024-04-02 14:00', 'Boulevard des Tensoba, Ouagadougou', 'Excès de vitesse (> 80 km/h)',  10000, 'EN_ATTENTE','Agent SAWADOGO T.'),
(11, 10, 11, '2023-08-10 10:15', 'Route de Bobo, Ouagadougou',         'Défaut de visite technique',    15000, 'PAYE',      'Agent TRAORE M.'),
(14, 9,  14, '2024-01-22 07:45', 'Entrée Ouagadougou RN1',             'Surcharge (dépassement PTAC)',  50000, 'CONTESTE',  'Agent KABORÉ P.'),
(6,  6,  6,  '2024-05-08 16:20', 'Secteur 15, Ouagadougou',            'Moto-taxi sans autorisation',   5000,  'EN_ATTENTE','Agent ZONGO A.');

-- =============================================================
--  VUES UTILES
-- =============================================================

-- Vue complète carte grise
CREATE VIEW v_carte_grise_complete AS
SELECT
    cg.numero_cg,
    cg.immatriculation,
    cg.statut                                          AS statut_cg,
    cg.date_immatriculation,
    cg.type_immatriculation,
    -- Propriétaire
    CASE p.type_personne
        WHEN 'PHYSIQUE' THEN p.nom || ' ' || p.prenom
        ELSE p.raison_sociale
    END                                                AS proprietaire,
    p.type_personne,
    p.telephone,
    -- Engin
    te.libelle                                         AS type_engin,
    ma.nom_marque,
    mo.nom_modele,
    e.annee_fabrication,
    e.immatriculation_engin,
    e.numero_chassis,
    e.cylindree,
    e.couleur,
    e.energie,
    e.usage,
    -- Localisation
    co.nom_commune                                     AS commune_emission
FROM carte_grise cg
JOIN engin       e   ON e.id_engin       = cg.id_engin
JOIN personne    p   ON p.id_personne    = cg.id_proprietaire
JOIN type_engin  te  ON te.id_type_engin = e.id_type_engin
LEFT JOIN modele mo  ON mo.id_modele     = e.id_modele
LEFT JOIN marque ma  ON ma.id_marque     = mo.id_marque
LEFT JOIN commune co ON co.id_commune    = cg.id_commune_emission;

-- Correction : la table engin n'a pas de colonne immatriculation_engin
-- On crée la vue sans ce champ
CREATE OR REPLACE VIEW v_carte_grise_complete AS
SELECT
    cg.numero_cg,
    cg.immatriculation,
    cg.statut                                          AS statut_cg,
    cg.date_immatriculation,
    cg.type_immatriculation,
    CASE p.type_personne
        WHEN 'PHYSIQUE' THEN p.nom || ' ' || p.prenom
        ELSE p.raison_sociale
    END                                                AS proprietaire,
    p.type_personne,
    p.telephone,
    te.libelle                                         AS type_engin,
    ma.nom_marque,
    mo.nom_modele,
    e.annee_fabrication,
    e.numero_chassis,
    e.cylindree,
    e.couleur,
    e.energie,
    e.usage,
    co.nom_commune                                     AS commune_emission
FROM carte_grise cg
JOIN engin       e   ON e.id_engin       = cg.id_engin
JOIN personne    p   ON p.id_personne    = cg.id_proprietaire
JOIN type_engin  te  ON te.id_type_engin = e.id_type_engin
LEFT JOIN modele mo  ON mo.id_modele     = e.id_modele
LEFT JOIN marque ma  ON ma.id_marque     = mo.id_marque
LEFT JOIN commune co ON co.id_commune    = cg.id_commune_emission;

-- Vue statistiques par type d'engin
CREATE VIEW v_stats_type_engin AS
SELECT
    te.libelle                AS type_engin,
    ca.libelle                AS categorie,
    COUNT(e.id_engin)         AS nb_engins,
    COUNT(cg.id_carte_grise)  AS nb_cartes_grises_actives
FROM type_engin  te
JOIN categorie_engin ca ON ca.id_categorie  = te.id_categorie
LEFT JOIN engin  e   ON e.id_type_engin = te.id_type_engin
LEFT JOIN carte_grise cg ON cg.id_engin = e.id_engin AND cg.statut = 'ACTIVE'
GROUP BY te.libelle, ca.libelle
ORDER BY nb_engins DESC;

-- Vue assurances expirées
CREATE VIEW v_assurances_expirees AS
SELECT
    cg.immatriculation,
    CASE p.type_personne
        WHEN 'PHYSIQUE' THEN p.nom || ' ' || p.prenom
        ELSE p.raison_sociale
    END AS proprietaire,
    p.telephone,
    a.compagnie,
    a.numero_police,
    a.date_fin,
    te.libelle AS type_engin
FROM assurance   a
JOIN engin       e   ON e.id_engin       = a.id_engin
JOIN carte_grise cg  ON cg.id_engin      = e.id_engin AND cg.statut = 'ACTIVE'
JOIN personne    p   ON p.id_personne    = cg.id_proprietaire
JOIN type_engin  te  ON te.id_type_engin = e.id_type_engin
WHERE a.statut = 'EXPIREE' OR a.date_fin < CURRENT_DATE;

-- =============================================================
--  REQUÊTES EXEMPLES (commentées)
-- =============================================================

-- 1. Toutes les motos et leur carte grise active
-- SELECT * FROM v_carte_grise_complete WHERE type_engin ILIKE '%moto%';

-- 2. Statistiques par type d'engin
-- SELECT * FROM v_stats_type_engin;

-- 3. Engins avec assurance expirée
-- SELECT * FROM v_assurances_expirees;

-- 4. Historique mutations pour une immatriculation
-- SELECT h.*, p1.nom ancien, p2.nom nouveau
-- FROM historique_carte_grise h
-- JOIN carte_grise cg ON cg.id_carte_grise = h.id_carte_grise
-- JOIN personne p1 ON p1.id_personne = h.id_ancien_proprietaire
-- JOIN personne p2 ON p2.id_personne = h.id_nouveau_proprietaire
-- WHERE cg.immatriculation = '19M3333 BF';

-- 5. Infractions non réglées
-- SELECT * FROM infraction WHERE statut_paiement = 'EN_ATTENTE';
