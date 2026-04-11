from flask import Flask, render_template, request, redirect, session
import psycopg2
import re
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_mobilehouse'

# 🔐 CONEXIÓN SEGURA (Render)
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# 🧱 CREAR TABLA
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS solicitudes (
        id SERIAL PRIMARY KEY,
        nombre TEXT,
        direccion TEXT,
        telefono TEXT,
        correo TEXT,
        equipo TEXT,
        problema TEXT,
        estado TEXT DEFAULT 'Recibido'
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# 🏠 INICIO
@app.route('/')
def index():
    return render_template('index.html')

# 📩 ENVIAR SOLICITUD
@app.route('/enviar', methods=['POST'])
def enviar():
    nombre = request.form['nombre']
    direccion = request.form['direccion']

    codigo = request.form['codigo_pais']
    numero = request.form['telefono']
    telefono = codigo + numero

    correo = request.form['correo']
    equipo = request.form['equipo']
    problema = request.form['problema']

    # VALIDACIONES
    if not re.match(r'^\+\d{1,3}\d{7,12}$', telefono):
        return "❌ Número inválido. Verifica el código país"

    if correo and not re.match(r'^[^@]+@[^@]+\.[^@]+$', correo):
        return "❌ Correo inválido"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO solicitudes (nombre, direccion, telefono, correo, equipo, problema)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id
    ''', (nombre, direccion, telefono, correo, equipo, problema))

    id_generado = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return render_template('confirmacion.html', id=id_generado)

# 🔐 LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']

        if usuario == 'admin' and clave == 'L0c4l':
            session['login'] = True
            return redirect('/admin')
        else:
            return "Credenciales incorrectas"

    return render_template('login.html')

# 📊 PANEL ADMIN
@app.route('/admin', methods=['GET', 'POST'])
def admin():

    if not session.get('login'):
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        busqueda = request.form.get('busqueda')
        estado = request.form.get('estado')

        if busqueda:
            cursor.execute("""
            SELECT * FROM solicitudes
            WHERE nombre ILIKE %s OR telefono ILIKE %s
            """, (f"%{busqueda}%", f"%{busqueda}%"))

        elif estado:
            cursor.execute("""
            SELECT * FROM solicitudes
            WHERE estado=%s
            """, (estado,))

        else:
            cursor.execute("SELECT * FROM solicitudes")

    else:
        cursor.execute("SELECT * FROM solicitudes")

    datos = cursor.fetchall()
    conn.close()

    return render_template('admin.html', datos=datos)

# 🔄 CAMBIAR ESTADO
@app.route('/cambiar_estado/<int:id>', methods=['POST'])
def cambiar_estado(id):
    estado = request.form['estado']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE solicitudes SET estado=%s WHERE id=%s", (estado, id))

    conn.commit()
    conn.close()

    return redirect('/admin')

# 🔍 CONSULTA CLIENTE
@app.route('/consulta', methods=['GET', 'POST'])
def consulta():
    resultados = None

    if request.method == 'POST':
        telefono = request.form['telefono']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM solicitudes WHERE telefono=%s", (telefono,))
        resultados = cursor.fetchall()

        conn.close()

    return render_template('consulta.html', resultados=resultados)

# 🚀 INICIO APP
if __name__ == '__main__':
    app.run(debug=True)