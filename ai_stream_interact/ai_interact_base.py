import os
import re
import time
import queue
import inspect
import threading
from types import GeneratorType
from dataclasses import dataclass

from pynput import keyboard
from rich import print
from rich.panel import Panel
from rich.prompt import Prompt
from rich.console import Console
from rich.markdown import Markdown
from dotenv import load_dotenv

from ai_stream_interact.streamer import Streamer
from ai_stream_interact.utils import img_utils
from ai_stream_interact.tts.tts_base import TextToSpeechBase
from ai_stream_interact.tts.tts_utils import play


@dataclass
class InteractionFramesConfig:
    nframes_interact: str  # number of video frames to use for ai interaction
    frame_capture_interval: float  # n seconds to sleep between capturing frames


def interact_on_key(key):
    def on_key_press(func):
        def wrapper(self, key_pressed):
            """on_press_function"""
            if hasattr(key_pressed, 'char') and key_pressed.char == (key):
                func(self)
        return wrapper
    return on_key_press


class AIStreamInteractBase:
    """Base class for Model Interactions. The class implements the skeleton for the cli menu and model interactions
    The below methods are to be implemented in child classes per each model's API:
        - _ai_auth: should implement the authentication for the relevant model.
        - _ai_interact: should implement the most basic interaction for a given model where it takes a prompt input (and potentially other **kwargs for model configs) and returns the model's repsponse.
        - _ai_interactive_mode: Same as the base _ai_interact but should keep track of chat history.
        - _ai_detect_object: should implement a function that does object detection in an image and returns either a string or a Generator (for streaming models).
    """

    def __init__(
        self,
        interaction_frames_config: InteractionFramesConfig,
        tts_instance: TextToSpeechBase
    ):
        self._console_interface = Console(style="bold #e079d4")
        self._console_model_output = Console(style="bold #6edb9d")
        self._console_user_prompt = Console(style="bold #6765e6")
        self._console_success = Console(style="bold green")
        self._console_warning = Console(style="bold red")
        self._interaction_frames_config = interaction_frames_config
        self._key_listeners = []
        self._api_key_dot_env_name = ""
        self._tts_instance = tts_instance
        self._complete_sentences_queue = queue.Queue()
        self._incomplete_sentences_queue = queue.Queue()

    def _ai_interact(self):
        raise NotImplementedError()

    def _ai_auth(self):
        raise NotImplementedError()

    def _ai_detect_object(self):
        raise NotImplementedError()

    def _ai_interactive_mode(self):
        raise NotImplementedError()

    def start(self):
        self._entry_point_interact()
        self._get_api_key()
        self._ai_auth(self.__api_key)
        self.streamer, self._cam_index = self._init_streamer()
        self._choose_mode()

    def _start_speech_synthesis_thread(self):
        threading.Thread(target=self._run_speech_synthesis, args=(), daemon=True).start()

    def _run_speech_synthesis(self):
        while True:
            if not self._presenting_in_progressand self._complete_sentences_queue.empty():
                break
            text = self._complete_sentences_queue.get()
            if not text:
                raise Exception("Got empty string for speech synthesis..")  # for easier debugging as it throws a difficult to spot error when it happens
            play(tts=self._tts_instance, text=text)

    def _queue_sentences(self, text):
        sentences = re.split("(?<=[a-z]\.)[ \n]", text)  # split text on lower case + "." ends.
        sentences = [sent for sent in sentences if sent]
        if not self._incomplete_sentences_queue.empty():
            partial_sent = self._incomplete_sentences_queue.get()
            sentences[0] = partial_sent + " " + sentences[0]
        if re.match("(.*?)[a-z]\.$", sentences[-1]):
            self._complete_sentences_queue.put(" ".join(sentences))
        elif len(sentences) > 1:
            self._complete_sentences_queue.put(" ".join(sentences[:-1]))
            self._incomplete_sentences_queue.put(sentences[-1])
        else:
            self._incomplete_sentences_queue.put(sentences[0])

    def _present_model_output(self, output):
        self._presenting_in_progress = True
        assert isinstance(output, (str, GeneratorType, list)), "output should be of type stror Generator"
        if isinstance(output, str):  # model output is expected to be either text or a Generator for stream output
            output = [output]
        for out in output:
            self._start_speech_synthesis_thread()
            self._queue_sentences(out)
            self._console_model_output.print(out)
        self._presenting_in_progress = False

    @interact_on_key("d")
    def ai_detect_object_mode(self):
        images = self._get_prompt_imgs_from_stream()
        output = self._ai_detect_object(images, self.custom_base_prompt)
        self._present_model_output(output)

    def ai_interactive_mode(self):
        while True:
            prompt = Prompt.ask("Prompt", console=self._console_user_prompt)
            if prompt == "exit":
                break
            output = self._ai_interactive_mode(prompt)
            self._present_model_output(output)
        self._choose_mode()

    @interact_on_key("c")
    def ai_custom_prompt_detect_object_mode(self):
        self.custom_base_prompt = Prompt.ask("Custom Prompt", console=self._console_user_prompt)

    @interact_on_key("i")
    def _switch_to_interactive_mode(self):
        self.console.print("Running in interact mode.")
        self.ai_interactive_mode()

    @interact_on_key("m")
    def _switch_to_choose_mode(self):
        self._choose_mode()

    def _entry_point_interact(self):
        welcome = """# Welcome to AI Stream Interact!"""
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
        - 'interact' mode will allow for a back and forth chat with the AI over the detected object.
        - 'quit' will exit

        Keys while in stream:
          - (d) Will detect an object that the camera has focus on.
          - (i) Will switch to interact mode.
          - (m) Will switch back to this menu.
          - (c) Will allow for typing in a custom prompt before running (d)etect.
          - (q) Will quit the app.
        """
        self._console_interface.print("\n\n")
        self._console_interface.print(Panel(message))
        self._console_interface.print("\n\n")
        self._mode = Prompt.ask("Choose a mode", choices=["detect", "detect_custom", "interact", "quit", "d", "dc", "i", "q"], show_choices=False)
        self.custom_base_prompt = None
        if self._mode.startswith("d"):
            if self._mode in ("detect_custom", "dc"):
                custom_prompt = Prompt.ask("Custom Prompt", console=self._console_user_prompt)
                self.custom_base_prompt = custom_prompt

            if self.streamer._video_stream_is_stopped:
                self.streamer.start_video_stream()
            self._start_key_listeners()
            self.console.print("Running in detect mode. Press (d) to detect an object")

        if self._mode.startswith("i"):
            self.console.print("Running in interact mode. Type 'exit' to go back to previous menu.")
            self.ai_interactive_mode()

        if self._mode.startswith("q"):
            os._exit(1)

    def _get_api_key(self):
        api_key = Prompt.ask("API key (press Enter to fetch from .env instead)", password=True, console=self._console_interface)
        if not api_key and self._api_key_dot_env_name:
            self.console.print(f"No API key provided thus will try to fetch key ({self._api_key_dot_env_name}) from .env", style="white")
            load_dotenv()
            api_key = os.getenv(self._api_key_dot_env_name)
        if not api_key:
            raise Exception("Unable to find an API key")
        self.__api_key = api_key

    def _init_streamer(self):
        while True:
            cam_index = Prompt.ask("Set cam index", console=self._console_interface)
            valid_index = re.match("[0-9]+$", str(cam_index))
            if valid_index:
                streamer = Streamer(int(cam_index))
                if streamer._success:
                    self._console_success.print("Cam detected successfully...")
                    break
                self.console.print("Unable to detect cam at this index, please try again", style="bold red")
            self.console.print("Cam index must be an integer.", style="bold red")
        return streamer, cam_index

    def _start_key_listeners(self):
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