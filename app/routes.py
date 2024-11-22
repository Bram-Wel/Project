# app/routes.py
from flask import Blueprint, request, jsonify, url_for, redirect, flash, render_template
from flask_login import login_user, logout_user, login_required, current_user
import json
from tb_rest_client.rest import ApiException
from app.main import get_rest_client, get_user_tb
from app.forms import LoginForm, DeviceForm, CreateUserForm
from app.models import User
import secrets

main = Blueprint('main', __name__)

with get_rest_client() as rest_client:
    @main.route('/')
    @main.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('main.dashboard'))
        
        form = LoginForm()
        if form.validate_on_submit():
            username = form.email.data
            password = form.password.data
            user = User.get(username)
            if user and user.verify_password(password):
                login_user(user)
                return redirect(url_for('main.dashboard'))
            else:
                flash('Invalid password or expired token')
        return render_template('login.html', title='Login', form=form)
    
    @main.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('main.login'))

    @main.route('/device', methods=['POST'])
    @login_required
    def create_device():
        form = DeviceForm()
        if form.validate_on_submit():
            data = {
                "name": form.device_name.data,
                "type": form.device_type.data,
                "label": form.device_label.data,
                "additionalInfo": {
                    "description": form.device_description.data
                }
            }
            try:
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
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        return render_template('device.html', title='Add Device', form=form)

    @main.route('/device/<device_id>', methods=['GET'])
    @login_required
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
        except Exception as e:
            return jsonify({"error": str(e)})
        
    @main.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html', title='Dashboard')

    @main.route('/create_user', methods=['GET', 'POST'])
    def create_user():
        form = CreateUserForm()
        if form.validate_on_submit():
            role = form.role.data.upper()
            user = User(
                id=form.id.data,
                username=form.username.data,
                role=role,
                password=form.password.data
            )

            try:
                user.save_to_db()
            except Exception as e:
                return jsonify({"error": str(e)}), 400

            with get_rest_client() as rest_client:
                try:
                    if role == "CUSTOMER_ADMIN":
                        customer = {
                            "title": form.username.data,
                            "name": form.username.data
                        }
                        created_customer = rest_client.save_customer(customer)
                        customer_id = created_customer.id.id
                    else:
                        customer_id = None

                    tb_user = {
                        "name": form.username.data,
                        "authority": role,
                        "email": f"{form.username.data}@example.com",
                        "password": form.password.data,
                        "customerId": {"id": customer_id} if customer_id else None
                    }
                    rest_client.save_user(tb_user)
                except ApiException as e:
                    return jsonify({"error": "Failed to create user in ThingsBoard"}), 500

            return jsonify({"message": "User created successfully"}), 201

        return render_template('create_user.html', title='Create User', form=form)