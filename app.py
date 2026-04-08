import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- CONFIGURACIÓN ---
# Asegúrate de usar mysql+pymysql para Alwaysdata
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://pomaraygst:dngr232..@mysql-pomaraygst.alwaysdata.net/pomaraygst_appdatabs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'pomaray_2026_gst' 

db = SQLAlchemy(app)

# --- MODELO DE DATOS ---
class Pasante(db.Model):
    __tablename__ = 'pasante'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    # Agrega aquí el resto de tus campos (correo, carrera, etc.)

# --- RUTAS DE NAVEGACIÓN ---

@app.route('/')
def index():
    # Flask busca index.html dentro de la carpeta /templates
    return render_template('index.html')

@app.route('/registro')
def registro():
    # Esta ruta permite que Flask detecte y cargue registro.html
    return render_template('registro.html')

@app.route('/login')
def login():
    # Esta ruta permite que Flask detecte y cargue login.html
    return render_template('login.html')

# --- RUTA PARA PROCESAR EL FORMULARIO (Ejemplo) ---
@app.route('/guardar_pasante', methods=['POST'])
def guardar_pasante():
    if request.method == 'POST':
        nombre = request.form['nombre']
        nuevo_pasante = Pasante(nombre=nombre)
        db.session.add(nuevo_pasante)
        db.session.commit()
        flash('Pasante registrado con éxito')
        return redirect(url_for('index'))

# --- INICIO ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)