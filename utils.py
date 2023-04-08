import subprocess
import os
from colorama import Fore, Style
from moviepy import config_defaults
from load_im import get_image_magick_executable

# Set ImageMagick path at runtime before importing moviepy
config_defaults.IMAGEMAGICK_BINARY = get_image_magick_executable()


def delete_temp_files():
    for filename in os.listdir(os.getcwd()):
        # Delete silence_to_remove.txt file
        if filename.endswith('silence_to_remove.txt'):
            os.remove(filename)

        # Delete log files
        if filename.endswith('.log'):
            os.remove(filename)

        # Delete mp3 files
        if filename.endswith('.mp3'):
            os.remove(filename)

        # Delete video files
        if filename.endswith('.mp4'):
            if 'clip' in filename:
                os.remove(filename)  # Delete clip files
            elif 'silence' in filename:
                os.remove(filename)  # Delete silence files

    print(Fore.RED + 'Temporary files deleted.' + Style.RESET_ALL)


def check_ffmpeg_installed():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False
