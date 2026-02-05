-- Schema base (en evolución)

CREATE TABLE IF NOT EXISTS asesores (
	id INT AUTO_INCREMENT PRIMARY KEY,
	username VARCHAR(100) NOT NULL UNIQUE,
	password_hash VARCHAR(255) NOT NULL,
	rol VARCHAR(50) NOT NULL DEFAULT 'asesor',
	nombres VARCHAR(120) NOT NULL DEFAULT '',
	apellidos VARCHAR(120) NOT NULL DEFAULT '',
	activo TINYINT(1) NOT NULL DEFAULT 1,
	requiere_cambio_password TINYINT(1) NOT NULL DEFAULT 0,
	ultimo_acceso DATETIME NULL,
	-- Campos extendidos
	primer_nombre VARCHAR(120) NULL,
	segundo_nombre VARCHAR(120) NULL,
	apellido_paterno VARCHAR(120) NULL,
	apellido_materno VARCHAR(120) NULL,
	curp VARCHAR(20) NULL,
	fecha_nacimiento DATE NULL,
	edad INT NULL,
	genero VARCHAR(20) NULL,
	estado_civil VARCHAR(30) NULL,
	telefono VARCHAR(20) NULL,
	correo VARCHAR(150) NULL,
	pais VARCHAR(80) NULL,
	estado VARCHAR(80) NULL,
	ciudad VARCHAR(80) NULL,
	zona VARCHAR(80) NULL,
	inmobiliaria VARCHAR(150) NULL,
	area VARCHAR(120) NULL,
	anos_experiencia INT NULL,
	comision_asignada DECIMAL(12,2) NULL,
	fecha_ingreso DATE NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS clientes (
	id INT AUTO_INCREMENT PRIMARY KEY,
	activo TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS propiedades (
	id INT AUTO_INCREMENT PRIMARY KEY,
	activo TINYINT(1) NOT NULL DEFAULT 1,
	precio DECIMAL(12,2) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
