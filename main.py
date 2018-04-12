import os
import sqlite3
import imghdr
import shortuuid
import datetime
import json
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, send_file, jsonify
from peewee import *
from flask_cors import CORS
from werkzeug.utils import secure_filename
import config

app = Flask(__name__)
CORS(app)

database = SqliteDatabase(config.DATABASE)

class Image(Model):
    id = TextField(primary_key=True)
    path = TextField()
    owner = TextField(null=True)
    added = DateTimeField(default=datetime.datetime.now())
    private = BooleanField(default=False)
    expires = DateTimeField(default=None, null=True)
    delete_key = TextField(default=shortuuid.uuid())
    
    class Meta:
        database = database
        
    def to_dict(self, request):
        return {'owner': self.owner, 'added': self.added, 'expires': self.expires, 'url': self.url(request)}
        
    def url(self, request):
        return 'http://%s/i/%s' % (request.host, self.id)
    
    def delete_url(self, request):
        return 'http://%s/delete/%s?key=%s' % (request.host, self.id, self.delete_key)

def create_tables():
    with g.db:
        g.db.create_tables([Image])

@app.before_request
def before_request():
    g.db = database
    g.db.connect()

@app.teardown_appcontext
def close_db(error):
    g.db.close()

@app.before_first_request
def before_first_request():
    before_request()
    create_tables()
    
@app.route('/')
def index():
    print(request.headers)
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'no file param', 422
    file = request.files.get('file')
    owner = request.values.get('owner')
    private = request.values.get('private') is not None
    if file.filename == '':
        return 'emtpy file name', 422
    filename = secure_filename(file.filename)
    dest = os.path.join(config.UPLOAD_DIR, filename)
    file.save(dest)
    if not imghdr.what(dest):
        os.remove(dest)
    image = Image.create(id=shortuuid.uuid(), owner=owner, path=dest, private=private)
    return jsonify({'image-url': image.url(request), 'delete-url': image.delete_url(request)})

@app.route('/list/<owner>')
def list(owner):
    images = Image.select().where(Image.owner == owner)
    result = []
    for i in images:
        result.append(i.to_dict(request))
    return jsonify(result)

@app.route('/i/<id>')
def image(id):
    image = Image.get_or_none(Image.id == id)
    if not image:
        return jsonify({'result': 'image not found'}), 404
    return send_file(image.path, os.path.basename(image.path))

@app.route('/delete/<id>')
def delete(id):
    image = Image.get_or_none(Image.id == id)
    if not image:
        return jsonify({'result': 'image not found'}), 404
    delete_key = request.values.get('key')
    if not delete_key:
        return jsonify({'result': 'no delete key provided'}), 404        
    if image.delete_key == delete_key:
        image.delete_instance()
        return jsonify({'result': 'success'}), 200
    else:
        return jsonify({'result': 'denied'}), 403

@app.route('/recent')
def recent():
    count = int(request.values.get('count', 10))
    count = 50 if count > 50 else count
    page = int(request.values.get('page', 1))
    images = Image.select().where(Image.private == False).order_by(Image.added.desc()).paginate(page, count)
    result = []
    for i in images:
        result.append(i.to_dict(request))
    return jsonify(result)
