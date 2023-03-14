# -*- coding: utf-8 -*-
import logging
import os
import os.path

from colorama import Fore, Style
from tqdm import tqdm
from argparse import ArgumentParser

from pydub.utils import *
from pydub import AudioSegment
from moviepy.editor import *
from moviepy import config_defaults
from load_im import get_image_magick_executable

# define o caminho do imagemagick em runtime antes de importar o moviepy
config_defaults.IMAGEMAGICK_BINARY = get_image_magick_executable()


def load_audio(filename):
    file_extension = filename.split('.')
    return AudioSegment.from_file(filename, file_extension[1])


def load_video(filename):
    try:
        video_file = VideoFileClip(filename)
    except FileNotFoundError:
        print(Fore.RED + f'Error: {filename} not found.' + Style.RESET_ALL)
        return None
    return video_file


def split_audio(audio_file, chunk_size=200.0):
    return make_chunks(audio_file, chunk_size)


def create_clip(
    video_file, clip_filename, start_time, end_time, is_debug_mode=False
):
    """
    Creates a single video clip from specified start and end times.
    """
    try:
        clip = video_file.subclip(start_time, end_time)

        if is_debug_mode and not os.path.exists(clip_filename):
            clip.write_videofile(clip_filename)
    except Exception as e:
        print(f'Error creating clip: {e}')
    else:
        return clip


def create_composite_clip(
    video_file, clip_filename, start_time, end_time, is_debug_mode=False
):
    """
    Creates a composite video clip with a label from specified start and end times.
    """
    try:
        clip = create_clip(
            video_file, clip_filename, start_time, end_time, False
        )
        text_clip = create_label(clip_filename)

        composite_clip = CompositeVideoClip([clip, text_clip]).set_duration(
            end_time - start_time
        )

        if is_debug_mode and not os.path.exists(clip_filename):
            composite_clip.write_videofile(clip_filename)
    except Exception as e:
        print(f'Error creating clip: {e}')
    else:
        return composite_clip


def create_label(filename):
    return TextClip(filename, fontsize=80)


def save_merged_clips(filename, list_of_clips):
    try:
        concatenated_silence_clips = concatenate_videoclips(list_of_clips)
        concatenated_silence_clips.write_videofile(filename)
    except Exception as e:
        print(f'Error saving video file: {e}')
    else:
        concatenated_silence_clips.close()


def write_silences(list_of_silences):
    with open('silence_to_remove.txt', 'w') as f:
        for each_silence in list_of_silences:
            line = ','.join(str(x) for x in each_silence) + '\n'
            f.write(line)


def identify_silence_clips(
    video_filename,
    rms_of_silence,
    time_of_silence_in_seconds,
    is_debug_mode=False,
    chunk_size=200.0,
):
    audio_file = load_audio(video_filename)
    video_file = load_video(video_filename)
    audio_chunks = split_audio(audio_file, chunk_size)

    is_silence_detected = False
    elapsed_time = 0.0
    silence_file_id = 0

    list_of_combined_clips = []
    list_of_silences = []
    print(Fore.GREEN + 'Searching for periods of silence.' + Style.RESET_ALL)

    # Itera sobre cada pedaço de áudio
    for chunk_index, chunk in enumerate(tqdm(audio_chunks)):
        logging.info(f'{chunk_index} {chunk.rms} {rms_of_silence}')

        # Detectou um pedaço inicial de silêncio?
        if chunk.rms < rms_of_silence and not is_silence_detected:
            logging.info(f'Começou o silêncio em {elapsed_time}')

            start_silence_time = elapsed_time
            is_silence_detected = True

        # Acabou o silêncio
        elif (
            chunk.rms > rms_of_silence
            and is_silence_detected
            and start_silence_time < elapsed_time - time_of_silence_in_seconds
        ):
            end_silence_time = elapsed_time
            logging.info(f'Acabou o silêncio em {end_silence_time}')

            # Cria um trecho de vídeo que corresponde ao trecho de silêncio
            silence_filename = 'silence' + str(silence_file_id) + '.mp4'
            clip = create_composite_clip(
                video_file,
                silence_filename,
                start_silence_time,
                end_silence_time,
                is_debug_mode,
            )

            list_of_combined_clips.append(clip)

            is_silence_detected = False
            silence_file_id += 1

            list_of_silences.append((start_silence_time, end_silence_time))
        # achou um chunk de exatamente x segundos, sendo x o tamanho do chunk. nesse caso ignora
        elif chunk.rms > rms_of_silence and is_silence_detected:
            is_silence_detected = False
            logging.info(f'Acabou o silêncio em {elapsed_time}')

        # "Força" a cair no último trecho se estiver no estado de silêncio
        elif chunk_index == len(audio_chunks) - 1 and is_silence_detected:
            end_silence_time = elapsed_time
            logging.info(
                f'Acabou o silêncio em {end_silence_time} (Último trecho)'
            )

            silence_filename = 'silence' + str(silence_file_id) + '.mp4'
            clip = create_composite_clip(
                video_file,
                silence_filename,
                start_silence_time,
                end_silence_time,
                is_debug_mode,
            )

            list_of_combined_clips.append(clip)

            logging.info(
                f'É silêncio: {start_silence_time} até {end_silence_time}'
            )

            # Lista de silêncio, a ser usada para salvar num arquivo para consulta a posteriori
            list_of_silences.append((start_silence_time, end_silence_time))
        elif is_silence_detected == True:
            # fins de debug
            pass

        # Incrementa o tempo decorrido
        elapsed_time += round(chunk_size / 1000.0, 2)

    # Salva o arquivo de vídeo contendo todos os trechos de silêncio removidos (usado no modo debug)
    if is_debug_mode:
        logging.info(f'Gerando um arquivo de silêncio chamado silence.mp4')
        save_merged_clips('silence.mp4', list_of_combined_clips)

    # Salva informações dos trechos de silêncio detectados num arquivo de texto
    write_silences(list_of_silences)

    # Fecha o arquivo de vídeo
    video_file.close()


def parse_silence_file(txt_file):
    try:
        with open(txt_file, 'r') as silence_to_remove_file:
            silence_lines = [
                line for line in silence_to_remove_file if line[0] != '#'
            ]
            intervals = [
                tuple(map(float, line.rstrip().split(',')))
                for line in silence_lines
            ]
    except FileNotFoundError:
        print(f'Error: {txt_file} not found')
        return None
    return intervals


def create_video_clips(video_file, intervals, is_debug_mode):
    """
    Creates video clips from specified intervals and saves into a single file.
    """
    clips = []
    last_end_time = 0.0

    for clip_id, (start_time, end_time) in enumerate(intervals):
        if start_time == 0.0 and not clips:
            last_end_time = end_time
        else:
            clip_filename = f'clip{clip_id - 1}.mp4'
            clip = create_clip(
                video_file,
                clip_filename,
                last_end_time,
                start_time,
                is_debug_mode,
            )

            clips.append(clip)
            last_end_time = end_time

    clip = create_clip(
        video_file,
        f'clip{clip_id}.mp4',
        last_end_time,
        video_file.duration,
        is_debug_mode,
    )
    clips.append(clip)

    save_merged_clips('final.mp4', clips)


def remove_silence_intervals(video_filename, txt_file, is_debug_mode=False):
    video_file = load_video(video_filename)
    if not video_file:
        return

    intervals = parse_silence_file(txt_file)
    if not intervals:
        return

    print(Fore.GREEN + 'Trimming intervals of silence...' + Style.RESET_ALL)
    create_video_clips(video_file, intervals, is_debug_mode)

    video_file.close()


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


def parse_args():
    parser = ArgumentParser(
        description='Remove all silent sections from the video'
    )
    parser.add_argument('file', help='Video file path')
    parser.add_argument(
        '-r',
        action='store',
        dest='rms_of_silence',
        type=int,
        default=100,
        required=False,
        help='Minimum volume level to consider as silence',
    )
    parser.add_argument(
        '-t',
        action='store',
        dest='time_of_silence_in_seconds',
        type=float,
        default=0.5,
        required=False,
        help='Minimum silence time in seconds',
    )
    parser.add_argument(
        '--d',
        action='store_true',
        dest='is_debug_mode',
        required=False,
        help='Debug mode',
    )

    return parser.parse_args()


def main():
    delete_temp_files()
    logging.basicConfig(filename='debug.log', level=logging.DEBUG)

    args = parse_args()
    try:
        with open(args.file):
            pass
    except FileNotFoundError:
        print(f'{args.file} not found')
        return

    identify_silence_clips(
        args.file,
        args.rms_of_silence,
        args.time_of_silence_in_seconds,
        is_debug_mode=args.is_debug_mode,
    )

    # essa função abaixo clipa o vídeo original passado por parâmetro de acordo com a informação de silêncio no arquivo de log
    remove_silence_intervals(
        args.file, 'silence_to_remove.txt', is_debug_mode=args.is_debug_mode
    )

    logging.shutdown()


if __name__ == '__main__':
    main()
