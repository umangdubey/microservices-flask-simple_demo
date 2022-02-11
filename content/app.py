import os
import csv
import requests
import datetime
import logging as log
from collections import Counter
from io import TextIOWrapper
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.exceptions import NotFound

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
log.basicConfig(filename='record.log', level=log.DEBUG,
                format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')


class Content(db.Model):
    __tablename__ = 'content'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    story = db.Column(db.String, nullable=False)
    user_id = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime)

    def __init__(self, title, story, user_id):
        self.title = title
        self.story = story
        self.user_id = user_id
        self.created_at = datetime.datetime.now()


db.create_all()


@app.route('/upload', methods=['POST'])
def upload_csv():
    """
    Used to upload csv file in database
    """
    try:
        if request.method == 'POST':
            csv_file = request.files['file']
            csv_file = TextIOWrapper(csv_file, encoding='utf-8')
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                content = Content(title=row[0], story=row[1], user_id=row[2])
                db.session.add(content)
                db.session.commit()
            return jsonify({"message": "Books Uploaded Successfully"})
    except Exception as e:
        log.error(e, exc_info=True)
        return custom_error(message=f"Book Upload process fail {e}", status_code=400)


@app.route('/get_content', methods=['GET'])
def get_all_content():
    """
    Used to all content
    """
    contents = []
    content_obj = fetch_all()
    if content_obj:
        for content in content_obj:
            del content.__dict__['_sa_instance_state']
            contents.append(content.__dict__)
        return make_response(jsonify(contents))
    return jsonify({"message": "No content found", "status_code": 400})


@app.route('/content/<id>', methods=['GET'])
def get_content_by_id(id):
    """
    Fetch content by id
    """
    content_obj = fetch_by_id(params={"id": id})
    if content_obj:
        del content_obj.__dict__['_sa_instance_state']
        return jsonify(content_obj.__dict__)
    return custom_error(message=f"Content id {id} Not Found", status_code=400)


@app.route('/content/<id>', methods=['PUT'])
def update_content(id):
    """
    Update content 
    """
    body = request.get_json()
    user_obj = fetch_by_id(params={"id": id})
    if user_obj:
        db.session.query(Content).filter_by(id=id).update(
            dict(user_id=body['user_id'], title=body['title'], story=body['story']))
        db.session.commit()
        return jsonify({"message": "Content Update Successfully", "status_code": 200})
    else:
        return custom_error(message=f"User id {body['user_id']} Not found ", status_code=400)


@app.route('/content/<id>', methods=['DELETE'])
def delete_content(id):
    """
    Delete Content
    """
    try:
        user_obj = fetch_by_id(params={"id": id})
        if user_obj:
            db.session.query(Content).filter_by(id=id).delete()
            db.session.commit()
            return jsonify({"message": "Content Delete Successfully", "status_code": 200})
    except Exception as e:
        log.error(e, exc_info=True)
        return custom_error(message=f"Content with id {id} Not Found", status_code=400)


@app.route('/top_content', methods=['GET'])
def get_top_content():
    """
    Sort content based on it user-interaction
    """
    resp = requests.get(
        'http://user_interaction:80/top_user_interaction').json()

    contents = []
    a = Counter(resp)
    for keys, values in a.items():
        content_obj = Content.query.get(keys)
        del content_obj.__dict__['_sa_instance_state']
        contents.append(content_obj.__dict__)
    return jsonify(contents)


@app.route('/get_recent_content', methods=['GET'])
def get_recent_content():
    """
    Sort content based on created date
    """
    contents = []
    for content in Content.query.order_by(Content.created_at.desc()).all():
        del content.__dict__['_sa_instance_state']
        contents.append(content.__dict__)
    return jsonify(contents)


def custom_error(message, status_code):
    """
    Custom error handling
    """
    response = {"message": message,
                "status": status_code}
    return jsonify(response)


def fetch_all():
    """
    Fetches data from DB by provided data.
    """
    try:
        data_objects = Content.query.all()
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
            Content).filter_by(**params).first()
        if data_object:
            return data_object
    except Exception as e:
        log.error(e, exc_info=True)
        return False
