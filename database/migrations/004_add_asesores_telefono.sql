-- Agrega columna telefono a asesores (si no existe)
ALTER TABLE asesores ADD COLUMN IF NOT EXISTS telefono VARCHAR(20) NULL;
