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
        
        columnas = [desc[0] for desc in cursor.description]
        arr_pacientes = [dict(zip(columnas, fila)) for fila in datos]

        return jsonify({
            'datos': arr_pacientes,
            'mensaje': "Listado de Pacientes",
            'exito': True
        }), 200
    except Exception as ex:
        return jsonify({
            'mensaje': f"Error al obtener pacientes: {str(ex)}",
            'exito': False
        }), 500

@pacientes_bp.route("/pacientes/<nombre>", methods=["GET"])
@jwt_required()
def buscar_pacientes(nombre):
    try:
        cursor = conexion.connection.cursor()
        # Usar parámetros para prevenir SQL Injection
        sql = "SELECT * FROM pacientes WHERE nombre = %s"
        cursor.execute(sql, (nombre,))
        datos = cursor.fetchone()
       
        if datos:
            # Usar zip para crear el diccionario automáticamente
            columnas = [desc[0] for desc in cursor.description]
            paciente = dict(zip(columnas, datos))

            return jsonify({
                'datos': paciente,
                'mensaje': "Paciente encontrado",
                'exito': True
            }), 200
        
        return jsonify({
            'mensaje': 'Paciente no encontrado',
            'exito': False
        }), 404
        
    except Exception as ex:
        return jsonify({
            'mensaje': f"Error al buscar paciente: {str(ex)}",
            'exito': False
        }), 500

@pacientes_bp.route("/pacientes", methods=["POST"])
@jwt_required()
def agregar_paciente():
    try:
        campos_requeridos = ['nombre', 'apellido', 'fecha_nacimiento',
                           'sexo', 'telefono', 'correo',
                           'direccion', 'historial_medico', 'fecha_registro']
        
        for campo in campos_requeridos:
            if campo not in request.json:
                return jsonify({
                    'mensaje': f"El campo {campo} es requerido",
                    'exito': False
                }), 400

        cursor = conexion.connection.cursor()
        # Quitar comillas de los nombres de columnas
        sql = """INSERT INTO pacientes (nombre, apellido, fecha_nacimiento,
                             sexo, telefono, correo,
                             direccion, historial_medico, fecha_registro)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        datos = tuple(request.json[campo] for campo in campos_requeridos)
        cursor.execute(sql, datos)
        conexion.connection.commit()

        return jsonify({
            'mensaje': "Paciente agregado exitosamente",
            'exito': True
        }), 201
    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error al agregar paciente: {str(ex)}",
            'exito': False
        }), 500

@pacientes_bp.route("/pacientes/<int:id_paciente>", methods=["DELETE"])
@jwt_required()
def eliminar_paciente(id_paciente):
    try:
        cursor = conexion.connection.cursor()
        
        # Verificar si el paciente existe
        sql_verify = "SELECT id_paciente FROM pacientes WHERE id_paciente = %s"
        cursor.execute(sql_verify, (id_paciente,))
        
        if not cursor.fetchone():
            return jsonify({
                'mensaje': f"No existe un paciente con el ID {id_paciente}",
                'exito': False
            }), 404

        sql = "DELETE FROM pacientes WHERE id_paciente = %s"
        cursor.execute(sql, (id_paciente,))
        conexion.connection.commit()
        
        return jsonify({
            'mensaje': f"Paciente con ID {id_paciente} eliminado exitosamente",
            'exito': True
        }), 200
    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error al eliminar paciente: {str(ex)}",
            'exito': False
        }), 500

@pacientes_bp.route("/pacientes/<int:id_paciente>", methods=["PUT"])
@jwt_required()
def actualizar_paciente(id_paciente):
    try:
        campos_permitidos = ['nombre', 'apellido', 'fecha_nacimiento',
                           'sexo', 'telefono', 'correo',
                           'direccion', 'historial_medico']
        
        # Construir la parte SET de la consulta SQL dinámicamente
        set_clauses = []
        valores = []
        for campo in campos_permitidos:
            if campo in request.json:
                set_clauses.append(f"{campo} = %s")
                valores.append(request.json[campo])
        
        if not set_clauses:
            return jsonify({
                'mensaje': "No se proporcionaron campos para actualizar",
                'exito': False
            }), 400

        sql_set = ", ".join(set_clauses)
        sql = f"UPDATE pacientes SET {sql_set} WHERE id_paciente = %s"
        valores.append(id_paciente)

        cursor = conexion.connection.cursor()
        cursor.execute(sql, tuple(valores))
        conexion.connection.commit()

        if cursor.rowcount == 0:
            return jsonify({
                'mensaje': f"No existe un paciente con el ID {id_paciente}",
                'exito': False
            }), 404

        return jsonify({
            'mensaje': f"Paciente actualizado exitosamente",
            'exito': True
        }), 200
    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error al actualizar paciente: {str(ex)}",
            'exito': False
        }), 500