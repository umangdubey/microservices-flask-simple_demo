import os
import logging as log
import requests
from sqlalchemy.orm import load_only
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


class User_interaction(db.Model):
    __tablename__ = 'user_interaction'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    read_by = db.Column(db.Boolean)
    like_by = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, nullable=False)
    content_id = db.Column(db.Integer, nullable=False)

    def __init__(self, read_by, like_by, user_id, content_id):
        self.read_by = read_by
        self.like_by = like_by
        self.user_id = user_id
        self.content_id = content_id


db.create_all()


@app.route('/user_interaction/<id>', methods=['GET'])
def get_user_interaction_by_id(id):
    """
    Get User interaction by id
    """
    user_obj = fetch_by_id(params={"id": id})
    if user_obj:
        del user_obj.__dict__['_sa_instance_state']
        return make_response(jsonify(user_obj.__dict__))
    return custom_error(message=f"User id {id} Not Found", status_code=400)


@app.route('/user_interaction', methods=['GET'])
def get_all_user_interaction():
    """
    Fetch all user interaction
    """
    users = []
    user_obj = fetch_all()
    if user_obj:
        for user in user_obj:
            del user.__dict__['_sa_instance_state']
            users.append(user.__dict__)
        return make_response(jsonify(users))
    return jsonify({"message": "No User interaction found", "status_code": 400})


@app.route('/user_interaction', methods=['POST'])
def create_user_interaction():
    """
    create user interaction
    """
    try:
        body = request.get_json()
        if user_exit(body["user_id"]):
            db.session.add(User_interaction(
                body['read_by'], body['like_by'], body['user_id'], body['content_id']))
            db.session.commit()
            return jsonify({"message": "User interaction created Successfully", "status_code": 200})
        else:
            return custom_error(message=f"User id {body['user_id']} Not found ", status_code=400)
    except Exception as e:
        log.error(e, exc_info=True)
        response = {"Error": "Wrong Params", "status_code": 400}
        return jsonify(response)


@app.route('/user_interaction/<id>', methods=['PUT'])
def update_user_interaction(id):
    """
    Update user interaction
    """
    body = request.get_json()
    user_obj = fetch_by_id(params={"id": id})
    if user_obj:
        db.session.query(User_interaction).filter_by(id=id).update(
            dict(user_id=body['user_id'], read_by=body['read_by'], like_by=body['like_by'], content_id=body['content_id']))
        db.session.commit()
        return jsonify({"message": "User Interaction Update Successfully", "status_code": 200})
    else:
        return custom_error(message=f"User id {body['user_id']} Not found ", status_code=400)


@app.route('/user_interaction/<id>', methods=['DELETE'])
def delete_user_interaction(id):
    """
    Delete user interaction
    """
    try:
        user_obj = fetch_by_id(params={"id": id})
        if user_obj:
            db.session.query(User_interaction).filter_by(id=id).delete()
            db.session.commit()
            return jsonify({"message": "User Interaction Delete Successfully", "status_code": 200})
    except Exception as e:
        log.error(e, exc_info=True)
        return custom_error(message=f"User Interaction with id {id} Not Found", status_code=400)


@app.route('/user_interaction_update/<id>', methods=['PATCH'])
def update_read_like(id):
    """
    Update single data in user interaction
    """
    body = request.get_json()
    user_obj = fetch_by_id(params={"id": id})
    if user_obj:
        db.session.query(User_interaction).filter_by(id=id).update(body)
        db.session.commit()
        return jsonify({"message": f"User Interaction {[i for i in body.keys()][0]} update Successfully", "status_code": 200})
    else:
        return custom_error(message=f"User Interaction with id {id} Not Found", status_code=400)


def user_exit(id):
    """
    Used to check user exit to make user interaction
    """
    resp = requests.get('http://user:80/user/{}'.format(id)).json()
    if resp.get("status") == 400:
        return False
    else:
        return True


def fetch_all():
    """
    Fetches data from DB by provided data.
    """
    try:
        data_objects = User_interaction.query.all()
        if data_objects:
            return data_objects
        return False
    except Exception as e:
        log.error(e, exc_info=True)
        return False


def fetch_by_id(params):
    """
    Fetches data from DB by id.
    """
    try:
        data_object = db.session.query(
            User_interaction).filter_by(**params).first()
        if data_object:
            return data_object
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


@app.route('/top_user_interaction', methods=['GET'])
def get_top_interaction():
    """
    Used to sort top content in content service
    """
    values = [model.content_id for model in db.session.query(
        User_interaction).options(load_only('content_id'))]
    return jsonify(values)
