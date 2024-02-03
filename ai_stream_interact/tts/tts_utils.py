from ai_stream_interact.tts.tts_base import TextToSpeechBase
from ai_stream_interact.tts.printout_utils import supress_printouts


def play(tts: TextToSpeechBase, text: str):
    with supress_printouts():
        tts.run(text)
