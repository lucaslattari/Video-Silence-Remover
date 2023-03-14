# -*- coding: utf-8 -*-
import logging
from colorama import init, Fore, Back, Style
from tqdm import tqdm
from pydub.utils import *
from pydub import AudioSegment
from moviepy.editor import VideoFileClip
from moviepy.editor import *
import os
import os.path
import sys
import shutil
import glob
from argparse import ArgumentParser
from moviepy import config_defaults
from load_im import get_image_magick_executable

# define o caminho do imagemagick em runtime antes de importar o moviepy
config_defaults.IMAGEMAGICK_BINARY = get_image_magick_executable()


def load_audio(video_filename):
    file_extension = video_filename.split(".")
    return AudioSegment.from_file(video_filename, file_extension[1])


def load_video(video_filename):
    return VideoFileClip(video_filename)


def split_audio(audio_file, chunk_size=200.0):
    return make_chunks(audio_file, chunk_size)


def create_clip(video_file, filename, start_time, end_time, is_debug_mode=False):
    silence_clip = video_file.subclip(start_time, end_time)

    text_clip = create_label(filename)
    composite_clip = CompositeVideoClip(
        [silence_clip, text_clip]).set_duration(end_time - start_time)

    if is_debug_mode and not os.path.exists(filename):
        composite_clip.write_videofile(filename, logger=None)

    return composite_clip


def create_label(filename):
    return TextClip(filename, fontsize=80)


def save_merged_clips(filename, list_of_clips):
    if (not os.path.exists(filename)):
        concatenated_silence_clips = concatenate_videoclips(list_of_clips)
        concatenated_silence_clips.write_videofile(filename, logger=None)
        concatenated_silence_clips.close()


def write_silences(list_of_silences):
    with open("silence_to_remove.txt", "w") as f:
        for each_silence in list_of_silences:
            line = ",".join(str(x) for x in each_silence) + "\n"
            f.write(line)


def identify_silence_clips(video_filename, rms_of_silence, time_of_silence_in_seconds, is_debug_mode=False,
                           chunk_size=200.0):
    audio_file = load_audio(video_filename)   # Carrega o arquivo de áudio
    video_file = load_video(video_filename)   # Carrega o arquivo de vídeo
    # Divide o arquivo de áudio em pedaços de tamanho 'chunk_size'
    audio_chunks = split_audio(audio_file, chunk_size)

    # Variável que indica se um trecho de silêncio está sendo detectado
    is_silence_detected = False
    elapsed_time = 0.0   # Variável para armazenar o tempo decorrido
    silence_file_id = 0   # ID do arquivo que contém o trecho de silêncio específico

    # Lista que armazenará os trechos de silêncio que formarão um único vídeo
    list_of_combined_clips = []
    # Lista que armazenará informações sobre cada trecho de silêncio detectado
    list_of_silences = []
    print(Fore.GREEN + "Searching for periods of silence." + Style.RESET_ALL)

    # Itera sobre cada pedaço de áudio
    for chunk_index, chunk in enumerate(tqdm(audio_chunks)):
        logging.info(f"{chunk_index} {chunk.rms} {rms_of_silence}")

        # Detectou um pedaço inicial de silêncio?
        if (chunk.rms < rms_of_silence and not is_silence_detected):
            logging.info(f"Começou o silêncio em {elapsed_time}")

            start_silence_time = elapsed_time  # Armazena início de trecho de silêncio
            is_silence_detected = True   # Define estado em que um trecho de silêncio foi detectado

        elif (chunk.rms > rms_of_silence  # Som do trecho ultrapassou o limiar de silêncio?
              and is_silence_detected  # Ainda estamos num silêncio?
              and start_silence_time < elapsed_time - time_of_silence_in_seconds):  # Tem um tamanho mínimo de silêncio?
            # Acabou o silêncio

            end_silence_time = elapsed_time

            logging.info(f"Acabou o silêncio em {end_silence_time}")

            # Cria um trecho de vídeo que corresponde ao trecho de silêncio
            silence_filename = "silence" + str(silence_file_id) + ".mp4"
            composite_clip = create_clip(
                video_file, silence_filename, start_silence_time, end_silence_time, is_debug_mode)
            # Adiciona o trecho de vídeo na lista de trechos combinados
            list_of_combined_clips.append(composite_clip)

            # Define que não há mais trecho de silêncio sendo detectado
            is_silence_detected = False
            silence_file_id += 1   # Incrementa o ID do arquivo de silêncio

            # Adiciona informações do trecho de silêncio na lista de silêncios detectados
            list_of_silences.append(
                (silence_file_id, start_silence_time, end_silence_time))
        elif (chunk.rms > rms_of_silence and is_silence_detected):
            # achou um chunk de exatamente x segundos, sendo x o tamanho do chunk. nesse caso ignora
            is_silence_detected = False
            logging.info(f"Acabou o silêncio em {elapsed_time}")

        elif (chunk_index == len(audio_chunks) - 1 and is_silence_detected):
            # "Força" a cair no último trecho se estiver no estado de silêncio
            logging.info(
                f"Acabou o silêncio em {elapsed_time} (Último trecho)")

            end_silence_time = elapsed_time
            # Define o nome do arquivo do trecho de silêncio
            silence_filename = "silence" + str(silence_file_id) + ".mp4"
            composite_clip = create_clip(
                video_file, silence_filename, start_silence_time, end_silence_time, is_debug_mode)

            list_of_combined_clips.append(composite_clip)

            logging.info(
                f"É silêncio: {start_silence_time} até {end_silence_time}")

            # Lista de silêncio, a ser usada para salvar num arquivo para consulta a posteriori
            list_of_silences.append(
                (silence_file_id, start_silence_time, end_silence_time))
        elif (is_silence_detected == True):
            # fins de debug
            pass

        # Incrementa o tempo decorrido
        elapsed_time += round(chunk_size / 1000.0, 2)

    # Salva o arquivo de vídeo contendo todos os trechos de silêncio removidos (usado no modo debug)
    if (is_debug_mode):
        logging.info(
            f"Gerando um arquivo de silêncio chamado silence.mp4")
        save_merged_clips("silence.mp4", list_of_combined_clips)

    # Salva informações dos trechos de silêncio detectados num arquivo de texto
    write_silences(list_of_silences)

    # Fecha o arquivo de vídeo
    video_file.close()


def remove_silence_intervals(video_filename, txt_file, debug=True):
    silence_to_remove_file = open(txt_file, "r")
    video_file = VideoFileClip(video_filename)

    print(Fore.GREEN + "Trimming intervals of silence..." + Style.RESET_ALL)
    first_iteration = True
    combined_clips = []
    i = 0
    start_time = 0.0
    end_time = 0.0
    for line in list(silence_to_remove_file):
        if line[0] == "#":
            continue

        file, start_time, end_time = line.rstrip().split(",")
        start_time = float(start_time)
        end_time = float(end_time)

        if (start_time == 0.0 and first_iteration == True):
            first_iteration = False
            last_end_time = end_time
        elif (first_iteration == True):
            clip = video_file.subclip(0, start_time)
            combined_clips.append(clip)
            if debug:
                filename = "clip" + str(i) + ".mp4"
                clip.write_videofile(filename)
            last_end_time = end_time
            first_iteration = False
        else:
            clip = video_file.subclip(last_end_time, start_time)
            combined_clips.append(clip)
            if debug:
                filename = "clip" + str(i) + ".mp4"
                clip.write_videofile(filename)
            last_end_time = end_time
        i += 1

    # add the end
    clip = video_file.subclip(end_time, float(video_file.duration))
    combined_clips.append(clip)
    if debug:
        filename = "clip" + str(i) + ".mp4"
        clip.write_videofile(filename)

    final_video_clips = concatenate_videoclips(combined_clips)
    final_video_clips.write_videofile("final.mp4")
    final_video_clips.close()

    video_file.close()
    silence_to_remove_file.close()


def delete_temp_files():
    for file in os.listdir(os.getcwd()):
        if file.endswith("silenceToRemove.txt"):
            os.remove(file)
        if file.endswith("silenceToRemoveCOPY.txt"):
            os.remove(file)
        if file.endswith(".log"):
            os.remove(file)
        if file.endswith(".mp3"):
            os.remove(file)
        if file.endswith(".mp4"):
            if "clip" in file:
                os.remove(file)
            if "silence" in file:
                os.remove(file)


def parse_args():
    parser = ArgumentParser(description='Remove all sections with silence')
    parser.add_argument('file', help='Video file path')
    parser.add_argument('-r', action='store', dest='rms_of_silence', type=int, default=100, required=False,
                        help='Threshold that marks the measure of silence')
    parser.add_argument('-t', action='store', dest='time_of_silence_in_seconds', type=float, default=0.5, required=False,
                        help='Minimum silence time in seconds')
    parser.add_argument('--d', action='store_true',
                        dest='is_debug_mode', required=False, help='Debug mode')

    return parser.parse_args()


def init():
    delete_temp_files()
    print(Fore.RED + "Temporary files deleted." + Style.RESET_ALL)

    logging.basicConfig(filename='debug.log', level=logging.DEBUG)


def main():
    init()

    args = parse_args()

    if not os.path.exists(args.file):
        print(f'{args.file} not found')
        return

    identify_silence_clips(args.file, args.rms_of_silence,
                           args.time_of_silence_in_seconds, is_debug_mode=args.is_debug_mode)

    # essa função abaixo clipa o vídeo original passado por parâmetro de acordo com a informação de silêncio no arquivo de log
    remove_silence_intervals(
        args.file, "silence_to_remove.txt", debug=args.is_debug_mode)

    logging.shutdown()


if __name__ == "__main__":
    main()
