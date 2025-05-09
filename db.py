# db.py
import psycopg2
import os
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()

# Variables de conexión
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'productos_db')
DB_USER = os.getenv('DB_USER', 'usuario')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'contraseña')

def get_db_connection():
    try:
        print(f"🔌 Conectando a la base de datos en {DB_HOST}:{DB_PORT}...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")
        return None

def init_db():
    conn = get_db_connection()
    
    if conn is None:
        print("❌ No se pudo establecer conexión a la base de datos.")
        return

    try:
        cur = conn.cursor()

        # Crear las tablas si no existen
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
        print("✔️ Tablas creadas o ya existentes.")
    except Exception as e:
        print(f"❌ Error al crear las tablas: {e}")
    finally:
        conn.close()

def guardar_en_db(productos):
    conn = get_db_connection()

    if conn is None:
        print("❌ No se pudo establecer conexión a la base de datos.")
        return

    try:
        cur = conn.cursor()

        for p in productos:
            try:
                # Insertar producto, ignorando duplicados por nombre y tienda
                cur.execute('''
                    INSERT INTO productos (nombre, tienda, enlace) 
                    VALUES (%s, %s, %s) 
                    ON CONFLICT (nombre, tienda) DO NOTHING
                ''', (p["nombre"], p["tienda"], p["enlace"]))

                # Obtener ID del producto recién insertado
                cur.execute('''
                    SELECT id FROM productos WHERE nombre = %s AND tienda = %s
                ''', (p["nombre"], p["tienda"]))
                producto_id = cur.fetchone()[0]

                # Insertar precio
                precio = float(
                    p['precio'].replace('RD$', '').replace('DOP', '').replace('$', '').replace(',', '').strip()
                )

                cur.execute('''
                    INSERT INTO precios (producto_id, precio) 
                    VALUES (%s, %s)
                ''', (producto_id, precio))

            except Exception as e:
                print(f"❌ Error guardando en DB: {e}")

        conn.commit()
        print("✔️ Productos guardados correctamente.")
    except Exception as e:
        print(f"❌ Error general al guardar en DB: {e}")
    finally:
        conn.close()
