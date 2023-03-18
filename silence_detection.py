from colorama import Fore, Style
from tqdm import tqdm
import logging

from audio_processing import (
    load_audio,
    split_audio
)
from video_processing import (
    load_video,
    create_composite_clip,
    create_video_clips
)


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


def write_silences(list_of_silences):
    with open('silence_to_remove.txt', 'w') as f:
        for each_silence in list_of_silences:
            line = ','.join(str(x) for x in each_silence) + '\n'
            f.write(line)
