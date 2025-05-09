# db.py
import psycopg2
import os

# Variables de conexión
DB_HOST = os.getenv('DB_HOST', 'localhost')  # El host de Railway será un proxy, o 'localhost' si lo usas localmente
DB_PORT = os.getenv('DB_PORT', '5432')      # Puerto de conexión, el de Railway es '45740' o '5432' si es local
DB_NAME = os.getenv('DB_NAME', 'productos_db')
DB_USER = os.getenv('DB_USER', 'usuario')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'contraseña')

def get_db_connection():
    # Crear conexión a la base de datos
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,  # Usar el puerto de Railway o '5432' para conexión local
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

def init_db():
    conn = get_db_connection()
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
    conn.close()

def guardar_en_db(productos):
    conn = get_db_connection()
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
    conn.close()
