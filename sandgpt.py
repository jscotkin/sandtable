from openai import OpenAI
from dotenv import load_dotenv
import asyncio, telnetlib3
import time

import struct
import wave
import keyboard
from pvrecorder import PvRecorder

#for index, device in enumerate(PvRecorder.get_available_devices()):
#    print(f"{index}: {device}")

load_dotenv()
client = OpenAI()

def get_audio():
  audio_file = "wavfile.wav"
  recorder = PvRecorder(frame_length=512, device_index=0)
  recorder.start()

  print("Press space to start recording")
  while True:
    if keyboard.is_pressed(' '):
      keyboard.release(' ')
      time.sleep(1)
      break

  print ("Recording started, press space to stop")
  try:
      audio = wave.open(audio_file, 'w')
      audio.setparams((1, 2, recorder.sample_rate, recorder.frame_length, "NONE", "NONE"))
      while True:
          frame = recorder.read()
          audio.writeframes(struct.pack('h' * len(frame), *frame))
          if keyboard.is_pressed(' '):
            keyboard.release(' ')
            time.sleep(1)
            break
  except KeyboardInterrupt:
      print("Stopping recording")
  finally:
      recorder.delete()
      audio.close()
  
  return audio_file

def audio_to_text(wavfile):
  audio_file = open(wavfile, "rb")
  transcription = client.audio.transcriptions.create(
     model = "whisper-1",
     file = audio_file
  )

  print(transcription.text)
  return transcription.text
   

def text_to_gcode(command):
  response = client.chat.completions.create(
    model = "gpt-4-turbo-preview",
    temperature = 0.8,
    max_tokens = 4000,
    response_format={ "type": "text" },
    messages = [
      {"role": "system", "content": "You develop gcode to draw requested shapes on a robotic sand table which uses a marble to create patterns in the sand, precisely controlled via X and Y positions. The table is homed such that the lower left corner is 0,0, with X axis length of 530mm and Y axis length of 1250 mm. You don't need to rehome the table or start from 0,0. The marble is always in the sand so there is no Z axis. The movement rate should always be set to 1500mm/s. Responses should be in gcode with no commentary. Please make sure to carefully think about whether the coordinates are correct for the shape you are asked to draw, and that the order you are connecting points is correct for that shape.  Make sure that none of the commands will ever exceed the dimensions of the table. Please try to visualize the gcode you have generated when you are finished and see if it meets the request and these restrictions - if it does not fix the issue and generate it again."},
      {"role": "user", "content": "Draw an 8-inch, 5-pointed star."},
      {"role": "assistant", "content": """
G21 ; Set units to millimeters
G90 ; Use absolute positioning
G0 X82.20 Y-59.72 ; Move to start
G1 X-31.40 Y96.63 F1200 ; Draw line
G1 X-31.40 Y-96.63 F1200 ; Draw line
G1 X82.20 Y59.72 F1200 ; Draw line
G1 X-101.60 Y0.00 F1200 ; Draw line
G1 X82.20 Y-59.72 F1200 ; Draw line"""},
      #{"role": "user", "content": "Please generate G-Code to draw three five-inch circles in a line along the Y-axis, centered in the X axis."}
      #{"role": "user", "content": "Please generate G-Code to draw the Olympic rings."}
      {"role": "user", "content": command}
    ]
  )


  gcode = response.choices[0].message.content.strip("```\n")
  print(gcode)
  return gcode

async def send_gcode_to_table(gcode):
  reader, writer = await telnetlib3.open_connection("192.168.1.55", 8080)
  reply = await reader.read(128) # read the GRBL header
  for line in gcode.split("\n"):
    print(line)
    writer.write(line + "\n")
    reply = await reader.read(128)
    print('reply:', reply)



audio_file = get_audio()
transcription = audio_to_text(audio_file)
gcode = text_to_gcode(transcription)
asyncio.run(send_gcode_to_table(gcode))

