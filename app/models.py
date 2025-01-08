from flask_login import UserMixin
from tb_rest_client.rest import ApiException
from app.main import get_rest_client, get_user_tb, BRAM
from werkzeug.security import generate_password_hash, check_password_hash
import json

from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String, primary_key=True)
    username = db.Column(db.String, unique=True)
    role = db.Column(db.String)
    password_hash = db.Column(db.String)
    dynamic_attributes = db.Column(db.JSON, default={})

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
        self._password = password

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def __init__(self, username, password):
        with get_rest_client(BRAM['email'], BRAM['password']) as rest_client:
            try:
                user_instance = get_user_tb(username, rest_client)
                if user_instance:
                    self.id = user_instance.id.id
                    self.username = user_instance.email  # Use email as username
                    self.role = user_instance.authority  # Use authority for role
                    self.password = password  # Use provided password
                    self.dynamic_attributes = {
                        key: self.custom_serialize(value)
                        for key, value in user_instance.__dict__.items()
                        if key not in ['_id', 'id', 'email', 'authority', 'password']
                    }
            except ApiException as e:
                error_body = e.body.decode('utf-8')
                error_details = json.loads(error_body)
                raise Exception(f"API Exception: {error_details.get('message')}")

    @staticmethod
    def get(username, password=None):
        try:
            user = User.query.filter_by(username=username).first()
            if user:
                return user
            else:
                with get_rest_client(BRAM['email'], BRAM['password']) as rest_client:
                    try:
                        user_instance = get_user_tb(username, rest_client)
                        if user_instance:
                            new_user = User(
                                username=user_instance.email,  # Use email as username
                                password=password if password else 'Test123!'  # Use default password if not provided
                            )
                            new_user.dynamic_attributes = {
                                key: new_user.custom_serialize(value)
                                for key, value in user_instance.__dict__.items()
                                if key not in ['_id', 'id', 'email', 'authority', 'password']
                            }
                            new_user.role = user_instance.authority  # Set role from user_instance
                            new_user.id = user_instance.id.id  # Set id from user_instance
                            new_user.save_to_db()  # Save new user to the database
                            return new_user
                    except ApiException as e:
                        error_body = e.body.decode('utf-8')
                        error_details = json.loads(error_body)
                        raise Exception(f"API Exception: {error_details.get('message')}")
            return None
        except Exception as e:
            # Handle exceptions if necessary
            return None

    def save_to_db(self):
        existing_user = User.query.filter_by(username=self.username).first()
        if existing_user:
            if not existing_user.verify_password(self._password):
                raise Exception("Password doesn't match!")
            # update existing user given reason
            existing_user.role = self.role
        else:
            db.session.add(self)
        db.session.commit()

    def set_dynamic_attribute(self, key, value):
        self.dynamic_attributes[key] = self.custom_serialize(value)
        self.save_to_db()

    def get_dynamic_attribute(self, key):
        value = self.dynamic_attributes.get(key, None)
        return self.custom_deserialize(value)

    def custom_serialize(self, value):
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        elif isinstance(value, (int, float, str, bool)):
            return json.dumps(value)
        else:
            if value is None:
                return json.dumps(None)
            # Handle custom objects
            serialized_value = {
                "__class__": value.__class__.__name__,
                "__module__": value.__class__.__module__
            }
            if value.__dict__:
                serialized_value["__value__"] = value.__dict__
            return json.dumps(serialized_value)

    def custom_deserialize(self, value):
        if value is None:
            return None
        try:
            data = json.loads(value)
            if isinstance(data, dict) and "__class__" in data and "__module__" in data and "__value__" in data:
                # Handle custom objects
                class_name = data["__class__"]
                module_name = data["__module__"]
                class_value = data["__value__"]
                # Dynamically import the module and get the class
                module = __import__(module_name, fromlist=[class_name])
                cls = getattr(module, class_name)
                # Create an instance of the class and update its __dict__
                obj = cls.__new__(cls)
                obj.__dict__.update(class_value)
                return obj
            return data
        except (TypeError, json.JSONDecodeError):
            return value