# app/routes.py
from flask import Blueprint, request, jsonify
import json
from tb_rest_client.rest import ApiException
from app.main import get_rest_client

main = Blueprint('main', __name__)
 
with get_rest_client() as rest_client:
    @main.route('/')
    @main.route('/login', methods=['GET', 'POST'])
    def login():
        return "Login"

    @main.route('/device', methods=['POST'])
    def create_device():
        try:
            data = request.get_json()
            device = rest_client.save_device(data)
            return jsonify(device)
        except ApiException as e:
            error_body = e.body.decode('utf-8')
            error_details = json.loads(error_body)
            return jsonify({
                "status": e.status,
                "reason": e.reason,
                "message": error_details.get('message')
            })

    @main.route('/device/<device_id>', methods=['GET'])
    def get_device(device_id):
        try:
            device = rest_client.get_device_by_id(device_id)
            return jsonify(device)
        except ApiException as e:
            error_body = e.body.decode('utf-8')
            error_details = json.loads(error_body)
            return jsonify({
                "status": e.status,
                "reason": e.reason,
                "message": error_details.get('message')
            })