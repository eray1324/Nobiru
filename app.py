from flask import Flask, render_template, request, redirect, url_for, jsonify, g
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_muy_segura'
DATABASE = 'comunidad.db'

# Rangos de Gamificación
RANGOS = ["Bronce", "Plata", "Oro", "Platino", "Diamante", "Rubí", "Esmeralda", "Zafiro", "Amatista", "Obsidiana"]

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Inicializar la Base de Datos con datos de prueba
def init_db():
    with app.app_context():
        db = get_db()
        # Tabla de usuarios
        db.execute('''CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT,
            puntos INTEGER DEFAULT 0,
            rango TEXT DEFAULT 'Bronce'
        )''')
        # Tabla de comunidad (Mensajes)
        db.execute('''CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            contenido TEXT,
            materia TEXT
        )''')
        # Tabla de favoritos
        db.execute('''CREATE TABLE IF NOT EXISTS favoritos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            tipo TEXT,
            item_id TEXT,
            titulo TEXT
        )''')
        
        # Insertar un usuario de prueba si no existe
        try:
            db.execute("INSERT INTO usuarios (username, email, puntos, rango) VALUES ('Estudiante1', 'correo@prueba.com', 40, 'Plata')")
        except sqlite3.IntegrityError:
            pass
            
        db.commit()

# Rutas de la Aplicación
@app.route('/')
def inicio():
    db = get_db()
    # Obtener el usuario de prueba para simular sesión simple
    usuario = db.execute("SELECT * FROM usuarios WHERE username = 'Estudiante1'").fetchone()
    mensajes = db.execute("SELECT * FROM mensajes ORDER BY id DESC").fetchall()
    favoritos = db.execute("SELECT * FROM favoritos WHERE usuario = 'Estudiante1'").fetchall()
    
    # Datos estáticos para Reels y Biblioteca
    reels = [
        {"id": "r1", "materia": "Matemáticas", "titulo": "Truco de Álgebra en 30s", "url": "https://www.w3schools.com/html/mov_bbb.mp4"},
        {"id": "r2", "materia": "Historia", "titulo": "Resumen de la Independencia", "url": "https://www.w3schools.com/html/movie.mp4"}
    ]
    
    materiales = [
        {"id": "m1", "titulo": "Guía Oficial de Admisión PDF", "desc": "Temario completo resuelto.", "link": "#"},
        {"id": "m2", "titulo": "Formulario de Física", "desc": "Todas las fórmulas necesarias.", "link": "#"}
    ]

    return render_template('index.html', usuario=usuario, mensajes=mensajes, reels=reels, materiales=materiales, favoritos=favoritos)

@app.route('/registro', methods=['POST'])
def registro():
    username = request.form.get('username')
    email = request.form.get('email')
    db = get_db()
    try:
        db.execute("INSERT INTO usuarios (username, email, puntos, rango) VALUES (?, ?, 0, 'Bronce')", (username, email))
        db.commit()
    except sqlite3.IntegrityError:
        pass # Si ya existe, solo continúa
    return redirect(url_for('inicio'))

@app.route('/comunidad', methods=['POST'])
def publicar():
    usuario = request.form.get('usuario', 'Anónimo')
    contenido = request.form.get('contenido')
    materia = request.form.get('materia', 'General')
    db = get_db()
    db.execute("INSERT INTO mensajes (usuario, contenido, materia) VALUES (?, ?, ?)", (usuario, contenido, materia))
    
    # Gamificación: Publicar da 10 puntos
    user_data = db.execute("SELECT * FROM usuarios WHERE username = ?", (usuario,)).fetchone()
    if user_data:
        nuevos_puntos = user_data['puntos'] + 10
        # Calcular nuevo rango
        idx = min(nuevos_puntos // 20, len(RANGOS) - 1)
        nuevo_rango = RANGOS[idx]
        db.execute("UPDATE usuarios SET puntos = ?, rango = ? WHERE username = ?", (nuevos_puntos, nuevo_rango, usuario))
        
    db.commit()
    return redirect(url_for('inicio'))

@app.route('/quiz', methods=['POST'])
def quiz():
    usuario = request.form.get('usuario', 'Estudiante1')
    puntos_ganados = int(request.form.get('puntos_quiz', 0))
    db = get_db()
    
    user_data = db.execute("SELECT * FROM usuarios WHERE username = ?", (usuario,)).fetchone()
    if user_data:
        puntos_actuales = user_data['puntos']
        # Si saca 0 puntos, penalizamos bajando 10 puntos (mínimo 0)
        if puntos_ganados == 0:
            nuevos_puntos = max(0, puntos_actuales - 10)
        else:
            nuevos_puntos = puntos_actuales + puntos_ganados
            
        idx = min(nuevos_puntos // 20, len(RANGOS) - 1)
        nuevo_rango = RANGOS[idx]
        db.execute("UPDATE usuarios SET puntos = ?, rango = ? WHERE username = ?", (nuevos_puntos, nuevo_rango, usuario))
        db.commit()
        
    return redirect(url_for('inicio'))

@app.route('/favorito', methods=['POST'])
def favorito():
    usuario = request.form.get('usuario', 'Estudiante1')
    tipo = request.form.get('tipo')
    item_id = request.form.get('item_id')
    titulo = request.form.get('titulo')
    
    db = get_db()
    # Verificar si ya existe en favoritos
    existe = db.execute("SELECT * FROM favoritos WHERE usuario = ? AND tipo = ? AND item_id = ?", (usuario, tipo, item_id)).fetchone()
    if not existe:
        db.execute("INSERT INTO favoritos (usuario, tipo, item_id, titulo) VALUES (?, ?, ?, ?)", (usuario, tipo, item_id, titulo))
        db.commit()
    return redirect(url_for('inicio'))

# Ruta para que el robot mantenga viva la app
@app.route('/ping')
def ping():
    return "¡Despierto!", 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
