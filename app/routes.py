# app/routes.py
from flask import Blueprint, request, jsonify, url_for, redirect, flash, render_template
from flask_login import login_user, logout_user, login_required, current_user
import json
from tb_rest_client.rest_client_pe import Device
from tb_rest_client.rest import ApiException
from app.main import get_rest_client, get_user_tb_v2, BRAM
from app.forms import LoginForm, DeviceForm, CreateUserForm
from app.models import User
from datetime import datetime

main = Blueprint('main', __name__)

# Define a private variable to store the password
_private_niggle = None

with get_rest_client(BRAM['email'], BRAM['password']) as rest_client:
    @main.route('/')
    @main.route('/login', methods=['GET', 'POST'])
    def login():
        global _private_niggle  # Declare the variable as global to modify it
        if current_user.is_authenticated:
            return redirect(url_for('main.dashboard'))
        
        form = LoginForm()
        if form.validate_on_submit():
            username = form.email.data
            password = form.password.data
            user = User.get(username, password)
            if user and user.verify_password(password):
                login_user(user)
                _private_niggle = password  # Save the password in the private variable
                return redirect(url_for('main.dashboard'))
            else:
                flash('Invalid password or expired token', 'warning')
        return render_template('login.html', title='Login', form=form)
    
    @main.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('main.login'))

    @main.route('/device', methods=['GET', 'POST'])
    @login_required
    def create_device():
        form = DeviceForm(request.form)
        if form.validate_on_submit():
            data = {
                "name": form.device_name.data,
                "type": form.device_type.data,
                "label": form.device_label.data,
                #"customer_id": current_user.get_dynamic_attribute('_customer_id').id,
                "additionalInfo": {
                    "description": form.device_description.data
                }
            }
            try:
                device_user, client = get_user_tb_v2(current_user.username, get_private_niggle(), True)
                if data['type'] == 'default':
                    data['device_profile_id'] = client.get_default_device_profile_info().id
                device = Device(
                    name=data['name'],
                    type=data['type'],
                    label=data['label'],
                    device_profile_id=data['device_profile_id'],
                    additional_info=data['additionalInfo']
                )
                device = client.save_device(device)
                access_token = client.get_device_credentials_by_device_id(device.id)
                client.logout()
                flash(f'Created {device.name} Successfully. Access-Token = {access_token.credentials_id}','success')
                return redirect(url_for('main.dashboard'))
            except ApiException as e:
                error_body = e.body.decode('utf-8')
                error_details = json.loads(error_body)
                flash(f"Error: {error_details.get('message')}", 'error')
                return redirect(url_for('main.create_device'))
            except Exception as e:
                flash(f"Error: {str(e)}", 'error')
                return redirect(url_for('main.create_device'), 'error')
        return render_template('device.html', title='Add Device', form=form)

    def chunk_list(lst, chunk_size):
        """Yield successive chunks from lst."""
        for i in range(0, len(lst), chunk_size):
            yield lst[i:i + chunk_size]

    @main.route('/')    
    @main.route('/dashboard')
    @login_required
    def dashboard():
        try:
            user, client = get_user_tb_v2(current_user.username, get_private_niggle(), True)
            devices = []
            page_data = client.get_user_devices(30, 0)
            devices.extend(page_data.data)
            while page_data.has_next:
                page_size, page = 30, 1
                page_data = client.get_user_devices(page_size, page)
                devices.extend(page_data.data)
                page += 1

            client.logout()
            chunked_devices = list(chunk_list(devices, 3))
            if devices:
                device_attributes = [
                    attr for attr in dir(devices[0])
                    if not callable(getattr(devices[0], attr)) 
                    and not attr.startswith("__")
                    and not attr.startswith("_")
                    and attr not in ["customer_id", "tenant_id", "device_profile_id", "swagger_types", "attribute_map", "discriminator"]
                ]
            else:
                device_attributes = []
            for device in devices:
                timestamp_seconds = device.created_time / 1000.0
                device.created_time = datetime.fromtimestamp(timestamp_seconds)
            return render_template('dashboard.html', title='Dashboard', devices=chunked_devices, user=user, device_attributes=device_attributes)
        except ApiException as e:
            error_body = e.body.decode('utf-8')
            error_details = json.loads(error_body)
            flash(f"Error: {error_details.get('message')}", 'error')
            return redirect(url_for('main.create_device'))
        except Exception as e:
            flash(f"Error: {str(e)}", 'error')
            return redirect(url_for('main.create_device'))

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

            with get_rest_client(username=BRAM['email'], password=BRAM['password']) as rest_client:
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

 # Get the niggle   
def get_private_niggle():
    return _private_niggle