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

# script_data = [' ',
#                ' ',
#                ' ',
#                ' ',
#                ' ',
    
#                '동해물과 백두산이 마르고 닳도록',
#                '하느님이 보우하사 우리나라 만세',
#                '무궁화 삼천리 화려 강산',
#                '대한 사람 대한으로 길이 보전하세',
#                '남산 위에 저 소나무 철갑을 두른 듯',
#                '바람 서리 불변함은 우리 기상일세',

#                '가을 하늘 공활한데 높고 구름 없이',
#                '밝은 달은 우리 가슴 일편단심일세',
#                '이 기상과 이 맘으로 충성을 다하여',


#                '괴로우나 즐거우나 나라 사랑하세',
#                '아름다운 이 땅에 금수강산에',
#                '단군할아버지가 터잡으시고',
#                '홍익인간 뜻으로 나라세우니',

#                '대대손손 훌륭한 인물도 많아',
#                '고구려세운 동명왕 백제 온조왕',
#                '알에서 나온 혁거세',
#                '만주벌판 달려라 광개토대왕 신라장군 이사부',
#                '백결선생 떡방아 삼천궁녀 의자왕',
#                '황산벌의 계백 맞서 싸운 관창',
#                '역사는 흐른다',
#                '말목자른 김유신 통일 문무왕',
#                '원효대사 해골물 혜초천축국',
#                '바다의왕자 장보고 발해 대조영',
#                '귀주대첩 강감찬 서희 거란족',
#                '무단 정치 정중부 화포 최무선',
#                '죽림칠현 김부식',
               
#                '지눌국사 조계종 의천 천태종',
#                '대마도정벌 이종무',
#                '일편단심 정몽주 목화씨는 문익점',
#                '해동공자 최충 삼국유사 일연',
#                '황금을 보기를 돌같이하라',
#                '최영 장군의 말씀 받들자',
#                '황희 정승 맹사성 과학 장영실',
#                '신숙주와 한명회 역사는 안다',
#                '십만 양병 이율곡 주리 이퇴계',
#                '신사임당 오죽헌',
#                '잘싸운다 곽재우 조헌 김시민',
#                '나라구한 이순신',
#                '태정태세문단세 사육신과 생육신',
#                '몸바쳐서 논개 행주치마 권율',
#                '번쩍번쩍 홍길동 의적 임꺽정',
#                '대쪽같은 삼학사 어사 박문수',
#                '삼년 공부 한석봉 단원 풍속도',
#                '방랑시인 김삿갓 지도 김정호',
#                '영조대왕 신문고 정조 규장각',
#                '목민심서 정약용',
#                '녹두장군 전봉준 순교 김대건',
#                '서화가무 황진이',
#                '못살겠다 홍경래 삼일천하 김옥균',
#                '안중근은 애국 이왕용은 매국',
#                '별헤는 밤 윤동주 종두 지석영',
#                '삼십삼인 손병희',
#                '만세만세 유관순 도산 안창호',
#                '어린이날 방정환',
#                '이수일과 심순애 장군의 아들 김두한',
#                '날자꾸나 이상 황소그림 중섭',
#                ' ',
#                ' ',
#                ' ',
#                ' ',
#                ' '
#          ]

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

def listen_print_loop(responses, First):
    if(First):
       
        present_point = 5
        First = False
        
    num_chars_printed = 0
    for response in responses:
        with open('conti_script_print.txt', 'r') as f:
            data = f.read()
        script_data = data.splitlines()
    
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript

        overwrite_chars = ' ' * (40)

        if not result.is_final:
            present_point, ratio = similarity3(script_data[present_point-5:present_point+5], transcript + overwrite_chars,present_point)
            sys.stdout.write(script_data[present_point] +overwrite_chars +'\r')
#             sys.stdout.write(transcript + overwrite_chars + '\r')
            sys.stdout.flush()
            
            num_chars_printed = len(transcript)
            
#             present_point = similarity2(script_data[present_point-5:present_point+5], transcript + overwrite_chars,present_point)

        else:
            #print(transcript + overwrite_chars)

            if re.search(r'\b(exit|quit)\b', transcript, re.I):
                print('Exiting..')
                break

            num_chars_printed = 0
            
            present_sentence = transcript + overwrite_chars
            present_point = similarity2(script_data[present_point-5:present_point+6], transcript + overwrite_chars,present_point)

            
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
    print(script[np.argmax(ratio)])
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
        print(script[np.argmax(ratio)] ,"                                         ")
        return np.argmax(ratio) + present_point - 5
    else:
        print('                                       ')
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
    
    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (speech.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)

        responses = client.streaming_recognize(streaming_config, requests)

        listen_print_loop(responses, First = True)

if __name__ == '__main__':
    main()