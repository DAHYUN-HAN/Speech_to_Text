from __future__ import division

import re
import sys

from google.cloud import speech

import pyaudio
from six.moves import queue
from difflib import SequenceMatcher
from matplotlib import pyplot as plt

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
    print("listen_print_loop 들어옴")
    start = time.time()
    result_list = []
    
#     with open('conti_script_compare.txt', 'r') as f:
    with open('script.txt', 'r') as f:
        data = f.read()
    script_data = data.splitlines()
    
#     with open('conti_script_print.txt', 'r') as f:
    with open('script.txt', 'r') as f:
        data = f.read()
    print_script = data.splitlines()
        
    num_chars_printed = 0
    
    for response in responses:
        if(time.time()-start < 250):
            if not response.results:
                continue

            result = response.results[0]
            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript

            overwrite_chars = ' ' * (20)

            if not result.is_final:
    #             present_point, ratio = similarity3(script_data[present_point-5:present_point+6], transcript + overwrite_chars,present_point)
                
                print(transcript)
                result_list.append(similarity4(script_data[present_point-5:present_point+6], transcript, present_point))
                
#                 if(np.max(result_list[-1]) > 0.4):
#                     present_point = np.argmax(result_list[-1]) + present_point - 5

                if(present_point < 5):
                    present_point = 5

                name = script_data[present_point]

    #            sys.stdout.write("현재 대본: " + name +'\r')
    #             sys.stdout.write("현재 대본: " + script_data[present_point] + " " + str(ratio)+overwrite_chars +'\r')
    #             sys.stdout.write(transcript + overwrite_chars + '\r')
    #             sys.stdout.flush()

                num_chars_printed = len(transcript)

    
            else:
                print(transcript + overwrite_chars)

                with open('ratio_1118.txt', 'a') as f:
                    f.writelines(name+"\n")
                    for line in result_list:
                        f.writelines(str(line)+'\n')
                    
                plt.clf()
                plt.plot(result_list)
                plt.legend(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'], bbox_to_anchor=(1, 1))
                plt.savefig('similarity_graph/'+str(present_point) + name+'.png')
                
                if re.search(r'\b(exit|quit)\b', transcript, re.I):
                    print('Exiting..')
                    break

                num_chars_printed = 0

                present_sentence = transcript + overwrite_chars
                present_point = similarity2(script_data[present_point-5:present_point+6], transcript + overwrite_chars,present_point)
                print_script[present_point] = " "
                with open('script_after_run.txt', 'w') as f:
                    for line in print_script:
                        f.writelines(str(line)+'\n')
                result_list = []
        else:
            return present_point

            
def similarity(script, present_sentence, present_point):
    print('present_sentence', present_sentence)
    print('present_point', present_point)
    present_sentence = present_sentence.replace(" ", "")
    ratio = []
    for i in range(len(script)):
        script_sentence = script[i].replace(" ", "")
        script_sentence = script_sentence.replace(".", "")
    
        ratio.append(SequenceMatcher(None, present_sentence, script_sentence).ratio())
    #경험적으로, ratio() 값이 0.6 이상이면 시퀀스가 근접하게 일치함을 뜻합니다:
    print('현재 대본: ', script[np.argmax(ratio)], np.max(ratio))
    return np.argmax(ratio) +  present_point - 5
    
    
def similarity2(script, present_sentence, present_point):
#     print('present_point', present_point)
#     print('present_sentence', present_sentence)
    present_sentence = present_sentence.replace(" ", "")
    present_sentence = present_sentence.replace(".", "")
    ratio = []
    for i in range(len(script)):
        script_sentence = script[i].replace(" ", "")
        script_sentence = script_sentence.replace(".", "")
    
        ratio.append(SequenceMatcher(None, present_sentence, script_sentence).ratio())
    #경험적으로, ratio() 값이 0.6 이상이면 시퀀스가 근접하게 일치함을 뜻합니다:
    if(np.max(ratio) > 0.4):
        print('현재 대본: ', script[np.argmax(ratio)], np.max(ratio) ,"                                           ")
        return np.argmax(ratio) + present_point - 5
    else:
        print('현재 대본 : 없음                                                       ')
        return present_point    

    
def similarity3(script, present_sentence, present_point):
    present_sentence = present_sentence.replace(" ", "")
    present_sentence = present_sentence.replace(".", "")
    ratio = []
    for i in range(len(script)):
        script_sentence = script[i].replace(" ", "")
        script_sentence = script_sentence.replace(".", "")
    
        ratio.append(SequenceMatcher(None, present_sentence, script_sentence).ratio())
    #경험적으로, ratio() 값이 0.6 이상이면 시퀀스가 근접하게 일치함을 뜻합니다:
    if(np.max(ratio) > 0.4):
        return np.argmax(ratio) + present_point - 5, np.max(ratio)
    else:
        return present_point, np.max(ratio)
    
def similarity4(script, present_sentence, present_point):
    present_sentence = present_sentence.replace(" ", "")
    present_sentence = present_sentence.replace(".", "")
    ratio = []
    #print(present_sentence)
    for i in range(len(script)):
        script_sentence = script[i].replace(" ", "")
        script_sentence = script_sentence.replace(".", "")
    
        ratio.append(SequenceMatcher(None, present_sentence, script_sentence).ratio())
    return ratio

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
        with MicrophoneStream(RATE, CHUNK) as stream:

            audio_generator = stream.generator()

            requests = (speech.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator)
                

            responses = client.streaming_recognize(streaming_config, requests)

            present_point = listen_print_loop(responses, present_point)
            print("---------------------한번 끝남----------------------")
        print("microphoneStream 끝남")

if __name__ == '__main__':
    main()