from flask import Flask, request, redirect, render_template, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'clave_secreta'

# Función para conectar a la base de datos
def get_db_connection():
    conn = sqlite3.connect('bd_instituto.db')
    conn.row_factory = sqlite3.Row
    # Habilitar el soporte de Claves Foráneas en SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# Función para inicializar las tablas de la base de datos
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Crear tabla cursos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            horas INTEGER NOT NULL
        )
    ''')

    # Crear tabla estudiantes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            fecha_nacimiento TEXT
        )
    ''')

    # Crear tabla inscripciones (con claves foráneas FK)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inscripciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            curso_id INTEGER NOT NULL,
            estudiante_id INTEGER NOT NULL,
            FOREIGN KEY (curso_id) REFERENCES cursos (id) ON DELETE CASCADE,
            FOREIGN KEY (estudiante_id) REFERENCES estudiantes (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

# Función para insertar datos de prueba iniciales
def seed_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verificar si ya existen cursos registrados
    cursor.execute('SELECT COUNT(*) FROM cursos')
    if cursor.fetchone()[0] == 0:
        # Insertar Cursos
        cursor.executemany('''
            INSERT INTO cursos (descripcion, horas) VALUES (?, ?)
        ''', [
            ('Programación en Python y Flask', 40),
            ('Bases de Datos con SQL', 30),
            ('Desarrollo Web Frontend (HTML/CSS)', 35)
        ])

        # Insertar Estudiantes
        cursor.executemany('''
            INSERT INTO estudiantes (nombre, apellidos, fecha_nacimiento) VALUES (?, ?, ?)
        ''', [
            ('Carlos', 'Mendoza Quispe', '2001-05-14'),
            ('Maria', 'Flores Choque', '2002-11-20'),
            ('Javier', 'Mamani Aliaga', '2000-03-08')
        ])

        # Insertar Inscripciones (referenciando los IDs creados arriba)
        cursor.executemany('''
            INSERT INTO inscripciones (fecha, curso_id, estudiante_id) VALUES (?, ?, ?)
        ''', [
            ('2026-03-01', 1, 1), # Carlos se inscribe a Python
            ('2026-03-02', 2, 1), # Carlos se inscribe a SQL
            ('2026-03-01', 1, 2), # Maria se inscribe a Python
            ('2026-03-05', 3, 3)  # Javier se inscribe a Frontend
        ])

        conn.commit()
        print("Datos de prueba insertados con éxito.")

    conn.close()

# Inicializar las tablas e insertar los datos de prueba
init_db()
seed_db()

@app.route('/')
def index():
    return redirect(url_for('estudiantes'))

@app.route('/estudiantes')
def estudiantes():
    conn = get_db_connection()
    estudiantes = conn.execute('SELECT * FROM estudiantes').fetchall()
    conn.close()
    return render_template('estudiantes.html', estudiantes=estudiantes)


@app.route('/cursos')
def cursos():
    conn = get_db_connection()
    cursos = conn.execute('SELECT * FROM cursos').fetchall()
    conn.close()
    return render_template('cursos.html', cursos=cursos)

@app.route("/curso/nuevos", methods=["GET", "POST"])
def nuevo_curso():
    if request.method == "POST":
        # leer contenido del formulario
        descripcion = request.form["descripcion"]
        horas = request.form["horas"]
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO cursos (descripcion, horas) VALUES (?, ?)",
            (descripcion, horas),
        )
        conn.commit()
        conn.close()
        flash("Curso agregado exitosamente.", "success")
        return redirect(url_for("cursos"))
    return render_template("form_curso.html")

@app.route('/curso/editar/<int:id>', methods=['GET', 'POST'])
def editar_curso(id):
    conn = get_db_connection()
    curso = conn.execute('SELECT * FROM cursos WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
         descripcion = request.form['descripcion']
         horas = request.form['horas']
         conn.execute('UPDATE cursos SET descripcion = ?, horas = ? WHERE id = ?', (descripcion, horas, id))
         conn.commit()
         conn.close()
         flash("Curso actualizado exitosamente.", "success")
         return redirect(url_for('cursos'))
    return render_template('form_curso.html', curso=curso)

@app.route('/curso/eliminar/<int:id>')
def eliminar_curso(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM cursos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash("Curso eliminado exitosamente.", "success")
    return redirect(url_for('cursos'))



@app.route('/inscripciones')
def inscripciones():
    conn = get_db_connection()
    inscripciones = conn.execute(
        """
        select i.id,
            i.fecha,
            e.nombre || ' ' || e.apellidos as estudiante,
            c.descripcion as curso
        from inscripciones i
        join estudiantes e on i.estudiante_id = e.id
        join cursos c ON i.curso_id = c.id

        """
        ).fetchall()
    conn.close()
    return render_template('inscripciones.html', inscripciones=inscripciones)


@app.route("/inscripcion/nuevo", methods=["GET", "POST"])
def nueva_inscripcion():
    conn = get_db_connection()
    #en caso de que sea post, consolidar la inscripcion 
    if request.method == "POST":
        fecha = request.form["fecha"]
        estudiante_id = request.form["estudiante_id"]
        curso_id = request.form["curso_id"]
        
        conn.execute(
            """
            INSERT INTO inscripciones
            (fecha, curso_id, estudiante_id) 
            VALUES (?, ?, ?)
            """,(fecha, curso_id, estudiante_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("inscripciones"))
    
    #en caso de get enviar datos para mostrar el formulario de inscripcion
    
    estudiantes = conn.execute(
        
        """
        SELECT id, concat(nombre, ' ', apellidos) as nombre
        from estudiantes
        """
        
     ).fetchall()
    cursos = conn.execute(
        """
        SELECT id, descripcion from cursos
        """
     ).fetchall()
    conn.close()
    return render_template ("form_inscripcion.html", estudiantes=estudiantes, cursos=cursos)


@app.route('/inscripcion/eliminar/<int:id>')
def eliminar_inscripcion(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM inscripciones WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Inscripción eliminada exitosamente.", "success")
    return redirect(url_for("inscripciones"))

if __name__ == '__main__':
    app.run(debug=True)