# AI Stream Interact🧠🎞️ aims to provide basic LLM interaction capabilities with video streams.
This package can easily be extended to accommodate different LLMs, but for this first version interactions were implemented only for [Google's Gemini Pro & Vision Pro Models](https://ai.google.dev/tutorials)

**Note: This is a basic Alpha version that's been written & tested in Ubuntu only so it may have unexpected behavior with other operating systems.**

<br>
<br>

## Installation:
- `pip install ai-stream-interact`

Note that pip install will also install [coqui-ai](https://github.com/coqui-ai/TTS) as future versions will include Text To Speech. (It is already implemented but sometimes presents unexpected behavior so it's turned off by default for now.)


## Example Usage:

1. Make sure you already have an API key for Gemini. (or get one [here](https://ai.google.dev/tutorials/setup)).
2. Have a USB camera connected.
3. run `aisi_gemini` to enter the AI Stream Interact🧠🎞️ main menu. _(note that you can always go back to the main menu from the video stream by press "**m**" while having the video stream focused.)_

There are 3 interaction modes available:

### Detect Default:
This fires up a window with your camera stream and whenever you press "**d**" will identify the object the camera is looking at. (Make sure to press "**d**" with the camera window focused and not your terminal).
![](https://github.com/The0mar/ai_stream_interact/blob/main/gifs/detect.gif)


### Detect with Custom Prompt:
Use this to write up a custom prompt before showing the model an object for custom interactions beyond just identifying objects.
![](https://github.com/The0mar/ai_stream_interact/blob/main/gifs/detect_custom.gif)

### Interactions:
This just allows for back & forth chat with the model.

## Troubleshooting:

### Errors:

- `google.api_core.exceptions.FailedPrecondition: 400 User location is not supported for the API use.`: **This is specific to Gemini as they currently do not provide general availability to all regions, so you need to make sure your region is supported [https://ai.google.dev/available_regions#available_regions]()**
