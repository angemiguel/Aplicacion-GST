import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)

# --- CONFIGURACIÓN PARA ALWAYSDATA ---
# Usamos mysql+pymysql para asegurar compatibilidad en el servidor
# Asegúrate de que la contraseña dngr232.. sea la correcta en tu panel MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://pomaraygst:dngr232.@mysql-pomaraygst.alwaysdata.net/pomaraygst_appdatabs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pomaray_2026_gst') 

db = SQLAlchemy(app)

# --- MODELOS ---
# Asegúrate de que los nombres de las columnas coincidan con tu SQL
class Pasante(db.Model):
    __tablename__ = 'pasante'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    # Agrega aquí el resto de tus campos según tu tabla SQL
    # Ejemplo: carrera = db.Column(db.String(100))

# --- RUTAS ---
@app.route('/')
def index():
    return render_template('index.html')

# Agrega aquí tus otras rutas (registro, login, etc.)

# --- INICIO DE LA APLICACIÓN ---
if __name__ == '__main__':
    # Esto permite que la app use el puerto que Alwaysdata le asigne dinámicamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)