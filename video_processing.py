from colorama import Fore, Style
import subprocess
import tempfile
import os

from moviepy.editor import (
    VideoFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
)

from utils import (
    check_ffmpeg_installed
)


def load_video(filename):
    try:
        video_file = VideoFileClip(filename)
    except FileNotFoundError:
        print(f'{Fore.RED} Error: {filename} not found. {Style.RESET_ALL}')
        return None
    return video_file


def create_clip(video_file, clip_filename, start_time, end_time, is_debug_mode=False):
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


def create_composite_clip(video_file, clip_filename, start_time, end_time, is_debug_mode=False):
    """
    Creates a composite video clip with a label from specified start and end times.
    """
    try:
        clip = create_clip(video_file, clip_filename,
                           start_time, end_time, False)
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


def merge_video_files(filenames):
    video_clips = []

    for filename in filenames:
        clip = VideoFileClip(filename)
        video_clips.append(clip)

    return video_clips


def save_merged_clips(filename, list_of_clips):
    try:
        concatenated_silence_clips = concatenate_videoclips(list_of_clips)
        del (list_of_clips)
        concatenated_silence_clips.write_videofile(filename)
    except Exception as e:
        print(f'Error saving video file: {e}')
    else:
        concatenated_silence_clips.close()


def create_video_clips(video_file, intervals, is_debug_mode=False):
    """
    Creates video clips from specified intervals and saves into a single file.
    """
    clips = []
    last_end_time = 0.0

    percentage = 0.10
    for clip_id, (start_time, end_time) in enumerate(intervals):

        if clip_id > int(percentage * len(intervals)):
            print(f'{int(percentage * 100.0)}% concluded...')
            percentage += 0.10

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

    save_merged_clips('output.mp4', clips)


def convert_output_video(input_video, output_video):
    # Used to convert to DaVinci Resolve and others video editors
    if not check_ffmpeg_installed():
        print("Error: FFmpeg not found. Please install FFmpeg to use this function.")
        return

    extension = output_video[output_video.rfind('.'):]

    # Create a temporary file for the converted video
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_file = tempfile.NamedTemporaryFile(
        delete=False, suffix=extension, dir=script_dir)
    temp_file.close()

    if format == '.mov':
        command = [
            "ffmpeg", "-y", "-i", input_video,
            "-c:v", "prores", "-profile:v", "3",
            "-c:a", "pcm_s16le",
            temp_file.name
        ]
    else:
        command = [
            "ffmpeg", "-y", "-i", input_video,
            "-c:v", "libx264", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            temp_file.name
        ]

    try:
        subprocess.run(command, check=True)
        print(
            f"Conversion successful. Temporary output file: {temp_file.name}")

        # Delete the original input video
        os.remove(input_video)

        # Rename the temporary file to the original input video name
        os.rename(temp_file.name, input_video)

        print(f"Input video '{input_video}' overwritten successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")

        # Clean up the temporary file in case of an error
        os.remove(temp_file.name)
