# -*- coding: utf-8 -*-
import os
import sys
import time
import platform
from configparser import ConfigParser
from tkinter import filedialog, Tk

CONFIG_FILE_NAME = 'settings.ini'
CONFIG_IMAGEMAGICK_FILE = 'imagemagick_file_name'
WINDOWS = 'Windows'


def _open_dialog_file():
    """
    Opens a dialog window to select the magick.exe in the ImageMagick directory.

    Returns:
        str: The path of the file.
    """

    if platform.system() == WINDOWS:
        file_types = [('Arquivo executável', '*.exe')]
        title = 'Selecione o arquivo executável do ImageMagick (magick.exe)'
    else:
        file_types = []
        title = 'Selecione o arquivo executável do ImageMagick (magick)'

    root = Tk()
    root.withdraw()
    root.filename = filedialog.askopenfilename(
        initialdir=os.getcwd(), title=title, filetypes=file_types
    )
    file_name = root.filename
    root.destroy()

    return file_name


def _create_file(file_name):
    """
    Creates a configuration file (defined in the constant CONFIG_FILE_NAME)
    and stores the path of magick.exe in it.

    Args:
        file_name (str): The path of magick.exe.
    """
    config = ConfigParser()
    config['DEFAULT'] = {CONFIG_IMAGEMAGICK_FILE: file_name}

    with open(CONFIG_FILE_NAME, 'w') as f:
        config.write(f)


def _read_file():
    """
    Reads the configuration file (config.ini).

    Returns:
        str: The path of magick.exe.
    """
    config = ConfigParser()
    config.read(CONFIG_FILE_NAME)
    return config['DEFAULT'].get(CONFIG_IMAGEMAGICK_FILE)


def get_image_magick_executable():
    """
    Returns the path of magick.exe from the file defined in the constant
    CONFIG_FILE_NAME. If the file is not defined, it asks for the path and
    opens a dialog window, then saves this path.

    Exits the program if nothing is selected in the dialog window.

    Returns:
        str: The path of magick.exe.
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
