from flask import Flask, request, jsonify

app = Flask(__name__)

# 🟢 Ruta para verificar que la API funciona
@app.route("/api/saludo", methods=["GET"])
def saludo():
    return jsonify({"mensaje": "API funcionando en Azure 🚀"}), 200


# 🟡 Ruta para recibir datos del ESP32
@app.route("/api/datos", methods=["POST"])
def recibir_datos():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400

        # Extraer datos esperados
        peso = data.get("peso")
        distancia = data.get("distancia")
        estado = data.get("estado")

        # Aquí podrías guardar en base de datos o procesar
        print("📩 Datos recibidos:", data)

        return jsonify({
            "status": "ok",
            "peso": peso,
            "distancia": distancia,
            "estado": estado
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔴 Ruta raíz opcional
@app.route("/", methods=["GET"])
def root():
    return jsonify({"mensaje": "Bienvenido a la API del arenero IoT"}), 200


# 🔧 Para ejecutar en local
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
