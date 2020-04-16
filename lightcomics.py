# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import sys
import json
import logging
import zipfile
import argparse
import flask
from PIL import Image
from collections import namedtuple
from io import BytesIO
from werkzeug.routing import BaseConverter
from functools import wraps

if sys.version_info.major == 3:
    from urllib.parse import *
    from io import StringIO
else:
    from urllib import *
    import StringIO

__version__ = (0, 2, 1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CONF = json.loads(open('./lightcomics.json', 'r').read())
ROOT = CONF['ROOT']
CONTENTS = CONF['CONTENTS']

image_exts = ["jpg", "gif", "png", "tif", "bmp", "jpeg", "tiff"]
archive_exts = ["zip", "rar", "cbz", "cbr"]
allows = image_exts + archive_exts

to_hex = lambda x: hex(ord(x))
ComixData = namedtuple('ComixData', 'Directories Files')

if not os.path.exists(os.path.join(ROOT, CONTENTS)):
    raise Exception("No Folder")

def get_ext(path_name):
    ext = os.path.splitext(path_name)[-1]
    return ext[1:] if ext else ext

app = flask.Flask(__name__)


def check_auth(username, password):
    return username == 'LightComics' and password == CONF['PASSWORD']

def authenticate():
    return flask.Response(
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = flask.request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            logger.error("Failed to login")
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def get_real_path(base, abs_path):
    abs_path = unquote(abs_path)
    real_path = os.path.join(base, abs_path)
    app.logger.debug("real_path: %s", real_path)
    return real_path

def get_files_in_zip_path(zipname, path):
    """get list of files in folder in zip file """
    data = ComixData(Directories=[], Files=[])
    with zipfile.ZipFile(zipname) as zf:
        for name in zf.namelist():
            
            with zf.open(name) as f:
                bytesIO = BytesIO()
                bytesIO.write(f.read())
                im = Image.open(bytesIO)
                app.logger.info(im.size)


            # name = name.decode('euc-kr').encode('utf-8')
            pardir, basename = os.path.split(name)
            if basename and path == pardir:
                app.logger.debug("get_files_in_zip_path: %s, %s", pardir, basename)
                data.Files.append(basename)
    if len(data.Files):
        response = flask.Response(json.dumps(data._asdict(), ensure_ascii=False), headers=None)
        return response

    return ('', 204)

def list_zip_files(zip_path):
    """ Response list of files in zip file """
    with zipfile.ZipFile(zip_path) as zf:
        data = ComixData(Directories=[], Files=[])
        app.logger.info("Loaded the zip file: %s", zip_path)
        dirs = [name for name in zf.namelist() if name.endswith('/')]
        subdirs = set([name.split('/')[0] for name in dirs])
        if subdirs:
            for dirname in subdirs:
                # dirname = dirname.decode('euc-kr').encode('utf-8')
                app.logger.debug('list_zip_files: %s, %s', dirname, [to_hex(c) for c in dirname])
                data.Directories.append(dirname)
            data = json.dumps(data._asdict(), ensure_ascii=False)
            response = flask.Response(data, headers=None)
            return response
    ## No folder in zip file
    return get_files_in_zip_path(zip_path, '')

@app.route('/')
@requires_auth
def root():
    app.logger.info("root directory")
    data = json.dumps(ComixData(Directories=[CONTENTS], Files=[])._asdict(), ensure_ascii=False)
    r = flask.Response(data, headers=None)
    return r

@app.route('/welcome.102/')
@requires_auth
def welcome():
    welcome_str = """Hello!\r\n""" \
        """allowDownload=True\r\n""" \
        """autoResizing=False\r\n""" \
        """minVersion=1.3\r\n""" \
        """supportJson=True"""
    return welcome_str

@app.route('/<path:req_path>/<string:name>.<string:ext>')
@requires_auth
def load_file(req_path, name, ext):
    """ Load file
        /folder1/folder2/file.jpg
        /folder1/folder2/file.zip
    """
    BASE_DIR = ROOT
    full_path = "%s/%s.%s" % (req_path, name, ext)
    real_full_path= get_real_path(BASE_DIR, full_path)

    if ext not in allows:
        return ('', 204)

    if not os.path.exists(real_full_path):
        logger.error("No Path: %s", real_full_path)
        return ('', 204)

    if ext in archive_exts:
        """ List zip files """
        logger.info("Archive File: %s", real_full_path)
        return list_zip_files(real_full_path)
    ## Render Image Files
    return flask.send_file(real_full_path)

@app.route('/<path:req_path>/<string:name>.<string:ext>/<path:zip_path>')
@requires_auth
def load_zip_folder(req_path, name, ext, zip_path):
    """ Get folder in zip file
        /folder1/folder2/file.zip/folder
    """
    BASE_DIR = ROOT
    full_path = "%s/%s.%s" % (req_path, name, ext)
    full_real_path = get_real_path(BASE_DIR, full_path)
    try:
        # zip_path = unquote(zip_path).encode('utf-8')
        zip_path = unquote(zip_path)
    except Exception as e:
        logger.info("Failed to encode: %s", zip_path)

    if not os.path.exists(full_real_path):
        logger.error("No Path: %s", full_real_path)
        return ('', 204)

    if ext not in archive_exts:
        return ('', 204)

    #get list of files in folder in zip file
    data = ComixData(Directories=[], Files=[])
    with zipfile.ZipFile(full_real_path) as zf:
        for name in zf.namelist():
            # name = name.decode('euc-kr').encode('utf-8')
            pardir, basename = os.path.split(name)
            if basename and zip_path == pardir:
                logger.info("get_files_in_zip_path: %s, %s", pardir, basename)
                data.Files.append(basename)
    if len(data.Files):
        response = flask.Response(json.dumps(data._asdict(), ensure_ascii=False), headers=None)
        return response

    return ('', 204)


@app.route('/<path:req_path>/<string:archive>.<string:archive_ext>/<string:name>.<string:ext>')
@requires_auth
def load_file_in_archive2(req_path, archive, archive_ext, name, ext):
    """ Get file in zip file
        /folder1/folder2/file.zip/file.jpg
    """
    BASE_DIR = ROOT
    full_path = u"%s/%s.%s" % (req_path, archive, archive_ext)
    zip_path = u"%s.%s" % (name, ext)
    full_real_path = get_real_path(BASE_DIR, full_path)
    logger.info("%s, %s", full_real_path, [to_hex(c) for c in full_real_path])
    try:
        zip_path = unquote(zip_path)
    except Exception as e:
        logger.info("Failed to encode: %s", zip_path)

    if ext == 'thm' or archive_ext not in archive_exts:
        logger.info("Unsupported file")
        return ('', 204)

    if os.path.exists(full_real_path) == False:
        logger.info("File doesn't exist: %s", full_real_path)
        return ('', 204)

    #Only zip files are supported <path>/file.zip/1/01.jpg
    ## Render single file
    with zipfile.ZipFile(full_real_path) as zf:
        for name in zf.namelist():
            # encoded_name = name.decode('euc-kr').encode('utf-8')
            encoded_name = name
            logger.info("%s(%s), %s(%s), %s, %s", encoded_name, type(encoded_name), zip_path, type(zip_path),
                [to_hex(c) for c in name], [to_hex(c) for c in zip_path])
            if encoded_name == zip_path:
                with zf.open(name) as f:
                    bytesIO = BytesIO()
                    bytesIO.write(f.read())
                    bytesIO.seek(0)
                    return flask.send_file(bytesIO, attachment_filename=os.path.basename(zip_path), as_attachment=True)
    logger.error("No file Name: %s", zip_path)
    return ('', 204)

@app.route('/<path:req_path>/<string:archive>.<string:archive_ext>/<path:zip_path>/<string:name>.<string:ext>')
@requires_auth
def load_file_in_archive(req_path, archive, archive_ext, zip_path, name, ext):
    """ Get file in zip file
        /folder1/folder2/file.zip/folder1/file.jpg
    """
    BASE_DIR = ROOT
    full_path = u"%s/%s.%s" % (req_path, archive, archive_ext)
    zip_path = u"%s/%s.%s" % (zip_path, name, ext)
    full_real_path = get_real_path(BASE_DIR, full_path)
    logger.info("%s, %s", full_real_path, [to_hex(c) for c in full_real_path])
    try:
        # zip_path = unquote(zip_path).encode('utf-8')
        zip_path = unquote(zip_path)
    except Exception as e:
        logger.info("Failed to encode: %s", zip_path)

    if ext == 'thm' or archive_ext not in archive_exts:
        logger.info("Unsupported file")
        return ('', 204)

    # if os.path.exists(full_real_path.encode('utf-8')):
    if os.path.exists(full_real_path) == False:
        logger.info("File doesn't exist: %s", full_real_path)
        return ('', 204)

    #Only zip files are supported <path>/file.zip/1/01.jpg
    ## Render single file
    with zipfile.ZipFile(full_real_path) as zf:
        for name in zf.namelist():
            # encoded_name = name.decode('euc-kr').encode('utf-8')
            encoded_name = name
            logger.info("%s(%s), %s(%s), %s, %s", encoded_name, type(encoded_name), zip_path, type(zip_path),
                [to_hex(c) for c in name], [to_hex(c) for c in zip_path])
            if encoded_name == zip_path:
                with zf.open(name) as f:
                    bytesIO = BytesIO()
                    bytesIO.write(f.read())
                    bytesIO.seek(0)
                    return flask.send_file(bytesIO, attachment_filename=os.path.basename(zip_path), as_attachment=True)
    logger.error("No file Name: %s", zip_path)
    return ('', 204)

@app.route('/<path:req_path>')
@requires_auth
def load_folders(req_path):
    BASE_DIR = ROOT
    ROOT_CONTENTS = os.path.join(BASE_DIR, CONTENTS)
    real_path = get_real_path(BASE_DIR, req_path)

    ## List up Root folder
    if real_path == ROOT_CONTENTS:
        data = ComixData(Directories=[], Files=[])
        for name in os.listdir(real_path):
            # name = name.encode('utf-8')
            data.Directories.append(name)
        response = flask.Response(json.dumps(data._asdict(), ensure_ascii=False), headers=None)
        return response

    if not os.path.exists(real_path):
        logger.error("No Path: %s", real_path)
        return ('', 204)

    data = ComixData(Directories=[], Files=[])
    ## Send list of files
    if os.path.isdir(real_path):
        for name in os.listdir(real_path):
            if os.path.isdir(os.path.join(real_path, name)) or get_ext(name) == 'zip':
                data.Directories.append(name)
            elif get_ext(name) not in archive_exts:
                data.Files.append(name)
        response = flask.Response(json.dumps(data._asdict(), ensure_ascii=False), headers=None)
        return response

if __name__ == '__main__':
    app.run(host=CONF['HOST'], port=CONF['PORT'], debug=True)
