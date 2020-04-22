#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import datetime
import json
import zipfile
# import rarfile
import struct
import imghdr
import platform
import logging
import chardet
import flask
from flask import request
from PIL import Image
from io import BytesIO
from werkzeug.routing import BaseConverter
from functools import wraps
from io import StringIO
from urllib.parse import *

__version__ = (1, 0, 0)

allow_extensions_image = ['jpg', 'gif', 'png', 'tif', 'bmp', 'jpeg', 'tiff']
allow_extensions_archive = ['zip', 'cbz']
allow_extensions = allow_extensions_image + allow_extensions_archive

ZIP_FILENAME_UTF8_FLAG = 0x800

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CONF = json.loads(open('./lightcomics.json', 'r').read())
ROOT = CONF['ROOT']

# 경로 체크
if not os.path.exists(ROOT):
	raise Exception("No Folder")

# 앱 선언
app = flask.Flask(__name__)

# 권한 체크
def check_auth(username, password):
	return username == 'LightComics' and password == CONF['PASSWORD']

# 권한 오류 반환
def authenticate():
	return flask.Response(
		'You have to login with proper credentials', 401,
		{'WWW-Authenticate': 'Basic realm="Login Required"'})

# 권한 요구
def requires_auth(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		auth = flask.request.authorization
		if not auth or not check_auth(auth.username, auth.password):
			return authenticate()
		return f(*args, **kwargs)
	return decorated


# JSON Encoder
class LightEncoder(json.JSONEncoder):
	def default(self, o):
		return o.__dict__


# Identifier 모델
class BaseIdentifierModel(LightEncoder):
	def __init__(self):
		self._path = ""
		self._identifier = ""

	def __str__(self):
		return "BaseIdentifierModel (%s, %s)" % (self._path, self._identifier)


# 이미지 모델
class BaseImageModel(LightEncoder):
	def __init__(self):
		self._name = ""
		self._decode_name = ""
		self._width = -1
		self._height = -1

	def __str__(self):
		return "BaseImageModel %s (%sx%d)" % (self._name, self._width, self._height)

# 리스팅 모델
class BaseListingModel(LightEncoder):
	def __init__(self):
		self._root = ROOT
		self._directories = []
		self._archives = []
		self._images = []

	def __str__(self):
		return "BaseListingModel %s | %s | %s)" % (self._directories, self._archives, self._images)

def fix_str(str):
	name = str
	
	try:
		name = name.encode('cp437').decode('cp949')
	except UnicodeEncodeError:
		name = name.encode('utf8')
		encoding = chardet.detect(name)['encoding']
		name = name.decode(encoding)

	return name

def get_image_size_from_bytes(head):
	""" 이미지 사이즈를 반환한다 """
	try:
		im = Image.open(head)
		return im.size
	except:
		return 0,0

def is_hidden_or_trash(full_path):
	""" 숨김 파일 또는 __MACOSX 디렉토리인지 확인한다. """
	if full_path.startswith('DS_STORE'):
		return True
	if '__MACOSX' in full_path:	
		return True
	return False

def get_extension(file_name):
	""" 확장자를 반환한다. (숨김파일 또는 MACOSX파일의 경우 확장자를 반환하지 않는다._) """
	extension = os.path.splitext(file_name)[-1]
	if extension.startswith('.'):
		extension = extension[1:]
	
	if is_hidden_or_trash(extension):
		return ''

	return extension

def is_allow_extensions_image(file_name):
	""" 허용된 이미지 확장자인 경우 True를 반환한다 """
	extension = get_extension(file_name)
	if extension not in allow_extensions_image:
		return False
	else:
		return True
		
def is_allow_extensions_archive(file_name):
	""" 허용된 압축파일 확장자인 경우 True를 반환한다 """
	extension = get_extension(file_name)
	if extension not in allow_extensions_archive:
		return False
	else:
		return True

def get_imagemodel_in_dir(dir_path, mode):
	""" 디렉토리의(dir_path)의 이미지파일의 name, width, height를 모아서 반환한다."""
	image_models = []

	for name in os.listdir(dir_path):
	
		if is_allow_extensions_image(name):
			model = BaseImageModel()
			model._name = dir_path + name
			if mode == "1":
				with open(model._name, mode='rb') as f:
					bytesIO = BytesIO()
					bytesIO.write(f.read())
					bytesIO.seek(0)
					size = get_image_size_from_bytes(bytesIO)
					model._width = size[0]
					model._height = size[1]

			image_models.append(model)
				
	return image_models

def get_imagemodel_in_zip(zip_path, mode):
	""" 압축파일(zip_path)의 이미지파일의 name, width, height를 모아서 반환한다."""
	image_models = []
	
	with zipfile.ZipFile(zip_path) as zf:
		for name in zf.namelist():
		
			if is_allow_extensions_image(name):
				model = BaseImageModel()
				model._name = name
				model._decode_name = fix_str(name)
				if mode == "1":
					with zf.open(name) as f:
						bytesIO = BytesIO()
						bytesIO.write(f.read())
						bytesIO.seek(0)
						size = get_image_size_from_bytes(bytesIO)
						model._width = size[0]
						model._height = size[1]

				image_models.append(model)
				
	return image_models

# def get_imagemodel_in_rar(rar_path):
# 	""" 압축파일(rar_path)의 이미지파일의 name, width, height를 모아서 반환한다."""
# 	image_models = []
	
# 	with rarfile.RarFile(rar_path) as rf:
# 		for name in rf.namelist():
		
# 			if is_allow_extensions_image(name):
# 				model = BaseImageModel()
# 				model._name = name
								
# 				with rf.open(name) as f:
# 					bytesIO = BytesIO()
# 					bytesIO.write(f.read())
# 					bytesIO.seek(0)
# 					size = get_image_size_from_bytes(bytesIO)
# 					model._width = size[0]
# 					model._height = size[1]
# 					image_models.append(model)
				
# 	return image_models

def get_image_data_in_dir(file_path):
	""" 이미지 파일(file_path)의 데이터를 반환한다. """
	with open(file_path, mode='rb') as f:
		bytesIO = BytesIO()
		bytesIO.write(f.read())
		bytesIO.seek(0)
		return bytesIO

def get_image_data_in_zip(zip_path, file_path):
	""" 압축 파일(zip_path)에서 이미지 파일(file_path)의 데이터를 반환한다. """
	with zipfile.ZipFile(zip_path) as zf:
		for name in zf.namelist():
			if name == file_path:
				if is_allow_extensions_image(name):
					model = BaseImageModel()
					model._name = name

					with zf.open(model._name) as f:
						bytesIO = BytesIO()
						bytesIO.write(f.read())
						bytesIO.seek(0)
						return bytesIO

def get_listing_model(path):
	""" 리스팅 """
	listing_model = BaseListingModel()

	for name in os.listdir(path):
		full_path = path + name
		
		if os.path.isdir(full_path):
			listing_model._directories.append(full_path)
			
		elif is_allow_extensions_archive(full_path):
			listing_model._archives.append(full_path)
						
		elif is_allow_extensions_image(full_path):
			listing_model._images.append(full_path)
			
		else:
			app.logger.info(name + " ignore")
			
	return listing_model

def get_unique_identifier(path):
	""" path에 해당하는 고유값을 생성하여 반환한다 """
	path = remove_trail_slash(path)
	createdate = int(os.stat(path).st_ctime)
	filesize = int(getSizeOf(path))
	app.logger.info("createdate: " + str(createdate))
	app.logger.info("filesize: " + str(filesize))
	uniqueue_identifier = str(createdate + filesize)
	app.logger.info(uniqueue_identifier)
	return uniqueue_identifier

def get_real_path(base, abs_path):
	""" 실제 경로를 반환한다 """
	abs_path = unquote(abs_path)
	real_path = os.path.join(base, abs_path)
	return real_path

def remove_trail_slash(s):
	""" 마지막 slash를 제거한다 """
	if s.endswith('/'):
		s = s[:-1]
	return s

def getSizeOf(path):
	""" 해당 경로 파일 또는 디렉토리의 사이즈를 구하여 반환한다 """
	total_size = os.path.getsize(path)

	if os.path.isdir(path) == False:
		return total_size

	for item in os.listdir(path):
		itempath = os.path.join(folder, item)
		if os.path.isfile(itempath):
			total_size += os.path.getsize(itempath)
		elif os.path.isdir(itempath):
			total_size += getFolderSize(itempath)
	return total_size



# Flask 네트워크 맵핑 시작
@app.route('/')
@requires_auth
def root():
	"""
	리스팅
	localhost:8909/
	"""
	app.logger.info("@app.route('/')")

	return listing("")


@app.route('/<path:req_path>/')
@requires_auth
def listing(req_path):
	"""
	리스팅
	localhost:8909/dir/
	"""
	app.logger.info("@app.route('/<path:req_path>/')")

	basePath = get_real_path(ROOT, "")	
	full_path = "%s" % unquote(req_path)
	full_real_path = get_real_path(basePath, full_path)
	full_real_path = os.path.join(full_real_path, "")
	app.logger.info(full_real_path)

	model = get_listing_model(full_real_path)
	data = json.dumps(model, indent=4, cls=LightEncoder)
	response = flask.Response(data, headers=None, mimetype='application/json')
	return response


@app.route('/<string:archive>.<string:archive_ext>/')
@requires_auth
def load_image_model(archive, archive_ext):
	"""
	압축파일 내부 이미지 정보
	localhost:8909/sample.zip/
	"""
	app.logger.info("@app.route('/<string:archive>.<string:archive_ext>/')")

	return load_image_model2("", archive, archive_ext)


@app.route('/<path:req_path>/<string:archive>.<string:archive_ext>/')
@requires_auth
def load_image_model2(req_path, archive, archive_ext):
	"""
	압축파일 내부 이미지 정보
	localhost:8909/dir/sglee/sample.zip/
	"""
	app.logger.info("@app.route('/<path:req_path>/<string:archive>.<string:archive_ext>/')")

	basePath = get_real_path(ROOT, "")	
	full_path = "%s" % unquote(req_path)
	full_real_path = get_real_path(basePath, full_path)
	full_real_path = os.path.join(full_real_path, "")
	app.logger.info(full_real_path)

	archive_name = archive + "." + archive_ext
	archive_path = os.path.join(full_real_path, archive_name)

	app.logger.info(archive_path)

	mode = request.args.get('mode', "0")
	app.logger.info("mode: " + mode)

	if archive_ext == 'zip':
		models = get_imagemodel_in_zip(archive_path, mode)
		data = json.dumps(models, indent=4, cls=LightEncoder)
		response = flask.Response(data, headers=None, mimetype='application/json')
		return response
	
	# elif archive_ext == 'rar':
	# 	models = get_imagemodel_in_rar(archive_path)
	# 	data = json.dumps(models, indent=4, cls=LightEncoder)
	# 	response = flask.Response(data, headers=None, mimetype='application/json')
	# 	return response
	return ('', 204)


@app.route('/<string:archive>.<string:archive_ext>/<path:img_path>')
def load_image_data(archive, archive_ext, img_path):
	"""
	압축파일 내부 이미지 데이터 반환
	localhost:8909/sample.zip/img1.jpg
	localhost:8909/sample.zip/test/img1.jpg
	"""
	app.logger.info("@app.route('/<string:archive>.<string:archive_ext>/<path:img_path>')")
	
	return load_image_data2("", archive, archive_ext, img_path)


@app.route('/<path:req_path>/<string:archive>.<string:archive_ext>/<path:img_path>')
def load_image_data2(req_path, archive, archive_ext, img_path):
	"""
	압축파일 내부 이미지 데이터 반환
	localhost:8909/dir/sglee/sample.zip/img1.jpg
	localhost:8909/dir/sglee/sample.zip/test/img1.jpg
	"""
	app.logger.info("@app.route('/<path:req_path>/<string:archive>.<string:archive_ext>/<path:img_path>')")

	basePath = get_real_path(ROOT, "")
	full_path = "%s" % unquote(req_path)
	full_real_path = get_real_path(basePath, full_path)
	full_real_path = os.path.join(full_real_path, "")
	
	app.logger.info(full_real_path)

	archive_name = archive + "." + archive_ext
	archive_path = os.path.join(full_real_path, archive_name)
	
	app.logger.info(archive_path)

	img_path = unquote(img_path)
	app.logger.info(img_path)

	if archive_ext == 'zip':
		
		img = get_image_data_in_zip(archive_path, img_path)
		return flask.send_file(img, attachment_filename=os.path.basename(img_path), as_attachment=True)

	return ('', 204)


@app.route('/id/<path:req_path>')
@requires_auth
def get_identifier(req_path):
	"""
	해당하는 경로의 파일 identifier를 반환한다.
	localhost:8909/dir/hello.zip
	"""
	app.logger.info("@app.route('/id/<path:req_path>')")

	basePath = get_real_path(ROOT, "")	
	full_path = "%s" % unquote(req_path)
	full_real_path = get_real_path(basePath, full_path)
	full_real_path = os.path.join(full_real_path, "")
	app.logger.info(full_real_path)

	model = BaseIdentifierModel()
	model._path = remove_trail_slash(full_real_path)
	model._identifier = get_unique_identifier(full_real_path)

	data = json.dumps(model, indent=4, cls=LightEncoder)
	response = flask.Response(data, headers=None, mimetype='application/json')
	return response




# 앱 시작
if __name__ == '__main__':
	app.run(host=CONF['HOST'], port=CONF['PORT'], debug=True)
