import os
import sqlite3
import imghdr
import shortuuid
import datetime
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, send_file
from peewee import *
from werkzeug.utils import secure_filename
import config

app = Flask(__name__)

database = SqliteDatabase(config.DATABASE)

class Image(Model):
    id = TextField(primary_key=True)
    path = TextField()
    owner = TextField(null=True)
    added = DateTimeField(default=datetime.datetime.now())

    class Meta:
        database = database

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
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'no file param', 422
    file = request.files.get('file')
    owner = request.values.get('owner')
    if file.filename == '':
        return 'emtpy file name', 422
    filename = secure_filename(file.filename)
    dest = os.path.join(config.UPLOAD_DIR, filename)
    file.save(dest)
    if not imghdr.what(dest):
        os.remove(dest)
    image = Image.create(id=shortuuid.uuid(), owner=owner, path=dest)
    return image.id

@app.route('/l/<owner>')
@app.route('/list/<owner>')
def list(owner):
    images = Image.select().where(Image.owner == owner)
    for i in images:
        print(i)
    return 'k'

@app.route('/i/<id>')
def image(id):
    image = Image.get_or_none(Image.id == id)
    if not image:
        return '',404
    return send_file(image.path, os.path.basename(image.path))

@app.route('/recent')
def recent():
    count = int(request.values.get('count', 10))
    page = int(request.values.get('page', 1))
    images = Image.select().order_by(Image.added).paginate(page, count)
    for i in images:
        print(i.path)
    return 'k'
