import os
import re
import time
import inspect
from types import GeneratorType
from dataclasses import dataclass

from pynput import keyboard
from rich import print
from rich.panel import Panel
from rich.prompt import Prompt
from rich.console import Console
from rich.markdown import Markdown
from dotenv import load_dotenv

from llm_stream_interact.streamer import Streamer
from llm_stream_interact.utils import img_utils, tts_utils


# DEFAULT_TTS_MODEL = "tts_models/en/ljspeech/tacotron2-DCA"
# DEFAULT_TTS_MODEL = "tts_models/en/jenny/jenny"


@dataclass
class InteractionFramesConfig:
    nframes_interact: str  # number of video frames to use for llm interaction
    frame_capture_interval: float  # n seconds to sleep between capturing frames


def interact_on_key(key):
    def on_key_press(func):
        def wrapper(self, key_pressed):
            """on_press_function"""
            if hasattr(key_pressed, 'char') and key_pressed.char == (key):
                func(self)
        return wrapper
    return on_key_press


class LLMStreamInteractBase:

    def __init__(
        self,
        interaction_frames_config: InteractionFramesConfig,
        tts_model: str = DEFAULT_TTS_MODEL
    ):
        self.console = Console()
        self._interaction_frames_config = interaction_frames_config
        self._key_listeners = []
        self._api_key_dot_env_name = ""
        self._tts = self._init_tts(tts_model)

    def start(self):
        self._entry_point_interact()
        self._get_api_key()
        self._llm_auth(self.__api_key)
        self.streamer, self._cam_index = self._init_streamer()
        self._choose_mode()

    def _process_llm_outputs(self, output):
        if isinstance(output, GeneratorType):
            for out in output:
                self.console.print(out, style="bold #6edb9d")
                tts_utils.play(tts=self._tts, text=out)
        elif isinstance(output, str):
            self.console.print(output, style="bold #6edb9d")
        else:
            raise Exception("Invalid return type from self._llm_interactive_mode(prompt). Expected either types.Generator or str type.")

    @interact_on_key("d")
    def llm_detect_object_mode(self):
        images = self._get_prompt_imgs_from_stream()
        output = self._llm_detect_object(images, self.custom_base_prompt)
        self._process_llm_outputs(output)

    @interact_on_key("c")
    def llm_custom_prompt_detect_object_mode(self):
        self.custom_base_prompt = Prompt.ask("[bold][#6766e6]Custom Prompt[#6765e6][bold]")

    def llm_interactive_mode(self):
        while True:
            prompt = Prompt.ask("[bold][#6765e6]Prompt")
            if prompt == "exit":
                break
            output = self._llm_interactive_mode(prompt)
            self._process_llm_outputs(output)
        self._choose_mode()

    @interact_on_key("i")
    def _switch_to_interactive_mode(self):
        self.console.print("Running in interact mode.")
        self.llm_interactive_mode()

    @interact_on_key("m")
    def _switch_to_choose_mode(self):
        self._choose_mode()

    def _llm_detect_object(self):
        raise NotImplementedError()

    def _llm_interactive_mode(self):
        raise NotImplementedError()

    def _llm_interact(self):
        raise NotImplementedError()

    def _llm_auth(self):
        raise NotImplementedError()

    def _entry_point_interact(self):
        welcome = """# Welcome to LLM Stream Interact!"""
        md = Markdown(welcome, style="bold #e079d4")
        self.console.print("\n\n")
        self.console.print(md)

    def _choose_mode(self):
        if self._key_listeners:
            self._stop_key_listeners()
        message = """
        [bold]Choose one of the below modes:[bold]
        - 'detect' mode will start a cam video stream where you can start detecting objects by pressing (d).
        - 'detect_custom' mode is the same as detect mode but will allow you to customize the base prompt before asking the model to detect the object.
        - 'interact' mode will allow for a back and forth chat with the LLM over the detected object.
        - 'quit' will exit

        Keys while in stream:
          - (d) Will detect an object that the camera has focus on.
          - (i) Will switch to interact mode.
          - (m) Will switch back to this menu.
          - (c) Will allow for typing in a custom prompt before running (d)etect.
          - (q) Will quit the app.
        """
        self.console.print("\n\n")
        self.console.print(Panel(message, style="#e079d4"))
        self.console.print("\n\n")
        self._mode = Prompt.ask("Choose a mode", choices=["detect", "detect_custom", "interact", "quit", "d", "dc", "i", "q"], show_choices=False)
        self.custom_base_prompt = None
        if self._mode.startswith("d"):
            if self._mode in ("detect_custom", "dc"):
                custom_prompt = Prompt.ask("[bold][#6766e6]Custom Prompt[#6765e6][bold]")
                self.custom_base_prompt = custom_prompt

            if self.streamer._video_stream_is_stopped:
                self.streamer.start_video_stream()
            self.start_key_listeners()
            self.console.print("Running in detect mode. Press (d) to detect an object")

        if self._mode.startswith("i"):
            self.console.print("Running in interact mode. Type 'exit' to go back to previous menu.")
            self.llm_interactive_mode()

        if self._mode.startswith("q"):
            os._exit(1)

    def _get_api_key(self):
        api_key = Prompt.ask("[bold][#e079d4]API key(press Enter to fetch from .env instead)[#e079d4][bold]", password=True)
        if not api_key and self._api_key_dot_env_name:
            self.console.print(f"No API key provided thus will try to fetch key ({self._api_key_dot_env_name}) from .env", style="white")
            load_dotenv()
            api_key = os.getenv(self._api_key_dot_env_name)
        if not api_key:
            raise Exception("Unable to find an API key")
        self.__api_key = api_key

    def _init_streamer(self):
        while True:
            cam_index = Prompt.ask("[bold][#e079d4]Set cam index[#e079d4][bold]")
            valid_index = re.match("[0-9]+$", str(cam_index))
            if valid_index:
                streamer = Streamer(int(cam_index))
                if streamer._success:
                    self.console.print("Cam detected successfully...", style="bold green")
                    break
                self.console.print("Unable to detect cam at this index, please try again", style="bold red")
            self.console.print("Cam index must be an integer.", style="bold red")
        return streamer, cam_index

    def start_key_listeners(self):
        on_press_methods = self._get_on_press_interact_methods()
        if not on_press_methods:
            raise Exception("Can't call start method if no methods are decorated with interact_on_key")
        for method in on_press_methods:
            listener = keyboard.Listener(on_press=method)
            listener.start()
            self._key_listeners.append(listener)

    def _stop_key_listeners(self):
        for listener in self._key_listeners:
            listener.stop()

    def _get_prompt_imgs_from_stream(self):
        interaction_frames = []
        while len(interaction_frames) < self._interaction_frames_config.nframes_interact:
            interaction_frames.append(self.streamer._frame)
            print(f"{len(interaction_frames)} frames loaded...")
            time.sleep(self._interaction_frames_config.frame_capture_interval)
        return img_utils._img_arrays_to_pil_imgs(interaction_frames)

    def _get_on_press_interact_methods(self):
        press_interact_methods = []
        for method_name, method in inspect.getmembers(self, inspect.ismethod):
            method_signature = "\n".join(inspect.getsourcelines(method)[0])
            if method_name != "_get_on_press_interact_methods" and "on_press_function" in method_signature:
                press_interact_methods.append(method)
        return press_interact_methods

    def _init_tts(self, tts_model):
        self.console.print("Initializing Text To Speech Model...", style="#e079d4")
        self._tts_model = tts_model
        tts = tts_utils.TextToSpeech(model=self._tts_model)
        tts.init_model()
        return tts
