#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import zipfile
import struct
import imghdr
import flask
import logging
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CONF = json.loads(open('./lightcomics.json', 'r').read())
ROOT = CONF['ROOT']
CONTENTS = CONF['CONTENTS']

# 경로 체크
if not os.path.exists(os.path.join(ROOT, CONTENTS)):
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
            logger.error("Failed to login")
            return authenticate()
        return f(*args, **kwargs)
    return decorated

class JsonSerializable(object):
	def toJson(self):
		return json.dumps(self, default = lambda x: x.__dict__)
		# return json.dumps(self.__dict__)

	def __repr__(self):
		return self.toJson()


# 이미지 모델
class BaseImageModel(JsonSerializable):
	def __init__(self):
		self._name = ""
		self._width = -1
		self._height = -1
	# def __repr__(self):
	# 	return "BaseImageModel %s (%sx%d)" % (self._name, self._width, self._height)
	def __str__(self):
		return "BaseImageModel %s (%sx%d)" % (self._name, self._width, self._height)

# 리스팅 모델
class BaseListingModel(JsonSerializable):
	def __init__(self):
		self._directories = []
		self._archives = []
		self._images = []
	# def __repr__(self):
	# 	return "BaseListingModel %s | %s | %s)" % (self._directories, self._archives, self._images)
	def __str__(self):
		return "BaseListingModel %s | %s | %s)" % (self._directories, self._archives, self._images)

def get_image_size_from_bytes(head):
	""" 이미지 사이즈를 반환한다 """
	im = Image.open(head)
	return im.size

def is_hidden_or_trash(full_path):
	""" 숨김 파일 또는 __MACOSX 디렉토리인지 확인한다. """
	if full_path.startswith('DS_STORE'):
		return True
	if full_path.startswith('__MACOSX'):	
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

def get_imagemodel_in_dir(dir_path):
	""" 디렉토리의(dir_path)의 이미지파일의 name, width, height를 모아서 반환한다."""
	image_models = []

	for name in os.listdir(dir_path):
	
		if is_allow_extensions_image(name):
			model = BaseImageModel()
			model._name = dir_path + name

			with open(model._name, mode='rb') as f:
				bytesIO = BytesIO()
				bytesIO.write(f.read())
				bytesIO.seek(0)
				size = get_image_size_from_bytes(bytesIO)
				model._width = size[0]
				model._height = size[1]	
			image_models.append(model)
				
	return image_models

def get_imagemodel_in_zip(zip_path):
	""" 압축파일(zip_path)의 이미지파일의 name, width, height를 모아서 반환한다."""
	image_models = []
	
	with zipfile.ZipFile(zip_path) as zf:
		for name in zf.namelist():
		
			if is_allow_extensions_image(name):
				model = BaseImageModel()
				model._name = name
								
				with zf.open(model._name) as f:
					bytesIO = BytesIO()
					bytesIO.write(f.read())
					bytesIO.seek(0)
					size = get_image_size_from_bytes(bytesIO)
					model._width = size[0]
					model._height = size[1]
					image_models.append(model)
				
	return image_models

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
		print(full_path)
		if os.path.isdir(full_path):
			listing_model._directories.append(full_path)
			print("is Dir")
			
		elif is_allow_extensions_archive(full_path):
			listing_model._archives.append(full_path)
			print("is achive")
						
		elif is_allow_extensions_image(full_path):
			listing_model._images.append(full_path)
			print("is image")
			
		else:
			print(name + " ignore")

			
	return listing_model
	
	
def get_unique_identifier(path):
	""" path에 해당하는 고유값을 생성하여 반환한다 """
	createdate = int(os.path.getctime(path))
	filesize = int(os.path.getsize(path))
	uniqueue_identifier = str(createdate + filesize)
	return uniqueue_identifier

def get_real_path(base, abs_path):
	""" 실제 경로를 반환한다 """
	abs_path = unquote(abs_path)
	real_path = os.path.join(base, abs_path)
	return real_path


# Flask 네트워크 맵핑 시작

@app.route('/')
@requires_auth
def root():
	app.logger.info("root directory")
	return listing("")
	basePath = get_real_path(ROOT, CONTENTS)
	real_path = os.path.join(basePath, "")
	
	model = get_listing_model(real_path)
	data = json.dumps(model.toJson(), ensure_ascii=False)
	
	response = flask.Response(data, headers=None)
	return response

@app.route('/<path:req_path>/')
@requires_auth
def listing(req_path):

	basePath = get_real_path(ROOT, CONTENTS)	
	full_path = "%s" % unquote(req_path)
	full_real_path = get_real_path(basePath, full_path)
	full_real_path = os.path.join(full_real_path, "")
	app.logger.info(full_real_path)

	model = get_listing_model(full_real_path)
	data = json.dumps(model.toJson(), ensure_ascii=False)
	
	response = flask.Response(data, headers=None)
	return response


@app.route('/<string:archive>.<string:archive_ext>/')
@requires_auth
def load_image_model(archive, archive_ext):
	return load_image_model2("", archive, archive_ext)


@app.route('/<path:req_path>/<string:archive>.<string:archive_ext>/')
@requires_auth
def load_image_model2(req_path, archive, archive_ext):
	
	basePath = get_real_path(ROOT, CONTENTS)	
	full_path = "%s" % unquote(req_path)
	full_real_path = get_real_path(basePath, full_path)
	full_real_path = os.path.join(full_real_path, "")
	app.logger.info(full_real_path)

	archive_name = archive + "." + archive_ext
	archive_path = os.path.join(full_real_path, archive_name)

	app.logger.info(archive_path)

	if archive_ext == 'zip':
		models = get_imagemodel_in_zip(archive_path)
                
		json_response = {"response":[obj.__dict__ for obj in models]}
		data = json.dumps(json_response, ensure_ascii=False)

		response = flask.Response(data, headers=None)
		return response
	

@app.route('/<path:req_path>/<string:archive>.<string:archive_ext>/<string:img_path>')
@requires_auth
def load_image_data(req_path, archive, archive_ext, img_path):
    app.logger.info(img_path)
    app.logger.info("내부경로 미존재")

    basePath = get_real_path(ROOT, CONTENTS)
    full_path = "%s" % unquote(req_path)
    full_real_path = get_real_path(basePath, full_path)
    full_real_path = os.path.join(full_real_path, "")
    
    app.logger.info(full_real_path)

    archive_name = archive + "." + archive_ext
    archive_path = os.path.join(full_real_path, archive_name)
    
    app.logger.info(archive_path)

    if archive_ext == 'zip':
        
        img = get_image_data_in_zip(archive_path, img_path)
        return flask.send_file(img, attachment_filename=os.path.basename(img_path), as_attachment=True)

    return ('', 204)



@app.route('/<path:req_path>/<string:archive>.<string:archive_ext>/<path:inner_path>/<string:img_path>')
@requires_auth
def load_image_data2(req_path, archive, archive_ext, inner_path, img_path):
    new_path = os.path.join(inner_path, img_path)
    return load_image_data(req_path, archive, archive_ext, new_path)



# 앱 시작
if __name__ == '__main__':
	app.run(host=CONF['HOST'], port=CONF['PORT'], debug=True)





# sample_zip_path = "/Users/shinhanlife/Desktop/sample.zip"
# # image_models_from_zip = get_imagemodel_in_zip(sample_zip_path)
# # for model in image_models_from_zip:
# # 	print(model)
# # 	bytes = get_image_data_in_zip(sample_zip_path, model._name)
# # 	print(bytes)
	

# print(" ")

# sample_dir_path = "/Users/shinhanlife/Desktop/"
# # image_models_from_dir = get_imagemodel_in_dir(sample_dir_path)
# # for model in image_models_from_dir:
# # 	print(model)
# # 	bytes = get_image_data_in_dir(model._name)
# # 	print(bytes)
	
	
	
# listing_model = get_listing_model(sample_dir_path)


# print(" ")
# print("listing_model._directories")
# for name in listing_model._directories:
# 	print(name)
# 	print(get_unique_identifier(name))

# print(" ")
# print("listing_model._archives")
# for name in listing_model._archives:
# 	print(name)
# 	print(get_unique_identifier(name))
	
# print(" ")
# print("listing_model._images")
# for name in listing_model._images:
# 	print(name)
# 	print(get_unique_identifier(name))





