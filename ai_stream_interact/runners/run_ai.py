import os
import argparse
from importlib.machinery import SourceFileLoader

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

    # check if running from package endpoint or directly this script
    cwd = os.getcwd()
    if cwd.split("/")[-1] == "ai_stream_interact":
        llm_path = f"ai_stream_interact/models/{args.llm}.py"
    else:
        llm_path = f"../models/{args.llm}.py"

    LLM_MODULE = SourceFileLoader("module.name", llm_path).load_module()

    llm = LLM_MODULE.ModelInteract(
        interaction_frames_config=interaction_frames_config,
        tts_model_name=tts_model_name
    )
    llm.start()


if __name__ == '__main__':
    main()
