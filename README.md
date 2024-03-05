# sandgpt
AI voice control of ZenXY sandtable

This is set up to enable voice control of my ZenXY sandtable (more info at v1e.com). Mine is running off a Makerbase DLC32 board using GRBL, which I communicate with over telnet at port 8080. This is a quick prototype - you'll need to change the hardcoded IP address and port to match your setup.

This uses two APIs from OpenAI - Whisper to convert audio to text and Completions to call GPT-4-turbo.

You'll need a .env file in your directory which has your OpenAI API key:

OPENAI_API_KEY="your API key"
