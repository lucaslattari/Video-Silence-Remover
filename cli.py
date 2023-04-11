from argparse import ArgumentParser


def parse_args():
    parser = ArgumentParser(
        description='Remove all silent sections from the video'
    )
    parser.add_argument('file', help='Video file path')
    parser.add_argument(
        '-s',
        action='store',
        dest='silence_sensitivity',
        type=int,
        choices=range(1, 10),
        default=5,
        required=False,
        help=f"Silence sensitivity level from 1 (less aggressive) to 9 (more aggressive), default: %(default)s",
    )
    parser.add_argument(
        '-t',
        action='store',
        dest='time_of_silence_in_seconds',
        type=float,
        default=2.0,
        required=False,
        help=f"Minimum silence time in seconds, default: %(default)s",
    )
    parser.add_argument(
        '--d',
        action='store_true',
        dest='is_debug_mode',
        required=False,
        help='Debug mode',
    )

    return parser.parse_args()
