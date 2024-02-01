import os
import argparse

from dotenv import load_dotenv
from rich.console import Console

from llm_stream_interact.llm_interact_base import InteractionFramesConfig
from llm_stream_interact.google.gemini_stream_interact import GeminiStreamInteract


def main(args):
    console = Console()
    if args.api_key:
        api_key = args.api_key
    else:
        console.print("No API Key provided, thus looking for API key in .env")
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")

    interaction_frames_config = InteractionFramesConfig(nframes_interact=3, frame_capture_interval=0.4)

    gemini = GeminiStreamInteract(
        api_key=api_key,
        cam_index=args.cam,
        interaction_frames_config=interaction_frames_config,
    )
    gemini.start_video_stream()
    gemini.start_model_listeners()


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Stream Interact with Gemini...")

    parser.add_argument(
        "--cam",
        type=int,
        help="Pass cam index",
        required=True
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Api Key"
    )
    args = parser.parse_args()

    main(args)
