from argparse import ArgumentParser


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
