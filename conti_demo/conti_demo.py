import argparse
import numpy as np
import pandas as pd

import io
from google.cloud import speech

from difflib import SequenceMatcher
import shutil
import os
import sys

input_audio = ("audio/input_audio/")
output_audio = ("audio/output_audio/")

def transcribe_streaming(stream):
    client = speech.SpeechClient()

    requests = (
        speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in stream
    )

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ko-KR",
    )

    streaming_config = speech.StreamingRecognitionConfig(config=config)

    responses = client.streaming_recognize(
        config=streaming_config,
        requests=requests,
    )
    
    return responses
                
def get_result(responses, present_point):
   
    for response in responses:
        for result in response.results:
            alternatives = result.alternatives
            for alternative in alternatives:
                transcript = alternative.transcript
                present_point = similarity(script_data[present_point-5:present_point+5], transcript,present_point)
                print(print_script[present_point])
                
    return present_point

def similarity(script, present_sentence, present_point):
    present_sentence = present_sentence.replace(" ", "")
    present_sentence = present_sentence.replace(".", "")
    ratio = []
    for i in range(len(script)):
        script_sentence = script[i]
    
        ratio.append(SequenceMatcher(None, present_sentence, script_sentence).ratio())
    if(np.max(ratio) > 0.4):
        return np.argmax(ratio) + present_point - 5
    else:
        return present_point
                
                
def setting():
    with open('conti_script_compare.txt', 'r') as f:
        data = f.read()
    script_data = data.splitlines()
    
    with open('conti_script_print.txt', 'r') as f:
        data = f.read()
    print_script = data.splitlines()
    
    with open('jitter.txt', 'r') as f:
        data = f.read()
    jitter = data.splitlines()
    jitter = np.array(jitter, np.int16)
    ratio = 0.05
    jitter = ratio*jitter
    jitter = jitter.astype(np.int16)
    
    with io.open('blank.wav', "rb") as audio_file:
        blank= audio_file.read()
    blank = np.frombuffer(blank, np.int16)
    
    return script_data, print_script, jitter, blank

def get_audio(audio):
    with io.open(audio, "rb") as audio_file:
        byte_content = audio_file.read()
    
    int_content = np.frombuffer(byte_content, np.int16)
    
    sum = 0
    count = 0
    check = True
    new_content = int_content
    
    for i in range(len(int_content)):
        if(abs(int_content[i]) < 1000) :
            sum = sum + 1
            if(sum > 4000):
                if(check):
                    check = False

                    point = i + (len(blank[44:])*count)
                    new_content = np.concatenate((new_content[44:point], blank[44:], new_content[point:]), axis=0)
                    count = count +1
                              
        else:
            sum = 0
            check = True
    
    new_content = new_content + jitter[:len(new_content)]
    byte_content = new_content.tobytes()
    return [byte_content]

def predict(audio, present_point):
    stream = get_audio(input_audio + audio)
    responses = transcribe_streaming(stream)
    
    present_point = get_result(responses, present_point)
    move_file(audio)
    return present_point

def move_file(audio):
    shutil.move(input_audio+audio, output_audio + audio)
    
def main():
    global script_data, print_script, jitter, blank
    script_data, print_script, jitter, blank = setting()
    
    present_point = 5
    
    while True:
        
        try:
            input_audio_list = os.listdir(input_audio)

            if(len(input_audio_list)):
                
                present_point = predict(input_audio_list[0], present_point)

        except KeyboardInterrupt:
            print("종료")
            break
            
#     audio = 'test.wav'
#     present_point = predict(audio, present_point)
    
if __name__ == "__main__":
    main()
    sys.exit()