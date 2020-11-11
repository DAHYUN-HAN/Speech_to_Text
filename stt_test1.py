from __future__ import division

import re
import sys

from google.cloud import speech

import pyaudio
from six.moves import queue
from difflib import SequenceMatcher

import numpy as np

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

script = ['아주 멀리까지 가 보고 싶어',
          '그곳에선 누구를 만날 수가 있을지',
          '아주 높이까지 오르고 싶어',
          '얼마나 더 먼 곳을 바라볼 수 있을지',
          '작은 물병 하나, 먼지 낀 카메라',
          '때 묻은 지도 가방 안에 넣고서',

          '언덕을 넘어 숲길을 헤치고',
          '가벼운 발걸음 닿는 대로',
          '끝없이 이어진 길을 천천히 걸어가네',


          '멍하니 앉아서 쉬기도 하고',
          '가끔 길을 잃어도 서두르지 않는 법',
          '언젠가는 나도 알게 되겠지',
          '이 길이 곧 나에게 가르쳐 줄 테니까',

          '촉촉한 땅바닥 앞서 간 발자국',
          '처음 보는 하늘 그래도 낯익은 길',

          '언덕을 넘어 숲길을 헤치고',
          '가벼운 발걸음 닿는 대로',
          '끝없이 이어진 길을 천천히 걸어가네',


          '새로운 풍경에 가슴이 뛰고',
          '별것 아닌 일에도 호들갑을 떨면서',
          '나는 걸어가네 휘파람 불며',
          '때로는 넘어져도 내 길을 걸어가네',

          '작은 물병 하나 먼지 낀 카메라',
          '때 묻은 지도 가방 안에 넣고서',

          '언덕을 넘어 숲길을 헤치고',
          '가벼운 발걸음 닿는 대로',
          '끝없이 이어진 길을 천천히 걸어가네',

          '내가 자라고 정든 이 거리를',
          '난 가끔 그리워하겠지만',
          '이렇게 나는 떠나네 더 넓은 세상으로']

class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)

def listen_print_loop(responses):
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = ' ' * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + '\r')
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            print(transcript + overwrite_chars)

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r'\b(exit|quit)\b', transcript, re.I):
                print('Exiting..')
                break

            num_chars_printed = 0
            
            present_sentence = transcript + overwrite_chars
            similarity(present_sentence)

            
def similarity(present_sentence):
    present_sentence = present_sentence.replace(" ", "")
    present_sentence = present_sentence.replace(".", "")
    ratio = []
    for i in range(len(script)):
        script_sentence = script[i].replace(" ", "")
        script_sentence = script[i].replace(".", "")
    
        ratio.append(SequenceMatcher(None, present_sentence, script_sentence).ratio())
    print('현재 대본: ', script[np.argmax(ratio)], np.max(ratio))
    
    
def similarity(present_sentence):
    present_sentence = present_sentence.replace(" ", "")
    present_sentence = present_sentence.replace(".", "")
    ratio = []
    for i in range(len(script)):
        script_sentence = script[i].replace(" ", "")
        script_sentence = script[i].replace(".", "")
    
        ratio.append(SequenceMatcher(None, present_sentence, script_sentence).ratio())
    
    if(np.max(ratio) > 0.5):
        print('현재 대본: ', script[np.argmax(ratio)], np.max(ratio))
    else:
        print('대본에 없음')


def main():
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = 'ko-KR'  # a BCP-47 language tag
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code)
    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True)

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (speech.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)

        responses = client.streaming_recognize(streaming_config, requests)

        # Now, put the transcription responses to use.
        listen_print_loop(responses)

if __name__ == '__main__':
    main()