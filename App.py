from flask import Flask, render_template, request, redirect, session
import sqlite3
import re
app = Flask(__name__)
app.secret_key = 'clave_secreta_mobilehouse'
# Crear base de datos
def init_db():
    conn = sqlite3.connect('clientes.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS solicitudes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/enviar', methods=['POST'])
def enviar():
    import re

    nombre = request.form['nombre']
    direccion = request.form['direccion']
    
    # TELÉFONO CORRECTO
    codigo = request.form['codigo_pais']
    numero = request.form['telefono']
    telefono = codigo + numero

    correo = request.form['correo']
    equipo = request.form['equipo']
    problema = request.form['problema']

    # VALIDAR TELÉFONO
    if not re.match(r'^\+\d{1,3}\d{7,12}$', telefono):
        return "❌ Número inválido. Verifica el código país y número"

    # VALIDAR CORREO
    if correo and not re.match(r'^[^@]+@[^@]+\.[^@]+$', correo):
        return "❌ Correo inválido"

    # GUARDAR EN BASE DE DATOS (ESTO ES LO IMPORTANTE)
    conn = sqlite3.connect('clientes.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO solicitudes (nombre, direccion, telefono, correo, equipo, problema)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (nombre, direccion, telefono, correo, equipo, problema))

    # OBTENER ID
    id_generado = cursor.lastrowid

    conn.commit()
    conn.close()

    return render_template('confirmacion.html', id=id_generado)

@app.route('/admin', methods=['GET', 'POST'])
def admin():

    if not session.get('login'):
        return redirect('/login')

    conn = sqlite3.connect('clientes.db')
    cursor = conn.cursor()

    datos = []

    if request.method == 'POST':
        busqueda = request.form.get('busqueda')
        estado = request.form.get('estado')

        if busqueda:
            cursor.execute("""
            SELECT * FROM solicitudes 
            WHERE nombre LIKE ? OR telefono LIKE ?
            """, (f"%{busqueda}%", f"%{busqueda}%"))

        elif estado:
            cursor.execute("""
            SELECT * FROM solicitudes 
            WHERE estado=?
            """, (estado,))

        else:
            cursor.execute("SELECT * FROM solicitudes")

        datos = cursor.fetchall()

    else:
        cursor.execute("SELECT * FROM solicitudes")
        datos = cursor.fetchall()

    conn.close()

    return render_template('admin.html', datos=datos)

@app.route('/cambiar_estado/<int:id>', methods=['POST'])
def cambiar_estado(id):
    estado = request.form['estado']

    conn = sqlite3.connect('clientes.db')
    cursor = conn.cursor()

    cursor.execute("UPDATE solicitudes SET estado=? WHERE id=?", (estado, id))

    conn.commit()
    conn.close()

    return redirect('/admin')

@app.route('/consulta', methods=['GET', 'POST'])
def consulta():
    resultados = None

    if request.method == 'POST':
        telefono = request.form.get('telefono')

        if telefono:
            conn = sqlite3.connect('clientes.db')
            cursor = conn.cursor()

            cursor.execute("""
            SELECT * FROM solicitudes 
            WHERE telefono LIKE ?
            """, (f"%{telefono}%",))

            resultados = cursor.fetchall()

            conn.close()

    return render_template('consulta.html', resultados=resultados)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']

        if usuario == 'admin' and clave == '1234':
            session['login'] = True
            return redirect('/admin')
        else:
            return "Credenciales incorrectas"

    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)
