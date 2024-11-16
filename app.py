from flask import Flask, request, jsonify
from tb_rest_client.rest import ApiException
from main import get_rest_client

app = Flask(__name__)

with get_rest_client() as rest_client:
    @app.route('/device', methods=['POST'])
    def create_device():
        try:
            data = request.get_json()
            device = rest_client.save_device(data)
            return jsonify(device)
        except ApiException as e:
            return jsonify({
                "status": e.status,
                "reason": e.reason,
                "message": e.body.decode('utf-8')
            })

    @app.route('/device/<device_id>', methods=['GET'])
    def get_device(device_id):
        try:
            device = rest_client.get_device_by_id(device_id)
            return jsonify(device)
        except ApiException as e:
            return jsonify({
                "status": e.status,
                "reason": e.reason,
                "message": e.body.decode('utf-8')
            })

    @app.route('/device/<device_id>', methods=['PUT'])
    def update_device(device_id):
        try:
            data = request.get_json()
            device = rest_client.update_device(device_id, data)
            return jsonify(device)
        except ApiException as e:
            return jsonify({
                "status": e.status,
                "reason": e.reason,
                "message": e.body.decode('utf-8')
            })

    @app.route('/device/<device_id>', methods=['DELETE'])
    def delete_device(device_id):
        try:
            rest_client.delete_device(device_id)
            return jsonify({
                "status": 200,
                "message": "Device deleted successfully"
            })
        except ApiException as e:
            return jsonify({
                "status": e.status,
                "reason": e.reason,
                "message": e.body.decode('utf-8')
            })
if __name__ == '__main__':
    app.run(port=5000, debug=True)