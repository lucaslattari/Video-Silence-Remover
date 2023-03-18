from colorama import Fore, Style
import os

from moviepy.editor import (
    VideoFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
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


def save_merged_clips(filename, list_of_clips):
    try:
        concatenated_silence_clips = concatenate_videoclips(list_of_clips)
        concatenated_silence_clips.write_videofile(filename)
    except Exception as e:
        print(f'Error saving video file: {e}')
    else:
        concatenated_silence_clips.close()


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
