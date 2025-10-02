from flask import Flask, request, jsonify
import os


app = Flask(__name__)


@app.route('/api/saludo')
def saludo():
    return jsonify({'mensaje': 'API funcionando en Azure 🚀'})


@app.route('/api/datos', methods=['POST'])
def recibir_datos():
    data = request.get_json()
    # ejemplo: guardar o procesar aquí
    print('Datos recibidos:', data)
    return jsonify({'status':'ok','data':data}), 201


if __name__ == '__main__':
# Solo para pruebas locales
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))