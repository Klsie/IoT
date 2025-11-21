from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import pyodbc
import joblib
import pandas as pd

app = Flask(__name__)

# ================================
# 🔹 CONFIGURACIÓN DE AZURE SQL
# ================================
server = os.getenv("DB_SERVER")
database = os.getenv("DB_NAME")
username = os.getenv("DB_USER")
password = os.getenv("DB_PASS")
driver = '{ODBC Driver 18 for SQL Server}'  

# Crear la conexión global
def get_connection():
    try:
        conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 18 for SQL Server}};'
            f'SERVER={server};'
            f'PORT=1433;'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password};'
            'Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
        )
        print("✅ Conexión exitosa a Azure SQL")
        return conn
    except Exception as e:
        print("❌ Error de conexión a Azure SQL:", e)  # 👈 Esto mostrará el error real
        return None



# ================================
# 🔹 CARGAR MODELO DE ML
# ================================
try:
    model = joblib.load("modelo_arenero.pkl")
    print("✅ Modelo cargado correctamente.")
except Exception as e:
    print("❌ No se pudo cargar el modelo:", e)
    model = None


# ================================
# 🔹 RUTAS
# ================================
@app.route("/", methods=["GET"])
def root():
    return jsonify({"mensaje": "Bienvenido a la API del arenero IoT con ML y Azure 🚀"}), 200


@app.route("/api/saludo", methods=["GET"])
def saludo():
    return jsonify({"mensaje": "API funcionando correctamente"}), 200


# ======================================
# 🧩 ENDPOINT PRINCIPAL: PREDICCIÓN Y BD
# ======================================
@app.route("/api/datos", methods=["POST"])
def recibir_datos():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400

        # Extraer variables esperadas
        peso = data.get("peso")
        distancia = data.get("distancia")
        limpieza = data.get("limpieza")

        if peso is None or distancia is None or limpieza is None:
            return jsonify({"error": "Faltan datos requeridos"}), 400

        # Convertir a tipos nativos (evita numpy.int64)
        try:
            peso = float(peso)
            distancia = float(distancia)
            limpieza = int(limpieza)
        except ValueError:
            return jsonify({"error": "Los datos deben ser numéricos"}), 400

        # 🧠 Generar predicción con el modelo
        if model:
            df = pd.DataFrame([[peso, distancia, limpieza]],
                              columns=["peso_gato", "distancia", "limpieza"])
            pred = model.predict(df)[0]

            # Convertir cualquier numpy tipo a Python nativo
            if hasattr(pred, "item"):
                prediccion = int(pred.item())
            else:
                prediccion = int(pred)
        else:
            prediccion = None

        # Convertir a nativos nuevamente por si acaso
        peso = float(peso)
        distancia = float(distancia)
        limpieza = int(limpieza)
        prediccion = int(prediccion) if prediccion is not None else None

        # 💾 Guardar en Azure SQL
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO DatosArenero (peso, distancia, limpieza, prediccion)
                VALUES (?, ?, ?, ?)
            """, (peso, distancia, limpieza, prediccion))
            conn.commit()
            cursor.close()
            conn.close()
        else:
            print("⚠️ No se guardaron datos, conexión a SQL fallida.")

        return jsonify({
            "status": "ok",
            "peso": peso,
            "distancia": distancia,
            "limpieza": limpieza,
            "prediccion": prediccion
        }), 201

    except Exception as e:
        print("❌ Error en /api/datos:", e)
        return jsonify({"error": str(e)}), 500



@app.route("/api/testenv", methods=["GET"])
def test_env():
    return {
        "DB_SERVER": os.getenv("DB_SERVER"),
        "DB_NAME": os.getenv("DB_NAME"),
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASS": "*********" if os.getenv("DB_PASS") else None
    }, 200

# ======================================
# 📦 OPCIONAL: Obtener últimos registros
# ======================================
@app.route("/api/registros", methods=["GET"])
def obtener_registros():
    conn = None
    try:
        # Parámetros opcionales de paginación
        limite = int(request.args.get("limit", 10))  # default 10
        if limite > 100:
            limite = 100  # Protección contra cargas excesivas

        conn = get_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

        cursor = conn.cursor()
        query = f"SELECT TOP ({limite}) * FROM DatosArenero ORDER BY id DESC"
        cursor.execute(query)

        columnas = [column[0] for column in cursor.description]
        registros = [dict(zip(columnas, row)) for row in cursor.fetchall()]

        if not registros:
            return jsonify({"message": "No hay registros disponibles"}), 200

        return jsonify({"total": len(registros), "registros": registros}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if conn:
            conn.close()
# ======================================
# 📦 Prediccion: Obtener registros de Prueba API
# ======================================

@app.route("/api/prediccion", methods=["POST"])
def hacer_prediccion():
    try:
        data = request.get_json()

        peso = data.get("peso")
        distancia = data.get("distancia")
        limpieza = data.get("limpieza")

        if peso is None or distancia is None or limpieza is None:
            return jsonify({"error": "Faltan datos para la predicción"}), 400

        modelo = joblib.load("modelo_arenero.pkl")

        df = pd.DataFrame([[peso, distancia, limpieza]], 
                          columns=["peso_gato","distancia","limpieza"])

        prediccion = modelo.predict(df)[0]

        return jsonify({
            "input": data,
            "prediccion": int(prediccion)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ======================================
# 🚀 ACTIVAR / DESACTIVAR LIMPIEZA
# ======================================

# Variable global para indicar si se pidió limpieza
limpieza_solicitada = False

@app.route("/api/activar_limpieza", methods=["POST"])
def activar_limpieza():
    global limpieza_solicitada
    data = request.get_json()

    activar = data.get("activar")

    # Validar booleano
    if activar is None:
        return jsonify({"error": "Falta el parámetro 'activar' (true/false)"}), 400

    limpieza_solicitada = bool(activar)

    return jsonify({
        "status": "ok",
        "limpieza_solicitada": limpieza_solicitada
    }), 200


# ======================================
# 🚀 ESP32 CONSULTA SI DEBE LIMPIAR
# ======================================
@app.route("/api/estado_limpieza", methods=["GET"])
def estado_limpieza():
    global limpieza_solicitada

    return jsonify({
        "limpieza_solicitada": limpieza_solicitada
    }), 200


# ======================================
# 🚀 ESP32 NOTIFICA QUE YA LIMPIÓ
# ======================================
@app.route("/api/limpieza_realizada", methods=["POST"])
def limpieza_realizada():
    global limpieza_solicitada

    limpieza_solicitada = False

    return jsonify({
        "status": "ok",
        "mensaje": "Limpieza completada y reiniciada"
    }), 200



# ================================
# 🔧 EJECUCIÓN LOCAL
# ================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
