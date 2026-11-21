"""
Script de inicialización de la base de datos para el proyecto
Caja Registradora Inteligente.

Crea el archivo database.db (o la ruta indicada por la variable de
entorno DATABASE_PATH) con las tablas productos, ventas y
detalle_venta, y agrega algunos productos de ejemplo si la tabla
productos está vacía.

Uso:
    python init_db.py
"""
import os
import sqlite3

DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "database.db"),
)

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    precio REAL NOT NULL CHECK (precio > 0),
    stock INTEGER NOT NULL CHECK (stock >= 0)
);

CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    total REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS detalle_venta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    subtotal REAL NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);
"""

PRODUCTOS_EJEMPLO = [
    ("Coca-Cola", 3500, 50),
    ("Papas", 2500, 30),
    ("Agua", 2000, 40),
]


def init_db(seed=True):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)

        if seed:
            existentes = conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
            if existentes == 0:
                conn.executemany(
                    "INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
                    PRODUCTOS_EJEMPLO,
                )

        conn.commit()
    finally:
        conn.close()

    print(f"Base de datos inicializada en: {DB_PATH}")


if __name__ == "__main__":
    init_db()
