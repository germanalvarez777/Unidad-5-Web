from datetime import datetime
import hashlib
from flask import Flask, request, render_template, url_for
from werkzeug.utils import redirect

app = Flask(__name__)
app.config.from_pyfile('config.py')

from models import db
from models import Usuario, Movil, Viaje


#-------------------------------------#
#       INICIO E INICIAR SESION       #
#-------------------------------------#

#http://localhost:8080/inicio
@app.route('/inicio')
def inicio():
    return render_template('index.html')

@app.route('/iniciar_sesion')
def iniciar_sesion():
    return render_template('iniciar_sesion.html', iniciarSesion=True)

@app.route('/autenticar_usuario', methods=['GET','POST'])
def autenticar_usuario():
    if request.method == 'POST':
        usuario_actual =  Usuario.query.filter_by(dni=request.form['usuario']).first()
        if usuario_actual is None:
            return render_template('iniciar_sesion.html', iniciarSesion=True, usuario = False)
        else:
            #verifico password
            clave = request.form['password']
            clave_cifrada = hashlib.md5(bytes(clave, encoding='utf-8'))
            if clave_cifrada.hexdigest() == usuario_actual.clave:
                #Envio como dato el usuario para saber que funcionalidades tiene y tipo
                if usuario_actual.tipo == 'cli':
                    return redirect(url_for('cliente',cliente_dni = usuario_actual.dni))
                elif usuario_actual.tipo == 'op':
                    return redirect(url_for('operador',operador_dni = usuario_actual.dni))
            else:
                return render_template('iniciar_sesion.html',iniciarSesion=True, password = False)


@app.route('/formulario_registrar_usuario')
def formulario_registrar_usuario():
    return render_template('iniciar_sesion.html',registrarUsuario=True)

@app.route('/registrar_usuario', methods=['GET','POST'])
def registrar_usuario():
    if request.method == 'POST':
        #chequear si el usuario ya esta registrado o no y mostrar el mensaje
        usuario =  Usuario.query.filter_by(dni=request.form['dni']).first()
        if usuario == None:
            #Cifro contraseña antes de crear el usuario:
            clave = request.form['password']
            clave_cifrada = hashlib.md5(bytes(clave, encoding='utf-8'))
            #Agrego el nuevo usuario por defecto de tipo cliente
            nuevo_usuario = Usuario(
                dni = request.form['dni'],
                nombre = request.form['nombre'],
                clave = clave_cifrada.hexdigest(),
                tipo = 'cli'
            )
            db.session.add(nuevo_usuario)
            db.session.commit()
            #Mostrar el mensaje en la planilla
            return render_template('iniciar_sesion.html', registrarUsuario=True, exito=True)
        else:
            return render_template('iniciar_sesion.html', registrarUsuario=True, usuarioRegistrado=True)


#-------------------------------------#
#       FUNCIONALIDADES CLIENTE       #
#-------------------------------------#

@app.route('/cliente/<int:cliente_dni>', methods=['GET','POST'])
@app.route('/cliente/<int:cliente_dni>/<int:estado>', methods=['GET','POST'])
def cliente(cliente_dni,estado = False):
    usuario_actual =  Usuario.query.filter_by(dni=cliente_dni).first()
    [viajes_usuario_actual, moviles_actual] = cargar_viajes_usuario(cliente_dni)    
    return render_template('funcionalidades_cliente.html', 
                            datos=usuario_actual, 
                            viajes = viajes_usuario_actual, 
                            moviles = moviles_actual, 
                            estado = estado)

#Solicita un viaje
@app.route('/solicitar_viaje/<int:cliente_dni>', methods=['GET','POST'])
def solicitar_viaje(cliente_dni):
    if request.method == 'POST':

        equipaje = request.form['equipaje']
        if equipaje == 'on':
                equipaje = 1
        else:
            equipaje = 0
        
        nuevo_viaje = Viaje(
            origen = request.form['dirOrigen'],
            destino = request.form['dirDestino'],
            fecha = datetime.today(),
            importe = 0.0,
            pasajeros = request.form['cantPasajeros'],
            equipaje = equipaje,
            dniCliente = cliente_dni 
        )
        print(request.form['equipaje'])
        db.session.add(nuevo_viaje)
        db.session.commit()
        #Envio estado verdadero para indicar que se muestre el modal de movil solicitado
        return redirect(url_for('cliente',cliente_dni=cliente_dni,estado = True))


#Carga viajes del usuario
def cargar_viajes_usuario(dni):
    #Leo viajes que aun no finalizan
    viajes = Viaje.query.filter_by(duracion=None).all()
    #Almaceno solo los del usuario
    viajes_pasajero = []
    for viaje in viajes:
        if str(viaje.dniCliente) == str(dni):
            viajes_pasajero.append(viaje)
    moviles = []
    for viaje in viajes_pasajero:
        movil = Movil.query.filter_by(numero = viaje.numMovil).first()
        if movil not in moviles:
            moviles.append(movil)   
    return [viajes_pasajero, moviles]


#-------------------------------------#
#      FUNCIONALIDADES OPERADOR       #
#-------------------------------------#

@app.route('/operador/<int:operador_dni>')
@app.route('/operador/<int:operador_dni>/<int:estado>/<int:volver>')
@app.route('/operador/<int:operador_dni>/<int:estado>/<int:volver>/<int:numero>/<fecha>')
def operador(operador_dni,estado = 0,volver= 1,numero = None, fecha = None):
    operador_actual =  Usuario.query.filter_by(dni=operador_dni).first()
    viajes_sin_movil = Viaje.query.filter_by(numMovil = None).all()
    viajes = Viaje.query.filter_by(duracion=None).all()
    viajes_sin_finalizar = []
    for viaje in viajes:
        if viaje.numMovil != None:
            viajes_sin_finalizar.append(viaje)
    moviles = Movil.query.all()
    
    viajes_ralizados_movil = []
    importe_total = 0

    #Lectura de los viajes realizados por un movil
    if volver == 3 and estado == 1:
        viajes = Viaje.query.filter_by(numMovil=numero).all()
        for viaje in viajes:
            #Convierto la fecha a string con el formato leido desde el formulario para comparar
            fechaViaje = viaje.fecha.strftime("%Y-%m-%d")
            if fechaViaje == fecha and viaje.duracion != None:
                viajes_ralizados_movil.append(viaje)
                importe_total += viaje.importe

    return render_template('funcionalidades_operador.html', 
                            datos=operador_actual, 
                            viajesSM = viajes_sin_movil,
                            viajesSF = viajes_sin_finalizar,
                            moviles = moviles,
                            estado = estado, #Que parte de viajes realizado renderizar
                            volver = volver, #Para mantenerse en la pestaña actual
                            fecha_movil = fecha,
                            numero_movil = numero,
                            importe_total = importe_total,
                            viajes_movil = viajes_ralizados_movil)


#Asignar movil a solicitud de viaje

@app.route('/asignar_movil/<int:operador_dni>/<int:id_viaje>', methods=['GET','POST'])
def asignar_movil(operador_dni,id_viaje):
    if request.method == 'POST':
        viaje = Viaje.query.filter_by(idViaje = id_viaje).first()
        viaje.numMovil = request.form['numMovil']
        viaje.demora = request.form['demora']
        db.session.commit()
        return redirect(url_for('operador',operador_dni = operador_dni))

#Finalizar viaje

@app.route('/finalizar_viaje/<int:operador_dni>/<int:id_viaje>', methods=['GET','POST'])
def finalizar_viaje(operador_dni,id_viaje):
    if request.method == 'POST':
        viaje = Viaje.query.filter_by(idViaje = id_viaje).first()
        duracion = request.form['duracion']
        importe_viaje = calcular_importe(duracion,viaje.demora)
        viaje.duracion = duracion
        viaje.importe = importe_viaje
        db.session.commit()
        return redirect(url_for('operador',operador_dni = operador_dni, estado = 0, volver = 2))


#Calcular el importe de un viaje realizado
def calcular_importe(duracion,demora):
    importe_base = 100.0
    importe_variable = 5 * int(duracion)
    importe_viaje = importe_base + importe_variable
    if demora > 15:
        importe_viaje -= 0.1 * importe_viaje
    return round(importe_viaje,2) 


#Consulta los viajes realizados por un movil

@app.route('/consultar_viajes/<int:operador_dni>', methods=['GET','POST'])
def consultar_viajes(operador_dni):
    if request.method == 'POST':
        numero = request.form['numMovil']
        fecha = request.form['fecha']
    return redirect(url_for('operador',operador_dni = operador_dni,estado = 1, volver = 3,numero = numero, fecha=fecha))

#Retorno a la vista de seleccion de movil y fecha

@app.route('/volver_viajes/<int:operador_dni>', methods=['GET','POST'])
def volver_viajes(operador_dni):
    #Estado en 0 renderiza el selector de fecha y numero de movil
    #Volver en 3 muestra la pantalla de viajes realizados
    return redirect(url_for('operador',operador_dni = operador_dni,estado = 0, volver = 3))



if __name__ == '__main__':
    db.create_all()
    #0.0.0.0
    app.run(host='localhost', port=8080, debug=True)