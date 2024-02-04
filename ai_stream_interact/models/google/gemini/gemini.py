from ai_stream_interact.ai_interact_base import InteractionFramesConfig
from ai_stream_interact.models.google.gemini.interactions import GeminiStreamInteract
from ai_stream_interact.tts.coqui_ai import TextToSpeechCoqui


def main():
    interaction_frames_config = InteractionFramesConfig(nframes_interact=3, frame_capture_interval=0.4)

    # coqui_tts_model_name = "tts_models/en/jenny/jenny"
    # coqui_tts_model_name = "tts_models/en/ljspeech/glow-tts"
    # coqui_tts_model_name = "tts_models/en/ljspeech/tacotron2-DCA"
    # tts_model = TextToSpeechCoqui(coqui_tts_model_name)
    gemini = GeminiStreamInteract(
        interaction_frames_config=interaction_frames_config,
        tts_instance=None
    )
    gemini.start()


if __name__ == '__main__':
    main()
