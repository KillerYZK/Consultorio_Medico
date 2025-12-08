from flask import Blueprint, jsonify, request
from flask_mysqldb import MySQL
from flask_jwt_extended import jwt_required

# Crear un Blueprint
pacientes_bp = Blueprint('pacientes_bp', __name__)

# La conexión se pasa desde app.py
conexion = None  # Se inicializará desde app.py

@pacientes_bp.route("/pacientes", methods=["GET"])
@jwt_required()
def lista_pacientes():
    try:
        cursor = conexion.connection.cursor()
        sql = "SELECT * FROM pacientes"
        cursor.execute(sql)
        datos = cursor.fetchall()
        
        if not datos:
            return jsonify({
                'datos': [],
                'mensaje': "No hay pacientes registrados",
                'exito': False
            }), 404
        
        columnas = [desc[0] for desc in cursor.description]
        arr_pacientes = [dict(zip(columnas, fila)) for fila in datos]

        return jsonify({
            'datos': arr_pacientes,
            'mensaje': "Listado de Pacientes",
            'exito': True
        }), 200
    except Exception as ex:
        return jsonify({
            'mensaje': f"Error: {str(ex)}",
            'exito': False
        }), 500

@pacientes_bp.route("/pacientes/<nombre>", methods=["GET"])
@jwt_required()
def buscar_pacientes(nombre):
    try:
        cursor = conexion.connection.cursor()
        sql = "SELECT * FROM pacientes WHERE nombre LIKE %s"
        cursor.execute(sql, (f"%{nombre}%",))
        datos = cursor.fetchall()
       
        if not datos:
            return jsonify({
                'datos': [],
                'mensaje': f"No se encontraron pacientes con el nombre: {nombre}",
                'exito': False
            }), 404

        columnas = [desc[0] for desc in cursor.description]
        arr_pacientes = [dict(zip(columnas, fila)) for fila in datos]

        return jsonify({
            'datos': arr_pacientes,
            'mensaje': "Pacientes encontrados",
            'exito': True
        }), 200
        
    except Exception as ex:
        return jsonify({
            'mensaje': f"Error: {str(ex)}",
            'exito': False
        }), 500

@pacientes_bp.route("/pacientes", methods=["POST"])
@jwt_required()
def crear_paciente():
    try:
        datos = request.json
        
        campos_requeridos = ['nombre', 'apellido', 'fecha_nacimiento', 
                           'sexo', 'telefono', 'correo', 'direccion']
        for campo in campos_requeridos:
            if campo not in datos:
                return jsonify({
                    'mensaje': f"El campo {campo} es requerido",
                    'exito': False
                }), 400

        cursor = conexion.connection.cursor()
        sql = """INSERT INTO pacientes (nombre, apellido, fecha_nacimiento,
                             sexo, telefono, correo, direccion, 
                             historial_medico, fecha_registro)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())"""
        
        cursor.execute(sql, (
            datos['nombre'],
            datos['apellido'],
            datos['fecha_nacimiento'],
            datos['sexo'],
            datos['telefono'],
            datos['correo'],
            datos['direccion'],
            datos.get('historial_medico', '')
        ))
        
        conexion.connection.commit()
        cursor.execute("SELECT LAST_INSERT_ID()")
        id_paciente = cursor.fetchone()[0]

        return jsonify({
            'datos': {
                'id_paciente': id_paciente,
                'nombre': datos['nombre'],
                'apellido': datos['apellido']
            },
            'mensaje': "Paciente agregado exitosamente",
            'exito': True
        }), 201
    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error: {str(ex)}",
            'exito': False
        }), 500

@pacientes_bp.route("/pacientes/<int:id_paciente>", methods=["PUT"])
@jwt_required()
def actualizar_paciente(id_paciente):
    try:
        cursor = conexion.connection.cursor()
        
        cursor.execute("SELECT id_paciente FROM pacientes WHERE id_paciente = %s", (id_paciente,))
        if not cursor.fetchone():
            return jsonify({
                'mensaje': "Paciente no encontrado",
                'exito': False
            }), 404

        datos = request.json
        campos_permitidos = ['nombre', 'apellido', 'fecha_nacimiento',
                           'sexo', 'telefono', 'correo', 'direccion', 'historial_medico']
        
        updates = []
        valores = []
        for campo in campos_permitidos:
            if campo in datos:
                updates.append(f"{campo} = %s")
                valores.append(datos[campo])
        
        if not updates:
            return jsonify({
                'mensaje': "No hay campos para actualizar",
                'exito': False
            }), 400

        valores.append(id_paciente)
        sql = f"UPDATE pacientes SET {', '.join(updates)} WHERE id_paciente = %s"
        
        cursor.execute(sql, tuple(valores))
        conexion.connection.commit()

        return jsonify({
            'mensaje': "Paciente actualizado exitosamente",
            'exito': True
        }), 200
    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error: {str(ex)}",
            'exito': False
        }), 500

@pacientes_bp.route("/pacientes/<int:id_paciente>", methods=["DELETE"])
@jwt_required()
def eliminar_paciente(id_paciente):
    try:
        cursor = conexion.connection.cursor()
        
        # Llamar al stored procedure que borra en cascada
        cursor.callproc('sp_eliminar_paciente', (id_paciente,))
        resultado = cursor.fetchone()
        cursor.nextset()
        conexion.connection.commit()
        
        if resultado:
            mensaje, exito = resultado
            return jsonify({
                'mensaje': mensaje,
                'exito': exito
            }), 200 if exito else 500
        
    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error: {str(ex)}",
            'exito': False
        }), 500