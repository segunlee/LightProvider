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
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import threading
from urllib.request import urlopen
import re
import socket


# 버전
__version__ = (1, 0, 3)


# 변수 설정
allow_extensions_image = ['jpg', 'gif', 'png', 'tif', 'bmp', 'jpeg', 'tiff']
allow_extensions_archive = ['zip', 'cbz']
allow_extensions = allow_extensions_image + allow_extensions_archive

ZIP_FILENAME_UTF8_FLAG = 0x800



# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)



# 설정파일 로그
CONF_ROOT_PATH = ""
CONF_SERVER_PORT = 12370
CONF_PASSWORD = ""
CONF_HOST = "0.0.0.0"


# 운영체제 변수
IS_OS_WINDOWS = sys.platform == 'win32'
IS_OS_MACOSX = sys.platform == 'darwin'
IS_OS_LINUX = sys.platform == 'linux'




if IS_OS_WINDOWS:
	CONF_ROOT_PATH = "c:/"
	CONF_SERVER_PORT = 12370
	CONF_PASSWORD = ""
	
elif IS_OS_MACOSX:
	CONF_ROOT_PATH = "/"
	CONF_SERVER_PORT = 12370
	CONF_PASSWORD = ""
	
elif IS_OS_LINUX:
	CONF = json.loads(open('./lightcomics.json', 'r').read())
	CONF_ROOT_PATH = CONF['ROOT']
	CONF_SERVER_PORT = CONF['PORT']
	CONF_PASSWORD = CONF['PASSWORD']
	CONF_HOST= CONF['HOST'];
	if not os.path.exists(CONF_ROOT_PATH):
		raise Exception("No Root Directory!!!!")

else:
	raise Exception("hmm?")



# 앱 선언
app = flask.Flask(__name__)


# 권한 체크
def check_auth(username, password):
	return username == 'LightComics' and password == CONF_PASSWORD

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

# 이미지 모델
class BaseImageModel(LightEncoder):
	def __init__(self):
		self._name = ""
		self._decode_name = ""
		self._width = -1
		self._height = -1

# 리스팅 모델
class BaseListingModel(LightEncoder):
	def __init__(self):
		self._root = CONF_ROOT_PATH
		self._directories = []
		self._archives = []
		self._images = []


# 함수
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
			model._name = os.path.join(dir_path, name).replace("\\","/")
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

# def get_imagemodel_in_rar(rar_path, mode):
# 	""" 압축파일(rar_path)의 이미지파일의 name, width, height를 모아서 반환한다."""
# 	image_models = []
	
# 	with rarfile.RarFile(rar_path) as rf:
# 		for name in rf.namelist():
		
# 			if is_allow_extensions_image(name):
# 				model = BaseImageModel()
# 				model._name = name
# 				if mode == "1":
# 					with rf.open(name) as f:
# 						bytesIO = BytesIO()
# 						bytesIO.write(f.read())
# 						bytesIO.seek(0)
# 						size = get_image_size_from_bytes(bytesIO)
# 						model._width = size[0]
# 						model._height = size[1]
				
# 				image_models.append(model)

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
		full_path = os.path.join(path, name).replace("\\","/")
		
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
	if abs_path == "":
		return base
	real_path = os.path.join(base, abs_path).replace("\\","/")
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
		itempath = os.path.join(folder, item).replace("\\","/")
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
	localhost:12370/
	"""
	app.logger.info("@app.route('/')")

	return listing("")


@app.route('/<path:req_path>/')
@requires_auth
def listing(req_path):
	"""
	리스팅
	localhost:12370/req_path/
	"""
	app.logger.info("@app.route('/<path:req_path>/')")

	basePath = get_real_path(CONF_ROOT_PATH, "")	
	full_path = "%s" % unquote(req_path)
	full_real_path = get_real_path(basePath, full_path)
	full_real_path = os.path.join(full_real_path, "").replace("\\","/")
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
	localhost:12370/sample.zip/
	"""
	app.logger.info("@app.route('/<string:archive>.<string:archive_ext>/')")

	return load_image_model2("", archive, archive_ext)


@app.route('/<path:req_path>/<string:archive>.<string:archive_ext>/')
@requires_auth
def load_image_model2(req_path, archive, archive_ext):
	"""
	압축파일 내부 이미지 정보
	localhost:12370/dir/sglee/sample.zip/
	"""
	app.logger.info("@app.route('/<path:req_path>/<string:archive>.<string:archive_ext>/')")

	basePath = get_real_path(CONF_ROOT_PATH, "")	
	full_path = "%s" % unquote(req_path)
	full_real_path = get_real_path(basePath, full_path)
	full_real_path = os.path.join(full_real_path, "").replace("\\","/")
	app.logger.info(full_real_path)


	archive_name = "%s" % unquote(archive) + "." + archive_ext
	archive_path = os.path.join(full_real_path, archive_name).replace("\\","/")

	app.logger.info(archive_path)

	mode = request.args.get('mode', "0")
	app.logger.info("mode: " + mode)

	if archive_ext == 'zip' or archive_ext == 'cbz':
		models = get_imagemodel_in_zip(archive_path, mode)
		data = json.dumps(models, indent=4, cls=LightEncoder)
		response = flask.Response(data, headers=None, mimetype='application/json')
		return response
	
	# elif archive_ext == 'rar':
	# 	models = get_imagemodel_in_rar(archive_path, mode)
	# 	data = json.dumps(models, indent=4, cls=LightEncoder)
	# 	response = flask.Response(data, headers=None, mimetype='application/json')
	# 	return response
	
	return ('', 204)


@app.route('/<string:archive>.<string:archive_ext>/<path:img_path>')
def load_image_data(archive, archive_ext, img_path):
	"""
	압축파일 내부 이미지 데이터 반환
	localhost:12370/sample.zip/img1.jpg
	localhost:12370/sample.zip/test/img1.jpg
	"""
	app.logger.info("@app.route('/<string:archive>.<string:archive_ext>/<path:img_path>')")
	
	return load_image_data2("", archive, archive_ext, img_path)


@app.route('/<path:req_path>/<string:archive>.<string:archive_ext>/<path:img_path>')
def load_image_data2(req_path, archive, archive_ext, img_path):
	"""
	압축파일 내부 이미지 데이터 반환
	localhost:12370/dir/sglee/sample.zip/img1.jpg
	localhost:12370/dir/sglee/sample.zip/test/img1.jpg
	"""
	app.logger.info("@app.route('/<path:req_path>/<string:archive>.<string:archive_ext>/<path:img_path>')")

	basePath = get_real_path(CONF_ROOT_PATH, "")
	full_path = "%s" % unquote(req_path)
	full_real_path = get_real_path(basePath, full_path)
	full_real_path = os.path.join(full_real_path, "").replace("\\","/")
	
	app.logger.info(full_real_path)

	archive_name = "%s" % unquote(archive) + "." + archive_ext
	archive_path = os.path.join(full_real_path, archive_name).replace("\\","/")
	
	app.logger.info(archive_path)

	img_path = unquote(img_path)
	app.logger.info(img_path)

	if archive_ext == 'zip' or archive_ext == 'cbz':
		img = get_image_data_in_zip(archive_path, img_path)
		return flask.send_file(img, attachment_filename=os.path.basename(img_path), as_attachment=True)

	return ('', 204)


@app.route('/id/<path:req_path>')
@requires_auth
def get_identifier(req_path):
	"""
	해당하는 경로의 파일 identifier를 반환한다.
	localhost:12370/dir/hello.zip
	"""
	app.logger.info("@app.route('/id/<path:req_path>')")

	basePath = get_real_path(CONF_ROOT_PATH, "")	
	full_path = "%s" % unquote(req_path)
	full_real_path = get_real_path(basePath, full_path)
	full_real_path = os.path.join(full_real_path, "").replace("\\","/")
	app.logger.info(full_real_path)

	model = BaseIdentifierModel()
	model._path = remove_trail_slash(full_real_path)
	model._identifier = get_unique_identifier(full_real_path)

	data = json.dumps(model, indent=4, cls=LightEncoder)
	response = flask.Response(data, headers=None, mimetype='application/json')
	return response




# UI 구현 for Windows or Mac OSX

def onClickServerState():
	global server_run
	global server_state_label
	global server_on_off_button
	global server_threading
	
	if server_run == True:
		tk.messagebox.showinfo("알림", "서버 정지는 정상적으로 동작되지 않습니다.\n프로그램 종료후 재시작 해야 합니다.")
		return
		shutdown_server()
		server_state_label['text'] = "서버: 정지됨"
		server_on_off_button['text'] = " 가동 "
	else:
		updateServerPort()
		updatePassword()
		server_threading.start()
		server_state_label['text'] = "서버: 가동중"
		server_on_off_button['text'] = " 정지 "
		
	server_run = not server_run

def start_server():
	app.logger.info("Server Start: " + str(CONF_SERVER_PORT))
	app.run(host=local_ip.get(), port=CONF_SERVER_PORT)
	
def shutdown_server():
	# TODO: 서버 어떻게 멈추냐.. 안되네
	# func = request.environ.get('werkzeug.server.shutdown')
    #     if func is None:
    #         raise RuntimeError('Not running with the Werkzeug Server')
	# func()
	app.logger.info("Sever Stopped")
	# server_threading.join()
	

def getPublicIp():
    data = str(urlopen('http://checkip.dyndns.com/').read())
    return re.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(data).group(1)

def updateServerIP():
	app.logger.info(getPublicIp())
	local_ip.set(socket.gethostbyname(socket.gethostname()))
	public_ip.set(getPublicIp())

def updateServerPort():
	global CONF_SERVER_PORT
	CONF_SERVER_PORT = int(server_port.get())
	app.logger.info(CONF_SERVER_PORT)

def updatePassword():
	global CONF_PASSWORD
	CONF_PASSWORD = password_var.get()
	app.logger.info(CONF_PASSWORD)

def updateRootPath():
	global CONF_ROOT_PATH
	folder_selected = filedialog.askdirectory()
	CONF_ROOT_PATH = folder_selected
	root_path_var.set(CONF_ROOT_PATH)
	app.logger.info(CONF_ROOT_PATH)

def resource_path(relative_path):    
	try:       
		base_path = sys._MEIPASS
	except Exception:
		base_path = os.path.abspath(".")
	return os.path.join(base_path, relative_path)


# Set UI values for Windows
if IS_OS_WINDOWS:
	server_run = False
	server_threading = threading.Thread(target=start_server)


	window = tk.Tk()
	server_state_label = tk.Label(window, text="서버: 중지됨", width=15, anchor="w", padx=10, pady=5)
	server_on_off_button = tk.Button(window, text=" 가동 ", command=onClickServerState, width=20)
	change_root_path_button = tk.Button(window, text=" 변경 ", command=updateRootPath, width=20)

	public_ip = tk.StringVar()
	local_ip = tk.StringVar()
	server_port = tk.StringVar()
	server_port.set(CONF_SERVER_PORT)
	password_var = tk.StringVar()
	password_var.set(CONF_PASSWORD)
	root_path_var = tk.StringVar()
	root_path_var.set(CONF_ROOT_PATH)

	local_ip_textbox = tk.Entry(window, width=20, textvariable=local_ip, state='readonly')
	public_ip_textbox = tk.Entry(window, width=20, textvariable=public_ip, state='readonly')
	server_port_textbox = tk.Entry(window, width=20, textvariable=server_port)
	password_textbox = tk.Entry(window, width=20, textvariable=password_var)
	root_path_textbox = tk.Entry(window, width=20, textvariable=root_path_var, state='readonly')

def applicationUI():
	global window
	global server_state_label
	global server_on_off_button
	global public_ip

	window.geometry("300x200")
	window.title("Light Provider")
	window.resizable(False, False)
	window.iconbitmap(default=resource_path('icon.ico'))
	reuse_label = tk.Label(window, text=" ", width=15, anchor="w")
	reuse_label.grid(row=0, column=0)

	server_state_label.grid(row=1, column=0)
	server_on_off_button.grid(row=1, column=1)
	
	reuse_label = tk.Label(window, text="Local IP", width=15, anchor="w")
	reuse_label.grid(row=2, column=0)
	local_ip_textbox.grid(row=2, column=1)

	reuse_label = tk.Label(window, text="Remote IP", width=15, anchor="w")
	reuse_label.grid(row=3, column=0)
	public_ip_textbox.grid(row=3, column=1)

	reuse_label = tk.Label(window, text="서버 Port", width=15, anchor="w")
	reuse_label.grid(row=4, column=0)
	server_port_textbox.grid(row=4, column=1)

	reuse_label = tk.Label(window, text="비밀번호", width=15, anchor="w")
	reuse_label.grid(row=5, column=0)
	password_textbox.grid(row=5, column=1)

	reuse_label = tk.Label(window, text="공유 폴더", width=15, anchor="w")
	reuse_label.grid(row=6, column=0)
	root_path_textbox.grid(row=6, column=1)

	reuse_label = tk.Label(window, text="폴더 변경", width=15, anchor="w")
	reuse_label.grid(row=7, column=0)
	change_root_path_button.grid(row=7, column=1)

	
	updateServerIP()

	window.mainloop()



# 앱 시작
if __name__ == '__main__':

	if IS_OS_WINDOWS:
		applicationUI()
		
	elif IS_OS_MACOSX:
		print("not yet")
		
	elif IS_OS_LINUX:
		app.run(host=CONF_HOST, port=CONF_SERVER_PORT)
		
	else:
		print("hmm..?")
		
	
	
