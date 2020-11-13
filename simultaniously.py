# coding:utf-8
from __future__ import print_function
import cv2  #导入opencv包
import time
import sys
import os
from path import Path
from pyaudio import PyAudio, paInt16
import numpy as np
from datetime import datetime
import wave
from multiprocessing import Process, Queue


class recorder:
    NUM_SAMPLES = 500  #pyaudio内置缓冲大小 2000
    SAMPLING_RATE = 16000  #取样频率 8000
    LEVEL = 0  #声音保存的阈值
    COUNT_NUM = 20  #NUM_SAMPLES个取样之内出现COUNT_NUM个大于LEVEL的取样则记录声音
    SAVE_LENGTH = 8  #声音记录的最小长度：SAVE_LENGTH * NUM_SAMPLES 个取样
    # TIME_COUNT = 100000  #录音时间，单位s

    Voice_String = []

    def savewav(self, filename):
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(self.SAMPLING_RATE)
        wf.writeframes(np.array(self.Voice_String).tostring())
        # wf.writeframes(self.Voice_String.decode())
        wf.close()

    def recorder(self, se_sign, save_sign):
        pa = PyAudio()
        stream = pa.open(format=paInt16,
                         channels=1,
                         rate=self.SAMPLING_RATE,
                         input=True,
                         frames_per_buffer=self.NUM_SAMPLES)
        save_count = 0
        save_buffer = []
        # time_count = self.TIME_COUNT
        print('Start record audio.')
        if se_sign.get(True) == 'start':
            pass
        while True:
            # 读入NUM_SAMPLES个取样
            string_audio_data = stream.read(self.NUM_SAMPLES)
            # 将读入的数据转换为数组
            audio_data = np.fromstring(string_audio_data, dtype=np.short)
            # 计算大于LEVEL的取样的个数
            large_sample_count = np.sum(audio_data > self.LEVEL)
            # print('Volume: ', np.max(audio_data))
            # 如果个数大于COUNT_NUM，则至少保存SAVE_LENGTH个块
            if large_sample_count > self.COUNT_NUM:
                save_count = self.SAVE_LENGTH
            else:
                save_count -= 1

            if save_count < 0:
                save_count = 0

            if save_count > 0:
                # 将要保存的数据存放到save_buffer中
                save_buffer.append(string_audio_data)
            if se_sign.empty() == False or 0xFF == 27:
                if len(save_buffer) > 0:
                    self.Voice_String = save_buffer
                    save_buffer = []
                    print("Record a piece of voice successfully!")
                    return True
                else:
                    return False


def start_record_video(name, se_sign, save_sign):
    piece_id = 0
    video = cv2.VideoCapture(0)  #打开摄像头
    fourcc = cv2.VideoWriter_fourcc(*'XVID')  #视频存储的格式
    fps = video.get(cv2.CAP_PROP_FPS)  #帧率
    #视频的宽高
    size = (int(video.get(cv2.CAP_PROP_FRAME_WIDTH)), \
            int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    print('Video\'s fps: ', fps)
    print('Video win\'s size: ', size)

    out = cv2.VideoWriter('video_' + name + '.avi', fourcc, fps, size)  #视频存储

    se_sign.put('start')
    print('Start record video.')
    while out.isOpened():
        ret, img = video.read()  #开始使用摄像头读数据，返回ret为true，img为读的图像
        if ret is False:  #ret为false则关闭
            exit()
        cv2.namedWindow('video', cv2.WINDOW_AUTOSIZE)  #创建一个名为video的窗口
        cv2.imshow('video', img)  #将捕捉到的图像在video窗口显示


        #按esc键退出程序
        if cv2.waitKey(1) & 0xFF == 27:
            se_sign.put('end')
            video.release()  #关闭摄像头
            out.release()
            video.release()
            print("Record a piece of video successfully!")
            break
    cv2.destroyAllWindows()


def start_record_audio(name, se_sign, save_sign):
    r = recorder()
    r.recorder(se_sign, save_sign)
    r.savewav('audio_' + name + ".wav")


def start_record_all():
    name = time.strftime('%Y%m%d-%H%M%S')
    se_sign = Queue()
    save_sign = Queue()

    p_video = Process(target=start_record_video, args=(
        name,
        se_sign,
        save_sign,
    ))
    p_audio = Process(target=start_record_audio, args=(
        name,
        se_sign,
        save_sign,
    ))
    p_video.start()
    p_audio.start()
    # p_video.join()
    # p_audio.join()
    return name


if __name__ == '__main__':
    start_record_all()