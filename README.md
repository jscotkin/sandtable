# sandtable

There's a few different things in here, all written for my ZenXY sandtable built from plans at V1 Engineering (v1e.com). 

# sandsketch
Let's you use a PS5 DualSense controller and a PC to turn your sandtable into an etch-a-sketch, with a few extra controls for inituitive arcs, circles and spirals. Can also home the table and has a built-in screen wipe for all or part of the table. You can save your drawing as gcode to replay in the future.

# sandsender
Send a gcode file to your sand table over the network.

# sandvision
Experiment using OpenCV and a camera to identify objects placed on my table and outline them in the sand. Currently very specific to my table which happens to have a very identifiable black border around the white sand that makes vision a bit more straightforward.

# sandgpt
Experiment with AI voice control of ZenXY sandtable

This is set up to enable voice control of my ZenXY sandtable. Mine is running off a Makerbase DLC32 board using GRBL, which I communicate with over telnet at port 8080. This is a quick prototype - you'll need to change the hardcoded IP address and port to match your setup.

This uses two APIs from OpenAI - Whisper to convert audio to text and Completions to call GPT-4-turbo.

You'll need a .env file in your directory which has your OpenAI API key:

OPENAI_API_KEY="your API key"
