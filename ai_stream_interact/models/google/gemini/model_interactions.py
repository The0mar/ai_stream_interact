from types import GeneratorType
from typing import Union, List, Dict
from dataclasses import dataclass

import PIL
import backoff
from rich.console import Console
from ratelimit import limits, RateLimitException
import google.generativeai as genai
from google.ai.generativelanguage import Content

from ai_stream_interact.ai_interact_base import AIStreamInteractBase
from ai_stream_interact.ai_interact_base import InteractionFramesConfig


DEFAULT_SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    }
]


def _get_text_only_history(history):
    text_only_history = []
    for messages in history:
        text_only_parts = [part for part in messages.parts if "inline_data" not in part]
        text_only_history.append(
            Content(role=messages.role, parts=text_only_parts)
        )
    return text_only_history


@dataclass
class RateLimitsConfig:
    calls: int  # number of calls per period
    period: Union[float, int]
    max_retries: int  # max retries on any none rate limit exceptions


gemini_ratelimits_config = RateLimitsConfig(calls=1, period=2, max_retries=5)


class GeminiStreamInteract(AIStreamInteractBase):
    """Implements Google's gemini-pro models interactions. For now implements text, image and text + image interactions."""

    def __init__(
        self,
        interaction_frames_config: InteractionFramesConfig,
        api_key: str = None,
        **kwargs
    ) -> None:
        super().__init__(interaction_frames_config=interaction_frames_config, **kwargs)
        self._api_key_dot_env_name = "GEMINI_API_KEY"
        if api_key:
            self.__api_key = api_key
        # self._ai_auth(self.__api_key)
        self.text_model = genai.GenerativeModel('gemini-pro')
        self.multimodal_model = genai.GenerativeModel('gemini-pro-vision')
        self.console = Console()

    def _ai_interactive_mode(
        self,
        prompt: str
    ) -> GeneratorType:
        """Simple interactive back and forth chat mode with the model."""
        if hasattr(self, "chat"):
            history = self.chat.history
        else:
            history = []
        response = self._ai_interact(
            prompt=prompt,
            multimodal=False,
            history=history,
            stream=True,
            generation_config=genai.types.GenerationConfig(
                temperature=0
            ),
            safety_settings=DEFAULT_SAFETY_SETTINGS
        )
        for chunk in response:
            yield chunk.text

    def _ai_detect_object(
        self,
        images: List[PIL.JpegImagePlugin.JpegImageFile],
        custom_base_prompt: str = None
    ) -> GeneratorType:
        """Detect object based on a primer prompt and a series of images following the prompt."""
        if custom_base_prompt:
            prompt = [custom_base_prompt]
        else:
            prompt = [
                """
                I will give you 3 images of the same object and I want you to identify the object. You MUST generate the output in the following format without any extra text:
                Object Detected: <object identification goes here>
                Detailed Description: <detailed description goes here>
                Confidence Level: <A score of how confident you are in your object identification. This MUST be a value between 0 and 1 where 0 is the lowest score and 1 is the highest.>
                """
            ]
        prompt.extend(images)
        response = self._ai_interact(
            prompt=prompt,
            multimodal=True,
            stream=True,
            generation_config=genai.types.GenerationConfig(
                temperature=0
            ),
            safety_settings=DEFAULT_SAFETY_SETTINGS
        )
        for chunk in response:
            yield chunk.text

    @backoff.on_exception(
        backoff.constant,
        exception=Exception,
        max_tries=gemini_ratelimits_config.max_retries
    )
    @backoff.on_exception(
        backoff.constant,
        exception=RateLimitException
    )
    @limits(calls=gemini_ratelimits_config.calls, period=gemini_ratelimits_config.period)
    def _ai_interact(
        self,
        prompt: str,
        multimodal: bool = False,
        stream: bool = True,
        history: genai.types.content_types.StrictContentType = None,
        generation_config: genai.types.GenerationConfig = None,
        safety_settings: List[Dict[str, str]] = None
    ) -> genai.types.generation_types.GenerateContentResponse:
        """Implements base model interaction using chat while keeping history memory."""
        if multimodal:
            model = self.multimodal_model
            history = []
        else:
            model = self.text_model
            # a dirty hack combining both gemini-pro & gemini-pro-vision as gemini-pro-vision does not currently support multi-turn chat.
            if history:
                history = _get_text_only_history(history)
            else:
                history = []
        self.chat = model.start_chat(history=history)
        return self.chat.send_message(
            prompt,
            stream=stream,
            generation_config=generation_config,
            safety_settings=safety_settings
        )

    def _ai_auth(self, api_key: str) -> None:
        """Model authentication."""
        genai.configure(api_key=api_key)
