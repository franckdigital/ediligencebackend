-- ============================================================================
-- SCRIPT SQL - CRÉATION DES TABLES DU MODULE AGENDA
-- ============================================================================
-- Ce script crée manuellement les tables si les migrations Django échouent
-- À exécuter dans la base de données de l'application
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table : core_rendezvous
-- Description : Gestion des rendez-vous individuels
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core_rendezvous (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre VARCHAR(255) NOT NULL,
    description TEXT,
    date_debut DATETIME NOT NULL,
    date_fin DATETIME NOT NULL,
    lieu VARCHAR(255),
    organisateur_id INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'prevu',
    mode VARCHAR(20) NOT NULL DEFAULT 'presentiel',
    lien_visio VARCHAR(200),
    commentaires TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organisateur_id) REFERENCES auth_user(id) ON DELETE CASCADE,
    FOREIGN KEY (participant_id) REFERENCES auth_user(id) ON DELETE CASCADE
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_rendezvous_organisateur ON core_rendezvous(organisateur_id);
CREATE INDEX IF NOT EXISTS idx_rendezvous_participant ON core_rendezvous(participant_id);
CREATE INDEX IF NOT EXISTS idx_rendezvous_date_debut ON core_rendezvous(date_debut);
CREATE INDEX IF NOT EXISTS idx_rendezvous_statut ON core_rendezvous(statut);

-- ----------------------------------------------------------------------------
-- Table : core_rendezvousdocument
-- Description : Documents associés aux rendez-vous
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core_rendezvousdocument (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rendezvous_id INTEGER NOT NULL,
    fichier VARCHAR(100) NOT NULL,
    nom VARCHAR(255) NOT NULL,
    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    uploaded_by_id INTEGER,
    FOREIGN KEY (rendezvous_id) REFERENCES core_rendezvous(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by_id) REFERENCES auth_user(id) ON DELETE SET NULL
);

-- Index
CREATE INDEX IF NOT EXISTS idx_rdvdoc_rendezvous ON core_rendezvousdocument(rendezvous_id);

-- ----------------------------------------------------------------------------
-- Table : core_reunion
-- Description : Gestion des réunions collectives
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core_reunion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intitule VARCHAR(255) NOT NULL,
    description TEXT,
    type_reunion VARCHAR(20) NOT NULL DEFAULT 'presentiel',
    date_debut DATETIME NOT NULL,
    date_fin DATETIME NOT NULL,
    lieu VARCHAR(255),
    lien_zoom VARCHAR(200),
    organisateur_id INTEGER NOT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'prevu',
    compte_rendu TEXT,
    pv_fichier VARCHAR(100),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organisateur_id) REFERENCES auth_user(id) ON DELETE CASCADE
);

-- Index
CREATE INDEX IF NOT EXISTS idx_reunion_organisateur ON core_reunion(organisateur_id);
CREATE INDEX IF NOT EXISTS idx_reunion_date_debut ON core_reunion(date_debut);
CREATE INDEX IF NOT EXISTS idx_reunion_statut ON core_reunion(statut);

-- ----------------------------------------------------------------------------
-- Table : core_reunion_participants
-- Description : Table de liaison ManyToMany entre Reunion et User
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core_reunion_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reunion_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (reunion_id) REFERENCES core_reunion(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE,
    UNIQUE (reunion_id, user_id)
);

-- Index
CREATE INDEX IF NOT EXISTS idx_reunion_part_reunion ON core_reunion_participants(reunion_id);
CREATE INDEX IF NOT EXISTS idx_reunion_part_user ON core_reunion_participants(user_id);

-- ----------------------------------------------------------------------------
-- Table : core_reunionpresence
-- Description : Suivi de la présence aux réunions
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS core_reunionpresence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reunion_id INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    present BOOLEAN NOT NULL DEFAULT 0,
    heure_arrivee TIME,
    commentaire TEXT,
    FOREIGN KEY (reunion_id) REFERENCES core_reunion(id) ON DELETE CASCADE,
    FOREIGN KEY (participant_id) REFERENCES auth_user(id) ON DELETE CASCADE,
    UNIQUE (reunion_id, participant_id)
);

-- Index
CREATE INDEX IF NOT EXISTS idx_presence_reunion ON core_reunionpresence(reunion_id);
CREATE INDEX IF NOT EXISTS idx_presence_participant ON core_reunionpresence(participant_id);

-- ============================================================================
-- DONNÉES DE TEST (Optionnel)
-- ============================================================================

-- Insérer un rendez-vous de test
-- ATTENTION : Remplacer les IDs par des IDs valides de votre base de données
/*
INSERT INTO core_rendezvous (
    titre, description, date_debut, date_fin, lieu,
    organisateur_id, participant_id, statut, mode, created_at, updated_at
) VALUES (
    'Entretien individuel de performance',
    'Évaluation annuelle des performances et objectifs',
    datetime('now', '+2 days', '+9 hours'),
    datetime('now', '+2 days', '+10 hours'),
    'Bureau du directeur',
    1,  -- Remplacer par un ID organisateur valide
    2,  -- Remplacer par un ID participant valide
    'prevu',
    'presentiel',
    datetime('now'),
    datetime('now')
);
*/

-- Insérer une réunion de test
/*
INSERT INTO core_reunion (
    intitule, description, type_reunion, date_debut, date_fin,
    lieu, organisateur_id, statut, created_at, updated_at
) VALUES (
    'Réunion de service mensuelle',
    'Ordre du jour : Bilan du mois et objectifs',
    'presentiel',
    datetime('now', '+3 days', '+10 hours'),
    datetime('now', '+3 days', '+12 hours'),
    'Salle de conférence A',
    1,  -- Remplacer par un ID organisateur valide
    'prevu',
    datetime('now'),
    datetime('now')
);
*/

-- ============================================================================
-- VÉRIFICATION
-- ============================================================================

-- Vérifier que les tables ont été créées
SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'core_%' ORDER BY name;

-- Compter les enregistrements
SELECT 'Rendez-vous' as table_name, COUNT(*) as count FROM core_rendezvous
UNION ALL
SELECT 'Documents RDV', COUNT(*) FROM core_rendezvousdocument
UNION ALL
SELECT 'Réunions', COUNT(*) FROM core_reunion
UNION ALL
SELECT 'Participants', COUNT(*) FROM core_reunion_participants
UNION ALL
SELECT 'Présences', COUNT(*) FROM core_reunionpresence;

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. Ce script est compatible SQLite (utilisé par défaut par Django)
-- 2. Pour PostgreSQL, remplacer :
--    - INTEGER PRIMARY KEY AUTOINCREMENT par SERIAL PRIMARY KEY
--    - DATETIME par TIMESTAMP
--    - BOOLEAN par BOOLEAN (déjà correct)
-- 3. Pour MySQL, remplacer :
--    - INTEGER PRIMARY KEY AUTOINCREMENT par INT AUTO_INCREMENT PRIMARY KEY
--    - DATETIME reste DATETIME
--    - BOOLEAN par TINYINT(1)
-- ============================================================================
