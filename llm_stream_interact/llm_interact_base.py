import glob
import time
import inspect
import tempfile
from dataclasses import dataclass

import cv2
from PIL import Image
from pynput import keyboard

from llm_stream_interact.mixin import StreamerMixin


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


class LLMStreamInteractBase(StreamerMixin):

    def __init__(
        self, cam_index,
        interaction_frames_config: InteractionFramesConfig
    ):
        super().__init__(cam_index=cam_index)
        self._interaction_frames_config = interaction_frames_config

    def start_model_listeners(self):
        on_press_methods = self._get_on_press_interact_methods()
        if not on_press_methods:
            raise Exception("Can't call start method if no methods are decorated with interact_on_key")
        for method in on_press_methods:
            listener = keyboard.Listener(on_press=method)
            listener.start()

    def _get_prompt_imgs_from_stream(self):
        interaction_frames = []
        while len(interaction_frames) < self._interaction_frames_config.nframes_interact:
            interaction_frames.append(self._frame)
            print(f"{len(interaction_frames)} frames loaded...")
            time.sleep(self._interaction_frames_config.frame_capture_interval)
        return self._convert_frames_to_pil_imgs(interaction_frames)

    def _llm_interact(self):
        raise NotImplementedError()

    def _llm_auth(self):
        raise NotImplementedError()

    def _convert_frames_to_pil_imgs(self, frames):
        """ Writes cv np.array frames and reloads them in PIL.image format """
        with tempfile.TemporaryDirectory() as tmp:
            for n, frame in enumerate(frames):
                cv2.imwrite(f"{tmp}/frame{n}.jpg", frame)
            images_list = []
            image_paths = glob.glob(f"{tmp}/*.jpg")
            for path in image_paths:
                img = Image.open(path)
                images_list.append(img)
        return images_list

    def _get_on_press_interact_methods(self):
        press_interact_methods = []
        for method_name, method in inspect.getmembers(self, inspect.ismethod):
            method_signature = "\n".join(inspect.getsourcelines(method)[0])
            if method_name != "_get_on_press_interact_methods" and "on_press_function" in method_signature:
                press_interact_methods.append(method)
        return press_interact_methods
