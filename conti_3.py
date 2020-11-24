from __future__ import division
from google.cloud import speech
from six.moves import queue
from difflib import SequenceMatcher
import re
import sys
import pyaudio
import numpy as np
import time

RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
PADDING = 5

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
    before = '/'
    cut_point = 0
    compare_list = []
    compare_list.append([0,0,0,0,0,0,0,0,0,0,0])
    
    start = time.time()
    
    for response in responses:
    
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript

        overwrite_chars = ' ' * (20)
        
        if(time.time()-start > 250):
            check = True
        else:
            check = result.is_final
            
        if not check:
#             print("transcript", transcript)

            now = transcript[cut_point:]
#             print("if", present_point)
            compare_list.append(similarity3(script_data[present_point-PADDING:present_point+PADDING+1], now))#now
            
            present_point, cut_point = similarity4(compare_list[-2:], present_point, before, cut_point)
            sys.stdout.write(print_script[present_point] +overwrite_chars +'\r')
#             print(print_script[present_point])
            before = transcript[cut_point:]
            
            sys.stdout.flush()
            
#             present_point = similarity2(script_data[present_point-5:present_point+5], transcript + overwrite_chars,present_point)

        else:
#             print("-----------------------------------------------------")
            compare_list = []
            compare_list.append([0,0,0,0,0,0,0,0,0,0,0])
            now = transcript[cut_point:]
            compare_list.append(similarity3(script_data[present_point-PADDING:present_point+PADDING+1], before))#before
            compare_list.append(similarity3(script_data[present_point-PADDING:present_point+PADDING+1], now))#now
            
            overwrite_chars = ' ' * (50)
            
            present_point, cut_point = similarity4(compare_list, present_point, before, cut_point)
            print(print_script[present_point]+overwrite_chars)
#             print("else", present_point)
            if re.search(r'\b(exit|quit)\b', transcript, re.I):
                print('Exiting..')
                break

            
            present_sentence = transcript + overwrite_chars
            
            before = "/"
            cut_point = 0
            
#             script_data.insert(present_point-1, ' ')
            
            if(time.time()-start > 200):
                return present_point
    
    
    
def similarity3(script, present_sentence):
    ratio = []
    present_sentence = present_sentence.replace(" ", "")
#     print(present_sentence)
#     print(script)
    for i in script:
        ratio.append(SequenceMatcher(None, present_sentence, i).ratio())
    return ratio

def similarity4(compare_list, present_point, before, cut_point):
#     print(compare_list)
#     print(np.argmax(compare_list[0]))
#     print(np.argmax(compare_list[1]))
#     print("present_point", present_point)
    if(np.max(compare_list[1]) > 0.4):
        sorting = np.argsort(compare_list[1])
        inner_present_point = sorting[-1]
#         print("inner_present_point", inner_present_point)
        next = sorting[-2]

        if((compare_list[1][inner_present_point]-compare_list[0][inner_present_point] < 0 ) and (compare_list[1][next]-compare_list[0][next] > 0 )):
            if(compare_list[1][inner_present_point] < compare_list[1][next]*2.5):
                inner_present_point = next
                cut_point = len(before)
                
        present_point = inner_present_point + present_point - PADDING    
#     print(present_point, cut_point)    
    return present_point, cut_point

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
    
    present_point = PADDING
    
    global script_data, print_script
    
    with open('conti_script_compare.txt', 'r') as f:
        data = f.read()
    script_data = data.splitlines()
    
    with open('conti_script_print.txt', 'r') as f:
        data = f.read()
    print_script = data.splitlines()
    
    
    while(True):
        with MicrophoneStream(RATE, CHUNK) as stream:
            audio_generator = stream.generator()
            requests = (speech.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator)

            responses = client.streaming_recognize(streaming_config, requests)
            present_point = listen_print_loop(responses, present_point)

if __name__ == '__main__':
    main()