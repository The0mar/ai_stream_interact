import argparse
import importlib

from ai_stream_interact.base.ai_interact_base import InteractionFramesConfig


def main():
    parser = argparse.ArgumentParser("AI Stream Interact")
    parser.add_argument(
        "--llm",
        type=str,
        required=True,
        help="LLM to use, this should match the LLM name in ai_stream_interact/models"
    )
    parser.add_argument(
        "--tts-model-name",
        type=str,
        help="Name of tts model to use. Use tts --list_models to see available models."
    )

    args = parser.parse_args()

    interaction_frames_config = InteractionFramesConfig(nframes_interact=3, frame_capture_interval=0.4)

    if args.tts_model_name:
        if args.tts_model_name.lower() == "default":
            tts_model_name = "tts_models/en/ljspeech/glow-tts"
        else:
            tts_model_name = args.tts_model_name
    else:
        tts_model_name = None

    Interact = importlib.import_module(f"ai_stream_interact.models.{args.llm}").ModelInteract

    llm_interact = Interact(
        interaction_frames_config=interaction_frames_config,
        tts_model_name=tts_model_name
    )
    llm_interact.start()


if __name__ == '__main__':
    main()
