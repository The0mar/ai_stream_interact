import os
import tempfile
import subprocess

from pydub.utils import get_player_name
from ai_stream_interact.tts.printout_utils import supress_printouts


class TextToSpeechBase:
    """Base class for TextToSpeech models or frameworks.

    Child classes should implement the two methods:
    - `_model_init`:
        This should implement the code for initializing the model.
    - `_run`:
        This shoud implement the code for running text to speech using the `self._tts` object.

    Example implementation for Coqui AI models:

    ```
    from TTS.api import TTS
    from ai_stream_interact.tts.tts_base import TextToSpeechBase

    class TextToSpeechCoqui(TextToSpeechBase):
        def __init__(self, model_name):
            self._model_name = model_name

        def _model_init(self):
            return TTS(model_name=self._model_name)

        def _run(self, text, file_name):
            tts = self._tts
            return tts.tts_to_file(text=text, file_name=file_name)
    ```
    """
    def __init__(self):
        self._tts = self.model_init()

    def _model_init(self):
        """Implement this for specific model/tts framework"""
        raise NotImplementedError()

    def _run(self):
        """Implement this for specific model/tts framework"""
        raise NotImplementedError()

    def model_init(self):
        with supress_printouts():
            return self._model_init()

    def run(self, text, tts_from="file"):
        if not self._tts:
            raise Exception("Please run TextToSpeechBase.model_init() first before running TextToSpeechBase.run()")
        if tts_from == "file":
            with tempfile.TemporaryDirectory() as tmp:
                file_name = os.path.join(tmp, "output.wav")
                self._run(text, file_name)
                self._play_with_ffplay(file_name)

    def _play_with_ffplay(self, file_name):
        PLAYER = get_player_name()

        devnull = open(os.devnull, 'w')
        subprocess.call(
            [PLAYER, "-nodisp", "-autoexit", file_name],
            stdout=devnull,
            stderr=devnull
        )
