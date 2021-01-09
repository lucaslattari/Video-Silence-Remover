# -*- coding: utf-8 -*-
import os
import sys
import time
from configparser import ConfigParser
from tkinter import filedialog, Tk

CONFIG_FILE_NAME = 'settings.ini'
CONFIG_IMAGEMAGICK_FILE = 'imagemagick_file_name'

def _open_dialog_file():
	"""Abre uma janela de diálogo para selecionar o magick.exe no diretório do ImageMagick

		retorno: o caminho do arquivo
	"""

	file_types = [('Arquivo executável', '*.exe')]
	file_name = None
	title = 'Selecione o arquivo executável do ImageMagick (magick.exe)'

	root = Tk()
	root.withdraw()
	root.filename = filedialog.askopenfilename(initialdir = os.getcwd(), title = title, filetypes = file_types)
	file_name = root.filename
	root.destroy()

	return file_name


def _create_file(file_name):
	"""Cria um arquivo de configuração (config.ini) e armazena o caminho do magick.exe nele

		file_name: caminho do magick.exe
	"""
	print(f"_create_file({file_name})")
	config = ConfigParser()
	config['DEFAULT'] = { CONFIG_IMAGEMAGICK_FILE: file_name }

	with open(CONFIG_FILE_NAME, 'w') as f:
		config.write(f)

def _read_file():
	"""Lê o arquivo de configuração (config.ini)

		retorno: o caminho do magick.exe
	"""
	config = ConfigParser()
	config.read(CONFIG_FILE_NAME)
	return config['DEFAULT'].get(CONFIG_IMAGEMAGICK_FILE)


def get_image_magick_executable():
	"""Retorna o caminho do magick.exe definido no settings.ini. Se settings.init não estiver definido então pergunta o caminho e abre uma janela de diálogo e então grava esse caminho no settings.ini.

		Mata o programa se nada for selecionado na janela de diálogo

		retorno: o caminho do magick.exe
	"""
	if os.path.exists(CONFIG_FILE_NAME):
		im_filename = _read_file()
	else:
		print('Selecione o executável do ImageMagick na pasta em que você o instalou:')
		time.sleep(1)

		im_filename = _open_dialog_file()
		if im_filename:
			_create_file(im_filename)
		else:
			print('Nenhum arquivo selecionado')
			sys.exit(1)

	return im_filename
