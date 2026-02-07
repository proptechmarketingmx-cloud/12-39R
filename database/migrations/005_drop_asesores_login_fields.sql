-- Elimina campos de login en asesores (si existen)
ALTER TABLE asesores DROP COLUMN IF EXISTS username;
ALTER TABLE asesores DROP COLUMN IF EXISTS password_hash;
