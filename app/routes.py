# app/routes.py
import logging
from flask import Blueprint, request, jsonify, url_for, redirect, flash, render_template
from flask_login import login_user, logout_user, login_required, current_user
import json
from tb_rest_client.rest_client_pe import Device, DeviceProfile, DeviceProfileData, Customer, User as TbUser, ActivateUserRequest
from tb_rest_client.rest import ApiException
from app.main import get_rest_client, get_user_tb_v2, BRAM
from app.forms import LoginForm, DeviceForm, CreateUserForm
from app.models import User
from datetime import datetime
import re

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
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {getattr(form, field).label.text}: {error}", 'info')
            
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
                else:
                    default = {'type': 'DEFAULT'}
                    device_profile = DeviceProfile(name=data['type'],
                                                   profile_data=DeviceProfileData(configuration=default,
                                                                                  transport_configuration=default),
                                                                                  type=default['type'],
                                                                                  transport_type=default['type'])
                    device_profile = client.save_device_profile(device_profile)
                    data['device_profile_id'] = device_profile.id

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
            page_data = client.get_all_device_infos(30, 0)
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
            customer = Customer(title=form.title.data)
            tb_user = {
                "name": form.username.data,
                "authority": role,
                "email": form.username.data
                #"password": form.password.data
                }
            with get_rest_client(username=BRAM['email'], password=BRAM['password']) as rest_client:
                try:
                    customer = rest_client.save_customer(body=customer)
                    # Fetch the automatically created "Customer Administrators" Group.
                    customer_admin = rest_client.get_entity_group_by_owner_and_name_and_type(
                        customer.id,
                        'USER',
                        'Customer Administrators'
                        )
                    tb_user['customer_id'] = customer.id

                    tb_user = TbUser(**tb_user)
                    tb_user = rest_client.save_user(tb_user, send_activation_mail=False)
                    activation_link = rest_client.get_activation_link(tb_user.id)
                    match = re.search(r'activateToken=([a-zA-Z0-9_-]+)', activation_link)
                    if match:
                        activation_token = match.group(1)
                    else:
                        raise Exception("Failed to get activation token")
                    jwt_token = rest_client.activate_user(
                        body=ActivateUserRequest(
                            activate_token=activation_token, 
                            password=form.password.data
                        ), 
                        send_activation_mail=False
                    )
                    rest_client.add_entities_to_entity_group(customer_admin.id, [tb_user.id.id])

                    # create the local copy of user to login
                    user = User(
                        username=form.username.data,
                        password=form.password.data
                    )
                    user.save_to_db()
                except ApiException as e:
                    flash("Failed to create user in ThingsBoard", 'error')
                except Exception as e:
                    flash(str(e), 'error')
                else:
                    flash("User created successfully", 'success')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {getattr(form, field).label.text}: {error}", 'info')

        return render_template('create_user.html', title='Create User', form=form)

    @main.route('/delete_device', methods=['POST'])
    def delete_device():
        device_id = request.form.get('device_id')
        if device_id:
            try:
                user, client = get_user_tb_v2(current_user.username, get_private_niggle(), True)
                client.delete_device(device_id)  # Delete the device using the device_id
                client.logout()
                flash('Device deleted successfully', 'info')
            except ApiException as e:
                error_body = e.body.decode('utf-8')
                error_details = json.loads(error_body)
                flash(f"Error: {error_details.get('message')}", 'error')
            except Exception as e:
                flash(f"Error: {str(e)}", 'error')
        else:
            flash('Device ID not provided', 'danger')
        return redirect(url_for('main.dashboard'))

    @main.route('/get_device_data/<device_id>', methods=['GET'])
    @login_required
    def get_device_data(device_id):
        try:
            user, client = get_user_tb_v2(current_user.username, get_private_niggle(), True)
            telemetry_data = client.telemetry_controller.get_latest_timeseries_using_get('DEVICE', device_id)
            client_attributes = client.telemetry_controller.get_attributes_by_scope_using_get('DEVICE', device_id, 'CLIENT_SCOPE')
            shared_attributes = client.telemetry_controller.get_attributes_by_scope_using_get('DEVICE', device_id, 'SHARED_SCOPE')
            server_attributes = client.telemetry_controller.get_attributes_by_scope_using_get('DEVICE', device_id, 'SERVER_SCOPE')
            client.logout()
            return jsonify({
                'telemetry': telemetry_data,
                'client_attributes': client_attributes,
                'shared_attributes': shared_attributes,
                'server_attributes': server_attributes
            })
        except ApiException as e:
            error_body = e.body.decode('utf-8')
            error_details = json.loads(error_body)
            return jsonify({"error": error_details.get('message')}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @main.route('/send_command/<device_id>', methods=['POST'])
    @login_required
    def send_command(device_id):
        command = request.form.get('command')
        if command:
            try:
                user, client = get_user_tb_v2(current_user.username, get_private_niggle(), True)
                client.send_command(device_id, command)
                client.logout()
                return jsonify({"message": "Command sent successfully"}), 200
            except ApiException as e:
                error_body = e.body.decode('utf-8')
                error_details = json.loads(error_body)
                return jsonify({"error": error_details.get('message')}), 500
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        else:
            return jsonify({"error": "Command not provided"}), 400

    @main.route('/create_alarm/<device_id>', methods=['POST'])
    @login_required
    def create_alarm(device_id):
        alarm_type = request.form.get('alarm_type')
        severity = request.form.get('severity')
        details = request.form.get('details')
        if alarm_type and severity:
            try:
                user, client = get_user_tb_v2(current_user.username, get_private_niggle(), True)
                alarm = {
                    "type": alarm_type,
                    "severity": severity,
                    "details": details,
                    "originator": {
                        "entityType": "DEVICE",
                        "id": device_id
                    }
                }
                client.save_alarm(alarm)
                client.logout()
                flash('Alarm created successfully', 'success')
                return redirect(url_for('main.dashboard'))
            except ApiException as e:
                error_body = e.body.decode('utf-8')
                error_details = json.loads(error_body)
                flash(f"Error: {error_details.get('message')}", 'error')
                return redirect(url_for('main.dashboard'))
            except Exception as e:
                flash(f"Error: {str(e)}", 'error')
                return redirect(url_for('main.dashboard'))
        else:
            flash('Alarm type and severity are required', 'warning')
            return redirect(url_for('main.dashboard'))

 # Get the niggle   
def get_private_niggle():
    return _private_niggle