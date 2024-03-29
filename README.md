# AI Stream Interact🧠🎞️ - LLM interaction capabilities on live USB camera video stream.
This package can easily be extended to accommodate different LLMs, but for this first version interactions were implemented only for [Google's Gemini Pro & Vision Pro Models](https://ai.google.dev/tutorials)

**Note: This is a basic Alpha version that's been written & tested in Ubuntu Linux only so it may have unexpected behavior with other operating systems.**

<br>
<br>

## Installation:
- `pip install ai-stream-interact`

Note that pip install might take a while as it will also install [coqui-ai](https://github.com/coqui-ai/TTS) for Text to Speech. Although TTS is partially implemented it is not turned on by default due to some glitchy behavior. (This will be fixed in future releases.)

## Example Usage:

1. You need a Gemini API key. (if you don't already have one you can get one [here](https://ai.google.dev/tutorials/setup)).
2. Have a USB camera connected.
3. run `aisi --llm gemini` to enter the AI Stream Interact🧠🎞️ main menu. _(note that you can always go back to the main menu from the video stream by press "**m**" while having the video stream focused.)_
4. Enter the API key or press enter if you've added it to .env.
5. You will be asked to enter your camera index. Currently there is no straight forward way to identify the exact index for your camera's name due to how open-cv enumerates such indicies so you'll have to just try a few times till you get the right one if you have multiple camers connected. If you have one camera connected you can try passing "**-1**" as in most cases it'll just pick that one.
   
Now you're in!. You have access to 3 types of interactions as of today.

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

- `google.api_core.exceptions.FailedPrecondition: 400 User location is not supported for the API use.`: **This is specific to Gemini as they currently do not provide general availability to all regions, so you need to make sure your region is supported [here](https://ai.google.dev/available_regions#available_regions)**
