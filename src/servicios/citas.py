from flask import Blueprint, request, jsonify
from flask_mysqldb import MySQL
from datetime import datetime, date, time, timedelta
from flask_jwt_extended import jwt_required

citas_bp = Blueprint('citas_bp', __name__)
conexion = None

# Función auxiliar para serializar tipos datetime
def serializar_citas(datos):
    columnas = [desc[0] for desc in conexion.connection.cursor().description] if datos else []
    arr_citas = []
    for fila in datos:
        fila_dict = {}
        for col, val in zip(columnas, fila):
            if isinstance(val, (datetime, date, time, timedelta)):
                fila_dict[col] = str(val)
            else:
                fila_dict[col] = val
        arr_citas.append(fila_dict)
    return arr_citas

@citas_bp.route("/citas", methods=["GET"])
@jwt_required()
def lista_citas():
    try:
        cursor = conexion.connection.cursor()
        # Llamar al stored procedure
        cursor.callproc('sp_obtener_todas_citas')
        datos = cursor.fetchall()
        
        if not datos:
            return jsonify({
                'datos': [],
                'mensaje': "No hay citas registradas",
                'exito': False
            }), 404

        # Obtener nombres de columnas ANTES de nextset()
        columnas = [desc[0] for desc in cursor.description]
        cursor.nextset()
        
        arr_citas = []
        for fila in datos:
            fila_dict = {}
            for col, val in zip(columnas, fila):
                if isinstance(val, (datetime, date, time, timedelta)):
                    fila_dict[col] = str(val)
                else:
                    fila_dict[col] = val
            arr_citas.append(fila_dict)

        return jsonify({
            'datos': arr_citas,
            'mensaje': "Listado de Citas",
            'exito': True
        }), 200
    except Exception as ex:
        return jsonify({
            'mensaje': f"Error al obtener citas: {str(ex)}",
            'exito': False
        }), 500
    
@citas_bp.route("/citas/<int:id_cita>", methods=["GET"])
@jwt_required()
def obtener_cita(id_cita):
    try:
        cursor = conexion.connection.cursor()
        cursor.callproc('sp_obtener_cita_por_id', (id_cita,))
        fila = cursor.fetchone()
        
        if fila is None:
            cursor.nextset()
            return jsonify({
                'mensaje': "Cita no encontrada",
                'exito': False
            }), 404

        columnas = [desc[0] for desc in cursor.description]
        cursor.nextset()
        
        cita_dict = {}
        for col, val in zip(columnas, fila):
            if isinstance(val, (datetime, date, time, timedelta)):
                cita_dict[col] = str(val)
            else:
                cita_dict[col] = val

        return jsonify({
            'datos': cita_dict,
            'mensaje': "Cita obtenida exitosamente",
            'exito': True
        }), 200
    except Exception as ex:
        return jsonify({
            'mensaje': f"Error al obtener cita: {str(ex)}",
            'exito': False
        }), 500

# Buscar citas por nombre del doctor
@citas_bp.route("/citas/doctor/<nombre_doctor>", methods=["GET"])
@jwt_required()
def buscar_citas_doctor(nombre_doctor):
    try:
        cursor = conexion.connection.cursor()
        cursor.callproc('sp_buscar_citas_doctor', (nombre_doctor,))
        datos = cursor.fetchall()
        
        if not datos:
            cursor.nextset()
            return jsonify({
                'datos': [],
                'mensaje': f"El doctor '{nombre_doctor}' no tiene citas registradas",
                'exito': False
            }), 404

        columnas = [desc[0] for desc in cursor.description]
        cursor.nextset()
        
        arr_citas = []
        for fila in datos:
            fila_dict = {}
            for col, val in zip(columnas, fila):
                if isinstance(val, (datetime, date, time, timedelta)):
                    fila_dict[col] = str(val)
                else:
                    fila_dict[col] = val
            arr_citas.append(fila_dict)

        return jsonify({
            'datos': arr_citas,
            'mensaje': f"Citas del doctor {nombre_doctor}",
            'exito': True
        }), 200
    except Exception as ex:
        return jsonify({
            'mensaje': f"Error al obtener citas: {str(ex)}",
            'exito': False
        }), 500

# Buscar citas por nombre del paciente
@citas_bp.route("/citas/paciente/<nombre_paciente>", methods=["GET"])
@jwt_required()
def buscar_citas_paciente(nombre_paciente):
    try:
        cursor = conexion.connection.cursor()
        cursor.callproc('sp_buscar_citas_paciente', (nombre_paciente,))
        datos = cursor.fetchall()
        
        if not datos:
            cursor.nextset()
            return jsonify({
                'datos': [],
                'mensaje': f"El paciente '{nombre_paciente}' no tiene citas registradas",
                'exito': False
            }), 404

        columnas = [desc[0] for desc in cursor.description]
        cursor.nextset()
        
        arr_citas = []
        for fila in datos:
            fila_dict = {}
            for col, val in zip(columnas, fila):
                if isinstance(val, (datetime, date, time, timedelta)):
                    fila_dict[col] = str(val)
                else:
                    fila_dict[col] = val
            arr_citas.append(fila_dict)

        return jsonify({
            'datos': arr_citas,
            'mensaje': f"Citas del paciente {nombre_paciente}",
            'exito': True
        }), 200
    except Exception as ex:
        return jsonify({
            'mensaje': f"Error al obtener citas: {str(ex)}",
            'exito': False
        }), 500

@citas_bp.route("/citas", methods=["POST"])
@jwt_required()
def agregar_cita():
    try:
        campos_requeridos = ['id_paciente', 'id_doctor', 
                           'fecha', 'hora', 'estado', 
                           'motivo', 'precio_costo']
        

        for campo in campos_requeridos:
            if campo not in request.json:
                return jsonify({
                    'mensaje': f"El campo {campo} es requerido",
                    'exito': False
                }), 400

        cursor = conexion.connection.cursor()
        cursor.execute("SELECT id_doctor FROM doctores WHERE id_doctor = %s", 
                      (request.json['id_doctor'],))
        if not cursor.fetchone():
            return jsonify({
                'mensaje': "El doctor no existe",
                'exito': False
            }), 404

        cursor.execute("SELECT id_paciente FROM pacientes WHERE id_paciente = %s", 
                      (request.json['id_paciente'],))
        if not cursor.fetchone():
            return jsonify({
                'mensaje': "El paciente no existe",
                'exito': False
            }), 404

        cursor.execute("""
            SELECT id_cita FROM citas 
            WHERE id_doctor = %s AND fecha = %s AND hora = %s
        """, (request.json['id_doctor'], request.json['fecha'], request.json['hora']))
        
        if cursor.fetchone():
            return jsonify({
                'mensaje': "El doctor ya tiene una cita en ese horario",
                'exito': False
            }), 409

        try:
            fecha = datetime.strptime(request.json['fecha'], '%Y-%m-%d').date()
            hora = datetime.strptime(request.json['hora'], '%H:%M:%S').time()
            precio = float(request.json['precio_costo'])
            if precio <= 0:
                raise ValueError("El precio debe ser mayor a 0")
        except ValueError as e:
            return jsonify({
                'mensaje': f"Error de formato: {str(e)}",
                'exito': False
            }), 400

        cursor.callproc('sp_registrar_cita', (
            request.json['id_paciente'],
            request.json['id_doctor'],
            request.json['fecha'],
            request.json['hora'],
            'nueva',
            request.json['motivo'],
            request.json['precio_costo']
        ))
        
        conexion.connection.commit()
        
        return jsonify({
            'mensaje': "Cita agregada exitosamente",
            'exito': True
        }), 201
        
    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error al agregar cita: {str(ex)}",
            'exito': False
        }), 500
    
@citas_bp.route("/citas/fecha/<fecha>", methods=["GET"])
@jwt_required()
def buscar_citas_fecha(fecha):
    try:
        cursor = conexion.connection.cursor()
        cursor.callproc('sp_buscar_citas_fecha', (fecha,))
        datos = cursor.fetchall()

        if not datos:
            cursor.nextset()
            return jsonify({
                'datos': [],
                'mensaje': f"No hay citas para la fecha {fecha}",
                'exito': False
            }), 404
        
        columnas = [desc[0] for desc in cursor.description]
        cursor.nextset()
        
        arr_citas = []
        for fila in datos:
            fila_dict = {}
            for col, val in zip(columnas, fila):
                if isinstance(val, (datetime, date, time, timedelta)):
                    fila_dict[col] = str(val)
                else:
                    fila_dict[col] = val
            arr_citas.append(fila_dict)
        
        return jsonify({
            'datos': arr_citas,
            'mensaje': f"Citas para la fecha {fecha}",
            'exito': True
        }), 200

    except Exception as ex:
        return jsonify({
            'mensaje': f"Error al obtener citas: {str(ex)}",
            'exito': False
        }), 500

@citas_bp.route("/citas/<int:id_cita>", methods=["PUT"])
@jwt_required() 
def actualizar_cita(id_cita):
    try:
        cursor = conexion.connection.cursor()
        
        cursor.execute("SELECT id_cita FROM citas WHERE id_cita = %s", (id_cita,))
        if not cursor.fetchone():
            return jsonify({
                'mensaje': "La cita no existe",
                'exito': False
            }), 404

        campos_permitidos = ['fecha', 'hora', 'estado', 'motivo', 'precio_costo']
        
        updates = []
        valores = []
        for campo in campos_permitidos:
            if campo in request.json:
                updates.append(f"{campo} = %s")
                valores.append(request.json[campo])
        
        if not updates:
            return jsonify({
                'mensaje': "No se proporcionaron campos para actualizar",
                'exito': False
            }), 400

        valores.append(id_cita)
        sql = f"UPDATE citas SET {', '.join(updates)} WHERE id_cita = %s"
        
        cursor.execute(sql, tuple(valores))
        conexion.connection.commit()

        return jsonify({
            'mensaje': "Cita actualizada exitosamente",
            'exito': True
        }), 200
    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error al actualizar cita: {str(ex)}",
            'exito': False
        }), 500

# Buscar citas por nombre de especialidad
@citas_bp.route("/citas/especialidad/<nombre_especialidad>", methods=["GET"])
@jwt_required()
def buscar_citas_especialidad(nombre_especialidad):
    try:
        cursor = conexion.connection.cursor()
        cursor.callproc('sp_buscar_citas_especialidad', (nombre_especialidad,))
        datos = cursor.fetchall()
        
        if not datos:
            cursor.nextset()
            return jsonify({
                'datos': [],
                'mensaje': f"No hay citas para la especialidad '{nombre_especialidad}'",
                'exito': False
            }), 404

        columnas = [desc[0] for desc in cursor.description]
        cursor.nextset()
        
        arr_citas = []
        for fila in datos:
            fila_dict = {}
            for col, val in zip(columnas, fila):
                if isinstance(val, (datetime, date, time, timedelta)):
                    fila_dict[col] = str(val)
                else:
                    fila_dict[col] = val
            arr_citas.append(fila_dict)

        return jsonify({
            'datos': arr_citas,
            'mensaje': f"Citas de la especialidad {nombre_especialidad}",
            'exito': True
        }), 200
    except Exception as ex:
        return jsonify({
            'mensaje': f"Error al obtener citas: {str(ex)}",
            'exito': False
        }), 500

@citas_bp.route("/citas/<int:id_cita>", methods=["DELETE"])
@jwt_required()
def eliminar_cita(id_cita):
    try:
        cursor = conexion.connection.cursor()
        
        cursor.execute("SELECT id_cita FROM citas WHERE id_cita = %s", (id_cita,))
        if not cursor.fetchone():
            return jsonify({
                'mensaje': "La cita no existe",
                'exito': False
            }), 404

        sql = "DELETE FROM citas WHERE id_cita = %s"
        cursor.execute(sql, (id_cita,))
        conexion.connection.commit()

        return jsonify({
            'mensaje': "Cita eliminada exitosamente",
            'exito': True
        }), 200
    except Exception as ex:
        conexion.connection.rollback()
        return jsonify({
            'mensaje': f"Error al eliminar cita: {str(ex)}",
            'exito': False
        }), 500
    
