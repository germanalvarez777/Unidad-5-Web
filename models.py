from __main__ import app
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)

class Usuario(db.Model):
    dni = db.Column(db.String(8), primary_key = True)
    nombre = db.Column(db.String(80), nullable=False)
    clave = db.Column(db.String(30), nullable=False)
    tipo = db.Column(db.String(3), nullable=False)
    #Como pongo los viajes realizados
    viaje = db.relationship('Viaje',backref='usuario',cascade="all, delete-orphan",lazy='dynamic')

class Movil(db.Model):
    numero = db.Column(db.Integer,primary_key=True)
    patente = db.Column(db.String(7), unique=True, nullable=False)
    marca = db.Column(db.String(30), nullable=False)
    #Como pongo la lista de viajes realizados
    viaje = db.relationship('Viaje',backref='movil',cascade="all, delete-orphan",lazy='dynamic')

class Viaje(db.Model):
    idViaje = db.Column(db.Integer,primary_key=True)
    origen = db.Column(db.String(80), nullable=False)
    destino = db.Column(db.String(80), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    demora = db.Column(db.Integer,nullable=True)
    duracion = db.Column(db.Integer,nullable=True)
    importe = db.Column(db.Float,nullable=True)
    pasajeros = db.Column(db.Integer,nullable = False)
    equipaje = db.Column(db.Integer,nullable = True) #Porque el db browser lo modela como entero 0/1
    dniCliente = db.Column(db.String(8),db.ForeignKey('usuario.dni'))
    numMovil = db.Column(db.Integer,db.ForeignKey('movil.numero'), nullable = False)
