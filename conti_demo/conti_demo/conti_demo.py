import argparse
import numpy as np
import pandas as pd

import io
from google.cloud import speech

from difflib import SequenceMatcher
import shutil
import os
import sys
import wave
import soundfile as sf
import librosa

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
        enable_word_time_offsets=True,
    )

    streaming_config = speech.StreamingRecognitionConfig(config=config)

    responses = client.streaming_recognize(
        config=streaming_config,
        requests=requests,
    )
    
    return responses
                
def get_result(responses, present_point):
    global before, input_audio_list, word_list, file_name
    word_list = []
    ratio_list = []
    ratio_list.append(0.0)
    start_time_list = []
    end_time_list = []
    final_time_list = []
    i = 1
    for response in responses:
        for result in response.results:
            
            #단어별 시간 출력
            alternative = result.alternatives[0]
#             print("for 바깥")
            for word_info in alternative.words:
                word = word_info.word
                word_list.append(word)
                start_time = word_info.start_time
                end_time = word_info.end_time
                    
                start_time_list.append(start_time.total_seconds())
                end_time_list.append(end_time.total_seconds())
                
#                 print(
#                     f"Word: {word}, start_time: {start_time.total_seconds()}, end_time: {end_time.total_seconds()}"
#                 )
                max_point, ratio = similarity(script_data[present_point-1:present_point+10], present_point)
                ratio_list.append(ratio)
#                 print(word_list)
#                 print(ratio_list[-1])
                if(ratio > 0.3):
                    if(ratio_list[-1] == 1):
                        present_point = max_point + present_point -1
                        ratio_list = []
                        ratio_list.append(0.0)
                        word_list = []
                        final_time_list.append(start_time_list[0])
                        
                        start_time_list = []
                        
                        print(present_point, print_script[present_point])
                        with open('final/txt/' + file_name[:-4] + "_" + str(i) + ".txt", 'w') as f:
                            f.writelines(print_script[present_point]+'\n')
                        i = i +1
                    elif(ratio_list[-1] < ratio_list[-2]):
                        present_point = max_point + present_point -1
                        ratio_list = []
                        ratio_list.append(0.0)
                        last = word_list[-1]
                        word_list = []
                        word_list.append(last)
                        final_time_list.append(start_time_list[0])
                        temp_start = start_time_list[-1]
                        start_time_list = []
                        start_time_list.append(temp_start)
                       
                        print(present_point, print_script[present_point])
                        with open('final/txt/' + file_name[:-4] + "_" + str(i) + ".txt", 'w') as f:
                            f.writelines(print_script[present_point]+'\n')
                        i = i +1
                    
                
#             #대본 비교    
#             alternatives = result.alternatives
#             for alternative in alternatives:
#                 transcript = alternative.transcript
#                 present_point = similarity(script_data[present_point-5:present_point+5], transcript,present_point)
#                 if(present_point != before):
#                     print(print_script[present_point])
                    
#                     #대본 저장
#                     f = open("txt/"+ input_audio_list[0][:-4] + "_" + str(i) + ".txt", 'w')
#                     f.write(print_script[present_point])
#                     f.close()
#                     i = i+1

#                 before = present_point
    print(final_time_list)
    return present_point, final_time_list

def similarity(script, present_point):
    global word_list
    present_sentence = ''.join(word_list)
    ratio = []
    for i in range(len(script)):
        script_sentence = script[i]
    
        ratio.append(SequenceMatcher(None, present_sentence, script_sentence).ratio())
    return np.argmax(ratio), np.max(ratio)
#     if(np.max(ratio) > 0.6):
#         return np.argmax(ratio) + present_point - 1
#     else:
#         return present_point
                
                
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
    global file_name
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
    print(count)
    
    sf.write("audio/blank_ver/blank_ver_" + file_name, new_content, 16000, subtype='PCM_16')
    new_content_jitter_ver = new_content + jitter[:len(new_content)]
    byte_content = new_content_jitter_ver.tobytes()
        
    
    return [byte_content], new_content

def predict(audio, present_point):
    stream, new_content = get_audio(input_audio + audio)
    
    responses = transcribe_streaming(stream)
    
    present_point, final_time_list = get_result(responses, present_point)
    
    for i in range(len(final_time_list)):
        if(i==len(final_time_list)-1):
            sf.write("final/audio/" + file_name[:-4] + "_" + str(i+1) + ".wav", new_content[int(float(final_time_list[i])*16000):len(new_content)], 16000, subtype='PCM_16')
        else:
            sf.write("final/audio/" + file_name[:-4] + "_" + str(i+1) + ".wav", new_content[int(float(final_time_list[i])*16000):int(float(final_time_list[i+1])*16000)], 16000, subtype='PCM_16')
        
    move_file(audio)
        
    return present_point

def move_file(audio):
    shutil.move(input_audio+audio, output_audio + audio)
    
def main():
    global script_data, print_script, jitter, blank, before, input_audio_list, file_name
    script_data, print_script, jitter, blank = setting()
    before = 0
    present_point = 1
    while True:
        try:
            input_audio_list = os.listdir(input_audio)

            if(len(input_audio_list)):
                file_name = input_audio_list[0]
                present_point = predict(file_name, present_point)

        except KeyboardInterrupt:
            print("종료")
            break
    
if __name__ == "__main__":
    main()
    sys.exit()