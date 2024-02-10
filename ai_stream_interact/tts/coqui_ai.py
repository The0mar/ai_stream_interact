import os
import queue
import tempfile
import subprocess

import torch
from TTS.api import TTS

from ai_stream_interact.tts.printout_utils import supress_printouts


def _play_sound_w_ffmpeg(file_path: str) -> None:
    """Plays a file using ffmpeg. Requires ffmpeg to be installed."""
    devnull = open(os.devnull, "w")
    subprocess.run(
        ["ffplay", "-nodisp", "-autoexit", file_path],
        stdout=devnull,
        stderr=devnull,
        shell=False
    )


class TextToSpeechCoqui:
    """TTS using Coqui AI"""

    def __init__(self, model_name: str) -> None:
        """For a list of available model names use tts --list_models"""
        device = "cuda" if torch.cuda.is_available() else "cpu"
        with supress_printouts():
            self._tts = TTS(model_name).to(device)

    def tts_from_queue(self, queue: queue.Queue) -> None:
        """Runs self.tts_from_str on a queue of incoming stream of texts."""
        while True:
            text = queue.get()
            with tempfile.TemporaryDirectory() as tmp:
                file_path = os.path.join(tmp, "output.wav")
                self.tts_from_str(text, file_path)

    def tts_from_str(self, text: str, file_path: str) -> None:
        """Converts text to a .wav sound file then plays the file."""
        # TODO the underlying printouts causes some weird behavior (even with supressing) where the user dialogue just freezes. Need to fix this later.
        with supress_printouts():
            self._tts.tts_to_file(text, file_path=file_path)
            _play_sound_w_ffmpeg(file_path)
