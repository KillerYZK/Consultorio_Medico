from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL
from flask_jwt_extended import jwt_required

doctores_bp = Blueprint('doctores_bp', __name__)
conexion = None

@doctores_bp.route("/doctores", methods=["GET"])
@jwt_required()
def lista_doctores():
    try:
        cursor = conexion.connection.cursor()
        sql = """SELECT d.*, e.nombre as especialidad FROM doctores d 
                INNER JOIN especialidades e ON d.id_especialidad = e.id_especialidad"""
        cursor.execute(sql)
        datos = cursor.fetchall()
       
        columnas = [desc[0] for desc in cursor.description]
        arr_doctores = [dict(zip(columnas, fila)) for fila in datos]

        return jsonify({
            'datos': arr_doctores,
            'mensaje': "Listado de Doctores",
            'exito': True
        }), 200
    except Exception as ex:
        return jsonify({
            'mensaje': f"Error al obtener doctores: {str(ex)}",
            'exito': False
        }), 500

@doctores_bp.route("/doctores/<nombre>", methods=["GET"])
@jwt_required
def buscar_doctores(nombre):
    try:
        cursor = conexion.connection.cursor()
        sql = """SELECT d.*, e.nombre as especialidad FROM doctores d 
                INNER JOIN especialidades e ON d.id_especialidad = e.id_especialidad 
                WHERE d.nombre = %s"""
        cursor.execute(sql, (nombre,))
        datos = cursor.fetchone()
       
        if datos:
            columnas = [desc[0] for desc in cursor.description]
            doctor = dict(zip(columnas, datos))

            return jsonify({
                'datos': doctor,
                'mensaje': "Doctor encontrado",
                'exito': True
            }), 200
        
        return jsonify({
            'mensaje': "Doctor no encontrado",
            'exito': False
        }), 404
    except Exception as ex:
        return jsonify({
            'mensaje': f"Error al buscar doctor: {str(ex)}",
            'exito': False
        }), 500
        + ['apellido', 'cedula_profesional', 
        'telefono', 'correo', 'id_especialidad']
        
        # Validar que todos los campos requeridos estén presentes
        for campo in campos_requeridos:
            if campo not in request.json:
                return jsonify({
                    'mensaje': f"El campo {campo} es requerido",
                    'exito': False
                }), 400

        cursor = conexion.connection.cursor()
        sql = """INSERT INTO doctores (nombre, apellido, cedula_profesional, 
                                     telefono, correo, id_especialidad)
                 VALUES (%s, %s, %s, %s, %s, %s)"""
        
        datos = tuple(request.json[campo] for campo in campos_requeridos)
        cursor.execute(sql, datos)
        conexion.connection.commit()

        return jsonify({
            'mensaje': "Doctor agregado exitosamente",
            'exito': True
        }), 201
    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error al agregar doctor: {str(ex)}",
            'exito': False
        }), 500

@doctores_bp.route("/doctores/<int:id_doctor>", methods=["DELETE"])
@jwt_required()
def eliminar_doctor(id_doctor):
    try:
        cursor = conexion.connection.cursor()
        
        # Primero verificamos si el doctor existe
        sql_verify = "SELECT id_doctor FROM doctores WHERE id_doctor = %s"
        cursor.execute(sql_verify, (id_doctor,))
        
        if not cursor.fetchone():
            return jsonify({
                'mensaje': f"No existe un doctor con el ID {id_doctor}",
                'exito': False
            }), 404

        sql = "DELETE FROM doctores WHERE id_doctor = %s"
        cursor.execute(sql, (id_doctor,))
        conexion.connection.commit()
        
        return jsonify({
            'mensaje': f"Doctor con ID {id_doctor} eliminado exitosamente",
            'exito': True
        }), 200
    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error al eliminar doctor: {str(ex)}",
            'exito': False
        }), 500
    
@doctores_bp.route("/doctores/<int:id_doctor>", methods=["PUT"])
@jwt_required()
def actualizar_doctor(id_doctor):
    try:
        # Primero verificar si el doctor existe
        cursor = conexion.connection.cursor()
        sql_verify = "SELECT id_doctor FROM doctores WHERE id_doctor = %s"
        cursor.execute(sql_verify, (id_doctor,))
        
        if not cursor.fetchone():
            return jsonify({
                'mensaje': f"No existe un doctor con el ID {id_doctor}",
                'exito': False
            }), 404

        # Verificar que el body sea JSON
        if not request.is_json:
            return jsonify({
                'mensaje': "El contenido debe ser JSON",
                'exito': False
            }), 400

        campos_permitidos = ['nombre', 'apellido', 'cedula_profesional', 
                           'telefono', 'correo', 'id_especialidad']
        
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
        sql = f"UPDATE doctores SET {sql_set} WHERE id_doctor = %s"
        valores.append(id_doctor)

        cursor.execute(sql, tuple(valores))
        conexion.connection.commit()

        if cursor.rowcount == 0:
            return jsonify({
                'mensaje': f"No existe un doctor con el ID {id_doctor}",
                'exito': False
            }), 404

        return jsonify({
            'mensaje': f"Doctor con ID {id_doctor} actualizado exitosamente",
            'exito': True
        }), 200
    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error al actualizar doctor: {str(ex)}",
            'exito': False
        }), 500
    