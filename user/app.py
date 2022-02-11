import os
import logging as log
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
if __name__ == '__main__':
    app.run(debug=True)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
log.basicConfig(filename='record.log', level=log.DEBUG,
                format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    email_id = db.Column(db.String(120),  nullable=False)
    phone_number = db.Column(db.String(120), nullable=False)

    def __init__(self, first_name, last_name, email_id, phone_number):
        self.first_name = first_name
        self.last_name = last_name
        self.email_id = email_id
        self.phone_number = phone_number


db.create_all()


@app.route('/user/<id>', methods=['GET'])
def get_user_by_id(id):
    """
    Get User by id
    """
    user_obj = fetch_by_id(params={"id": id})
    if user_obj:
        del user_obj.__dict__['_sa_instance_state']
        return make_response(jsonify(user_obj.__dict__))
    return custom_error(message=f"User id {id} Not Found", status_code=400)


@app.route('/user', methods=['GET'])
def get_all_user():
    """
    Fetch all user
    """
    users = []
    user_obj = fetch_all()
    if user_obj:
        for user in user_obj:
            del user.__dict__['_sa_instance_state']
            users.append(user.__dict__)
        return make_response(jsonify(users))
    return jsonify({"message": "No User found", "status_code": 400})


@app.route('/user', methods=['POST'])
def create_user():
    """
    Create User
    """
    try:
        body = request.get_json()
        db.session.add(User(body['first_name'], body['last_name'],
                            body['email_id'], body['phone_number']))
        db.session.commit()
        return jsonify({"message": "User Created Successfully", "status_code": 200})
    except Exception as e:
        log.error(e, exc_info=True)
        response = {"Error": "Wrong Params", "status_code": 400}
        return jsonify(response)


@app.route('/user/<id>', methods=['PUT'])
def update_user(id):
    """
    Update User Detail
    """
    body = request.get_json()
    user_obj = fetch_by_id(params={"id": id})
    if user_obj:
        db.session.query(User).filter_by(id=id).update(
            dict(first_name=body['first_name'], last_name=body['last_name'], email_id=body['email_id'], phone_number=body['phone_number']))
        db.session.commit()
        return jsonify({"message": "User Update Successfully", "status_code": 200})
    else:
        return custom_error(message=f"User with id {id} not found", status_code=400)


@app.route('/user/<id>', methods=['DELETE'])
def delete_user(id):
    """
    Delete User using id
    """
    try:
        user_obj = fetch_by_id(params={"id": id})
        if user_obj:
            db.session.query(User).filter_by(id=id).delete()
            db.session.commit()
            return jsonify({"message": "User Delete Successfully", "status_code": 200})
    except Exception as e:
        log.error(e, exc_info=True)
        return custom_error(message=f"User with id {id} Not Deleted", status_code=400)


def fetch_by_id(params):
    """
    Fetches data from DB by id.
    """
    try:
        data_object = db.session.query(User).filter_by(**params).first()
        if data_object:
            return data_object
    except Exception as e:
        log.error(e, exc_info=True)
        return False


def fetch_all():
    """
    Fetches All data from DB .
    """
    try:
        data_objects = User.query.all()
        if data_objects:
            return data_objects
        return False
    except Exception as e:
        log.error(e, exc_info=True)
        return False


def custom_error(message, status_code):
    """
    Custom error handling
    """
    response = {"message": message,
                "status": status_code}
    return jsonify(response)
