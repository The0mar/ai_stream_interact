import os
from typing import Union
from dataclasses import dataclass

import backoff
from rich.console import Console
from ratelimit import limits, RateLimitException
import google.generativeai as genai
from google.ai.generativelanguage import Content

from llm_stream_interact.llm_interact_base import (
    LLMStreamInteractBase,
    interact_on_key
)


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


class GeminiStreamInteract(LLMStreamInteractBase):

    def __init__(
        self,
        api_key,
        cam_index,
        interaction_frames_config
    ):
        super().__init__(
            cam_index=cam_index,
            interaction_frames_config=interaction_frames_config
        )
        self._llm_auth(api_key)
        self.text_model = genai.GenerativeModel('gemini-pro')
        self.multimodal_model = genai.GenerativeModel('gemini-pro-vision')
        self.console = Console()
        self._interactive_mode = False

    @interact_on_key("c")
    def interactive_chat(self):
        self._interactive_mode = True
        while self._interactive_mode:
            prompt = input("Prompt:")
            if prompt == "identify_mode":
                break
            if prompt.lower() in ["quit", "q"]:
                os._exit(1)

            if hasattr(self, "chat"):
                history = self.chat.history
            else:
                history = []
            response = self._llm_interact(
                prompt=prompt,
                multimodal=False,
                history=history,
                stream=True,
                generation_config=genai.types.GenerationConfig(
                    temperature=0
                ),
                safety_settings=[
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
            )
            for chunk in response:
                self.console.print(chunk.text)
        self._interactive_mode = False

    @interact_on_key("i")
    def identify_object(self):
        if not self._interactive_mode:
            images = self._get_prompt_imgs_from_stream()
            prompt = [
                """
                I will give you 3 images of the same object and I want you to identify the object. You MUST the output in the following json format without any extra text or details:

                ```
                {
                    object: <object identification goes here>,
                    description: <detailed description goes here>,
                    score: <score goes here>
                }
                ```

                object should contain a very brief identification of what the object is.
                description is a bit more detailed description of the object.
                score is how confident you are in your object identification. This MUST be a value between 0 and 1 where 0 is the lowest score and 1 is the highest.

                After you do the above task I will later follow up with some further questions. For the follow up questions don't revise your answer for the original object identification task unless explicitly asked to do so. Also make your answers concise without further explanations or confidence scores unless asked to give more detail.
                """
            ]
            prompt.extend(images)
            response = self._llm_interact(
                prompt=prompt,
                multimodal=True,
                stream=True,
                generation_config=genai.types.GenerationConfig(
                    temperature=0
                ),
                safety_settings=[
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
            )
            for chunk in response:
                self.console.print(chunk.text)

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
    def _llm_interact(
        self,
        prompt,
        multimodal=False,
        stream=True,
        history=None,
        generation_config=None,
        safety_settings=None
    ):
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

    def _llm_auth(self, api_key):
        genai.configure(api_key=api_key)
