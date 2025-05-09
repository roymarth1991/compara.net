# db.py
import psycopg2
import os
from psycopg2 import sql

# Configuración de la base de datos
DB_HOST = os.getenv("DB_HOST", "localhost")  # Usualmente, en producción en Railway será una variable de entorno
DB_NAME = os.getenv("DB_NAME", "productos_db")
DB_USER = os.getenv("DB_USER", "usuario")  # Tu usuario de PostgreSQL
DB_PASSWORD = os.getenv("DB_PASSWORD", "contraseña")  # Tu contraseña de PostgreSQL

def get_connection():
    """Conectar a la base de datos PostgreSQL"""
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS productos (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        tienda TEXT NOT NULL,
        enlace TEXT,
        UNIQUE(nombre, tienda)
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS precios (
        id SERIAL PRIMARY KEY,
        producto_id INTEGER,
        precio REAL,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(producto_id) REFERENCES productos(id)
    )
    ''')

    conn.commit()
    conn.close()

def guardar_en_db(productos):
    conn = get_connection()
    cur = conn.cursor()

    for p in productos:
        try:
            # Insertar un nuevo producto (ignorar duplicados)
            cur.execute('''
            INSERT INTO productos (nombre, tienda, enlace) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (nombre, tienda) DO NOTHING
            ''', (p["nombre"], p["tienda"], p["enlace"]))

            # Obtener el ID del producto insertado
            cur.execute('''
            SELECT id FROM productos WHERE nombre = %s AND tienda = %s
            ''', (p["nombre"], p["tienda"]))
            producto_id = cur.fetchone()[0]

            # Convertir precio a tipo float
            precio = float(p['precio'].replace('RD$', '').replace('DOP', '').replace('$', '').replace(',', '').strip())

            # Insertar el precio del producto
            cur.execute('''
            INSERT INTO precios (producto_id, precio) VALUES (%s, %s)
            ''', (producto_id, precio))

        except Exception as e:
            print(f"❌ Error guardando en DB: {e}")

    conn.commit()
    conn.close()
