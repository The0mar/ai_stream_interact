from llm_stream_interact.llm_interact_base import InteractionFramesConfig
from llm_stream_interact.google.gemini_stream_interact import GeminiStreamInteract


def main():
    interaction_frames_config = InteractionFramesConfig(nframes_interact=3, frame_capture_interval=0.4)

    gemini = GeminiStreamInteract(interaction_frames_config=interaction_frames_config)
    gemini.start()


if __name__ == '__main__':
    main()
