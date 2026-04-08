import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError

app = Flask(__name__)

# --- CONFIGURACIÓN OPTIMIZADA ---
# 1. Driver pymysql para evitar errores de compilación en Alwaysdata
# 2. pool_pre_ping=True evita el error "MySQL server has gone away" tras inactividad
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://pomaraygst:dngr232..@mysql-pomaraygst.alwaysdata.net/pomaraygst_appdatabs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True}
app.config['SECRET_KEY'] = 'pomaray_2026_gst' 

db = SQLAlchemy(app)

# --- MODELO DE DATOS ---
class Pasante(db.Model):
    __tablename__ = 'pasante'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    carrera = db.Column(db.String(100), nullable=False)
    institucion = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)

# --- RUTAS ---

@app.route('/')
def index():
    try:
        pasantes = Pasante.query.all()
        return render_template('index.html', pasantes=pasantes)
    except OperationalError:
        flash("Error de conexión con la base de datos.")
        return render_template('index.html', pasantes=[])

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/guardar', methods=['POST'])
def guardar():
    if request.method == 'POST':
        try:
            nuevo_pasante = Pasante(
                nombre=request.form['nombre'],
                apellido=request.form['apellido'],
                carrera=request.form['carrera'],
                institucion=request.form['institucion'],
                telefono=request.form['telefono']
            )
            db.session.add(nuevo_pasante)
            db.session.commit()
            flash('¡Pasante registrado exitosamente!')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {str(e)}')
        
        return redirect(url_for('index'))

# --- MANEJO DE ERRORES HTTP ---
@app.errorhandler(404)
def page_not_found(e):
    return "Página no encontrada. Revisa que el archivo HTML esté en la carpeta /templates", 404

# --- INICIO DINÁMICO ---
if __name__ == '__main__':
    # Usa el puerto de Alwaysdata o el 5000 por defecto en tu Arch Linux
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)