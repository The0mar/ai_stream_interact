from typing import Union
from dataclasses import dataclass

import backoff
from ratelimit import limits, RateLimitException
import google.generativeai as genai

from llm_stream_interact.llm_interact_base import (
    LLMStreamInteractBase,
    interact_on_key
)


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
        self.model = genai.GenerativeModel('gemini-pro-vision')

    @interact_on_key("a")
    def identify_object(self):
        images = self._get_prompt_imgs_from_stream()
        prompt = [
            """
            I will give you 3 images of the same object and I want you to identify the object.
            """
        ]
        prompt.extend(images)
        response = self._llm_interact(
            contents=prompt,
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
            print(chunk.text)

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
    def _llm_interact(self, *args, **kwargs):
        return self.model.generate_content(*args, **kwargs)

    def _llm_auth(self, api_key):
        genai.configure(api_key=api_key)
