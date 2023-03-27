# -*- coding: utf-8 -*-
import os
import sys
import time
import platform
from configparser import ConfigParser
from tkinter import filedialog, Tk


DEFAULT_CONFIG_FILE = 'settings.ini'
DEFAULT_MAGICK_EXECUTABLE = 'magick.exe'
WINDOWS_PLATFORM = 'Windows'


def open_dialog_file():
    """
    Opens a dialog window to select the magick executable in the ImageMagick directory.

    Returns:
        str: The path of the file, or None if no file was selected.
    """

    if platform.system() == WINDOWS_PLATFORM:
        file_types = [('Executable file', '*.exe')]
        title = f'Select the ImageMagick executable file "{DEFAULT_MAGICK_EXECUTABLE}"'
    else:
        file_types = []
        title = f'Select the ImageMagick executable file "imagemagick"'

    root = Tk()
    root.withdraw()
    root.filename = filedialog.askopenfilename(
        initialdir=os.getcwd(), title=title, filetypes=file_types
    )
    file_name = root.filename
    root.destroy()

    return file_name


def create_config_file(file_name, config_file=DEFAULT_CONFIG_FILE):
    """
    Create a configuration file and store the path of magick.exe in it.

    Args:
        file_name (str): The path of magick.exe.
        config_file (str): The name of the configuration file. Default is 'settings.ini'.
    """
    config = ConfigParser()
    config['DEFAULT'] = {'imagemagick_executable_path': file_name}

    try:
        with open(config_file, 'w') as f:
            config.write(f)
    except IOError:
        print(f'Error: Unable to create configuration file {config_file}.')
        sys.exit(1)


def read_config_file(config_file_name=DEFAULT_CONFIG_FILE):
    """
    Reads the configuration file containing the path to the ImageMagick executable.

    Args:
        config_file_name (str): The name of the configuration file. Default is 'settings.ini'.

    Returns:
        str: The path of the ImageMagick executable.
    """

    config = ConfigParser()

    try:
        with open(config_file_name, 'r') as f:
            config.read_file(f)
            return config['DEFAULT'].get('imagemagick_executable_path')
    except FileNotFoundError:
        print(f'Configuration file not found: {config_file_name}')
        sys.exit(1)
    except KeyError:
        print(f'Configuration file is missing required value: imagemagick_executable_path')
        sys.exit(1)


def get_image_magick_executable(config_file=DEFAULT_CONFIG_FILE):
    """
    Returns the path of magick.exe from the configuration file. If the file is not defined, it asks for the path and
    opens a dialog window, then saves this path.

    Exits the program if nothing is selected in the dialog window.

    Args:
        config_file (str): The name of the configuration file. Default is 'settings.ini'.

    Returns:
        str: The path of magick.exe.
    """
    # Check if the configuration file exists
    if os.path.exists(config_file):
        # Read the path of magick.exe from the configuration file
        im_filename = read_config_file(config_file)
    else:
        # Prompt the user to select the path of magick.exe
        print(
            f'Please select the path of the ImageMagick executable (Default path: C:/Program Files/ImageMagick-7.0.10-Q16/{DEFAULT_MAGICK_EXECUTABLE}):')
        time.sleep(1)

        # Open a dialog window to select the file
        im_filename = open_dialog_file()
        if im_filename:
            # If a file was selected, save the path to the configuration file
            create_config_file(im_filename, config_file)
        else:
            # If no file was selected, exit the program
            print('No file selected.')
            sys.exit(1)

    return im_filename
