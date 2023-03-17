# -*- coding: utf-8 -*-
import logging
import os
from colorama import Fore, Style
from tqdm import tqdm
from argparse import ArgumentParser
from pydub.utils import make_chunks
from pydub import AudioSegment
from moviepy.editor import (
    VideoFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
)
from moviepy import config_defaults
from load_im import get_image_magick_executable

# Set ImageMagick path at runtime before importing moviepy
config_defaults.IMAGEMAGICK_BINARY = get_image_magick_executable()


def load_audio(filename):
    file_extension = filename.split('.')
    return AudioSegment.from_file(filename, file_extension[1])


def load_video(filename):
    try:
        video_file = VideoFileClip(filename)
    except FileNotFoundError:
        print(f'{Fore.RED} Error: {filename} not found. {Style.RESET_ALL}')
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


def detect_silence_audio_chunk(
    chunk,
    elapsed_time,
    threshold_of_silence,
    time_of_silence_in_seconds,
    is_silence_detected,
    start_silence_time
):
    if chunk.rms < threshold_of_silence and not is_silence_detected:
        logging.info(f'Found a chunk of silence!')
        logging.info(f'Level of sound: {chunk.rms} : {threshold_of_silence}')
        logging.info(f'Is silence detected? True')
        logging.info(f'start time: {elapsed_time} , end time: {None}')

        return elapsed_time, None, True
    elif (  # the silence chunk is over
        chunk.rms > threshold_of_silence
        and is_silence_detected
        # and start_silence_time <= elapsed_time - time_of_silence_in_seconds
    ):
        logging.info(f'Chunk of silence ended!')
        logging.info(f'Level of sound: {chunk.rms} : {threshold_of_silence}')
        logging.info(f'Is silence detected? False')
        logging.info(
            f'start time: {start_silence_time} , end time: {elapsed_time}')

        return start_silence_time, elapsed_time, False
    else:  # no changes
        logging.info(f'No changes.')
        logging.info(f'Level of sound: {chunk.rms} : {threshold_of_silence}')
        logging.info(f'Is silence detected? {is_silence_detected}')
        logging.info(f'start time: {start_silence_time} , end time: {None}')

        return start_silence_time, None, is_silence_detected


def compute_silence_chunk(
    is_silence_detected,
    start_silence_time,
    end_silence_time,
    video_file,
    silence_file_id,
    is_debug_mode,
    list_of_silence_clips,
    list_of_silences,
):
    if not is_silence_detected:  # there is no silence chunk being processed right now
        logging.info(f'Generating silence{silence_file_id}.mp4')
        silence_filename = f'silence{silence_file_id}.mp4'
        clip = create_composite_clip(
            video_file,
            silence_filename,
            start_silence_time,
            end_silence_time,
            is_debug_mode,
        )
        list_of_silence_clips.append(clip)
        list_of_silences.append((start_silence_time, end_silence_time))
        silence_file_id += 1

    return silence_file_id, list_of_silence_clips, list_of_silences


def identify_silence_clips(
    video_filename,
    threshold_of_silence,
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
    start_silence_time = None

    list_of_silence_clips = []
    list_of_silences = []
    print(f'{Fore.GREEN}Searching for periods of silence.{Style.RESET_ALL}')

    for chunk_index, chunk in enumerate(tqdm(audio_chunks)):
        logging.info(f'{chunk_index} {chunk.rms} {threshold_of_silence}')

        start_silence_time, end_silence_time, is_silence_detected = detect_silence_audio_chunk(
            chunk, elapsed_time, threshold_of_silence, time_of_silence_in_seconds, is_silence_detected, start_silence_time
        )
        # don't enter (1)if a silence block is still being computed or (2)no silence block is being processed now
        if end_silence_time is not None:
            silence_file_id, list_of_silence_clips, list_of_silences = compute_silence_chunk(
                is_silence_detected,
                start_silence_time,
                end_silence_time,
                video_file,
                silence_file_id,
                is_debug_mode,
                list_of_silence_clips,
                list_of_silences,
            )

        # Update elapsed time
        elapsed_time += round(chunk_size / 1000.0, 2)

    if is_debug_mode:
        logging.info(f'Generating a silence file called silence.mp4')
        # generate a file with all silence clips
        save_merged_clips('silence.mp4', list_of_silence_clips)

    video_file.close()

    # Saves information of detected silence snippets in a text file
    write_silences(list_of_silences)

    return list_of_silence_clips


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

    print(f'{Fore.GREEN} Trimming intervals of silence... {Style.RESET_ALL}')
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
        default=1.0,
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
