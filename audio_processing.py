from pydub import AudioSegment
from pydub.utils import make_chunks


def load_audio(filename):
    file_extension = filename.split('.')
    return AudioSegment.from_file(filename, file_extension[1])


def split_audio(audio_file, chunk_size=200.0):
    return make_chunks(audio_file, chunk_size)
