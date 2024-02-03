from TTS.api import TTS

from ai_stream_interact.tts.tts_base import TextToSpeechBase


class TextToSpeechCoqui(TextToSpeechBase):

    def __init__(self, model_name):
        self._model_name = model_name
        super().__init__()

    def _model_init(self):
        return TTS(model_name=self._model_name)

    def _run(self, text, file_path):
        tts = self._tts
        tts.tts_to_file(text=text, file_path=file_path)
