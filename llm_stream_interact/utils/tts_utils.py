import os
import sys
import tempfile
import subprocess

from TTS.api import TTS

from pydub.utils import get_player_name


class TextToSpeech:
    def __init__(self, model):
        self._model = model
        self._tts = None

    def run(self, text):
        if not self._tts:
            raise Exception("Can't run without initializing model first. Make sure you ran TextToSpeech.init_model()")
        with tempfile.TemporaryFile() as tmp:
            file_name = f"{tmp}.wav"
            self._tts.tts_to_file(text=text, file_path=file_name)
            self._play_with_ffplay(file_name)

    def init_model(self):
        with supress_printouts():
            self._tts = TTS(model_name=self._model)

    def _play_with_ffplay(self, file_name):
        PLAYER = get_player_name()

        devnull = open(os.devnull, 'w')
        subprocess.call(
            [PLAYER, "-nodisp", "-autoexit", file_name],
            stdout=devnull,
            stderr=devnull
        )


class supress_printouts:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


def play(tts: TextToSpeech, text: str):
    with supress_printouts():
        tts.run(text)
