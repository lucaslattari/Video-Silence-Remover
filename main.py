# -*- coding: utf-8 -*-
import logging

import audio_processing
from utils import delete_temp_files
from cli import parse_args
from silence_detection import (
    identify_silence_clips,
    remove_silence_intervals
)


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

    remove_silence_intervals(
        args.file,
        'silence_to_remove.txt',
        is_debug_mode=args.is_debug_mode
    )

    logging.shutdown()


if __name__ == '__main__':
    main()
