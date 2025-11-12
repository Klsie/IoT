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

# Crear la conexión global
def get_connection():
    try:
        conn = pyodbc.connect(
            f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}'
        )
        return conn
    except Exception as e:
        print("❌ Error de conexión a Azure SQL:", e)
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

        # 🧠 Generar predicción con el modelo
        df = pd.DataFrame([[peso, distancia, limpieza]], columns=["peso_gato", "distancia", "limpieza"])
        prediccion = model.predict(df)[0] if model else "Error: modelo no disponible"

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

        # 🟢 Respuesta al cliente
        return jsonify({
            "status": "ok",
            "peso": peso,
            "distancia": distancia,
            "limpieza": limpieza,
            "prediccion": int(prediccion) if isinstance(prediccion, (int, float)) else prediccion
        }), 201

    except Exception as e:
        print("❌ Error en /api/datos:", e)
        return jsonify({"error": str(e)}), 500


# ======================================
# 📦 OPCIONAL: Obtener últimos registros
# ======================================
@app.route("/api/registros", methods=["GET"])
def obtener_registros():
    try:
        conn = get_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500

        cursor = conn.cursor()
        cursor.execute("SELECT TOP 10 * FROM DatosArenero ORDER BY id DESC")
        columnas = [column[0] for column in cursor.description]
        registros = [dict(zip(columnas, row)) for row in cursor.fetchall()]
        conn.close()

        return jsonify({"registros": registros}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================
# 🔧 EJECUCIÓN LOCAL
# ================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
