from __future__ import division

import re
import sys

from google.cloud import speech

import pyaudio
from six.moves import queue
from difflib import SequenceMatcher

import numpy as np
import time
# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

class MicrophoneStream(object):
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)

def listen_print_loop(responses, present_point):
    first = present_point
    first_ratio = []
    start = time.time()
    result_list = []
    
    NEXT_STEP = False
    
    with open('conti_script_compare.txt', 'r') as f:
        data = f.read()
    script_data = data.splitlines()
    
    with open('conti_script_print.txt', 'r') as f:
        data = f.read()
    print_script = data.splitlines()
    
    num_chars_printed = 0
    
    for response in responses:
        
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript

        overwrite_chars = ' ' * (50)

        if not result.is_final:
            print(transcript)
            if(len(transcript)):
                temp_ratio = (similarity4(script_data[present_point-5:present_point+10], transcript + overwrite_chars,present_point))
                print("temp_ratio", temp_ratio)
#             print(len(transcript))
#             print("present_point", present_point)
            if(len(temp_ratio)):
                result_list.append(temp_ratio)
                print(result_list)
            first_ratio.append(SequenceMatcher(None, transcript, script_data[first]).ratio())
            if(len(result_list)>=2):
                present_point, ratio, NEXT_STEP = similarity6(script_data[present_point-5:present_point+10], result_list[-2:], present_point, NEXT_STEP, len(transcript), first_ratio[-2:])
#             sys.stdout.write("현재 대본: " + script_data[present_point] + " " + str(ratio)+overwrite_chars +'\r')
            sys.stdout.write(print_script[present_point]+overwrite_chars +'\r')
            sys.stdout.flush()

            num_chars_printed = len(transcript)


        else:
#             print(transcript + overwrite_chars)
            result_list.append(similarity4(script_data[present_point-5:present_point+10], transcript + overwrite_chars,present_point))
            present_point, ratio, NEXT_STEP = similarity6(script_data[present_point-5:present_point+10], result_list[-2:], present_point, NEXT_STEP, len(transcript), first_ratio[-2:])
            print(print_script[present_point]+overwrite_chars)
        
            if re.search(r'\b(exit|quit)\b', transcript, re.I):
                print('Exiting..')
                break

            num_chars_printed = 0
        
            result_list = []
            NEXT_STEP = False
            first = present_point
            first_ratio = []
            
            if(time.time()-start > 200):
                return present_point
            
def similarity4(script, present_sentence, present_point):
    ratio = []
#     print(present_sentence)
    
    for i in script:    
#         print(i)
        print(SequenceMatcher(None, present_sentence, i).ratio())
        ratio.append(SequenceMatcher(None, present_sentence, i).ratio())
    
    return ratio

def similarity6(script, result_list, present_point, NEXT_STEP, length, first_ratio):
#     print(result_list)
    present_ratio = result_list[0]
    present = present_point
#     print("similarity6 present_point", present_point)
    if(length < 2):
        if(np.max(result_list) > 0.4):
            if(not NEXT_STEP) : 
                present = np.argmax(result_list[-1])
                present_ratio = result_list[-1][present]
            next = present+1
            if(next == len(script)):
                next = next-1

            if(np.max(result_list[-1])<result_list[-1][next]*3):
                if((result_list[-1][present]-result_list[0][present] < 0) and (result_list[-1][next]-result_list[0][next] > 0)):
                    present = next
                    present_ratio = result_list[-1][present]
                    NEXT_STEP = True
            present_point = present + present_point-5
    else:
        if(not NEXT_STEP) : 
            present = np.argmax(result_list[-1])
            present_ratio = result_list[-1][present]
        next = present+1
        if(next == len(script)):
            next = next-1

        if(first_ratio[-1]<result_list[-1][next]*3):
            if((first_ratio[-1]-first_ratio[0] < 0) and (result_list[-1][next]-result_list[0][next] > 0)):     #확인 필요
                present = next
                present_ratio = result_list[-1][present]
                NEXT_STEP = True
        present_point = present + present_point-5
        
    return present_point, present_ratio, NEXT_STEP



def similarity7(script, result_list, present_point, NEXT_STEP, length, first_ratio):
#     print(result_list)
    present_ratio = result_list[0]
    present = 0
#     print("similarity7 present_point", present_point)
    
    if(not NEXT_STEP) : 
        present = np.argmax(result_list[-1])
        present_ratio = result_list[-1][present]
    next = present+1
    if(next == len(script)):
        next = next-1

    if(first_ratio[-1]<result_list[-1][next]*3):
        if((first_ratio[-1]-first_ratio[0] < 0) and (result_list[-1][next]-result_list[0][next] > 0)):     #확인 필요
            present = next
            present_ratio = result_list[-1][present]
            NEXT_STEP = True
    present_point = present + present_point-5
        
    return present_point, present_ratio, NEXT_STEP


def main():
    language_code = 'ko-KR'
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code)
    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True)
    
    present_point = 5
        
    while(True):
#         print("시작", present_point)
        with MicrophoneStream(RATE, CHUNK) as stream:
            audio_generator = stream.generator()
            requests = (speech.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator)
            responses = client.streaming_recognize(streaming_config, requests)
            present_point = listen_print_loop(responses, present_point)

if __name__ == '__main__':
    main()