-- Création de la table device_locks pour le verrouillage des appareils

CREATE TABLE IF NOT EXISTS device_locks (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    username VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    locked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS device_locks_device_id_idx ON device_locks(device_id);
CREATE INDEX IF NOT EXISTS device_locks_user_id_idx ON device_locks(user_id);

-- Commentaires
COMMENT ON TABLE device_locks IS 'Verrouillage des appareils mobiles aux utilisateurs';
COMMENT ON COLUMN device_locks.device_id IS 'Empreinte unique de l''appareil';
COMMENT ON COLUMN device_locks.username IS 'Nom d''utilisateur propriétaire';
COMMENT ON COLUMN device_locks.email IS 'Email de l''utilisateur';
COMMENT ON COLUMN device_locks.locked_at IS 'Date de verrouillage initial';
COMMENT ON COLUMN device_locks.last_used IS 'Dernière utilisation';
