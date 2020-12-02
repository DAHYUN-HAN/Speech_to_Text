#!/usr/bin/env python

# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Google Cloud Speech API sample application using the streaming API.
Example usage:
    python transcribe_streaming.py resources/audio.raw
"""

import argparse
import numpy as np

# [START speech_transcribe_streaming]
def transcribe_streaming(stream_file):
    """Streams transcription of the given audio file."""
    import io
    from google.cloud import speech

    client = speech.SpeechClient()

    # [START speech_python_migration_streaming_request]
    with io.open(stream_file, "rb") as audio_file:
        content = audio_file.read()
        
    with io.open('pause2.wav', "rb") as audio_file:
        pause = audio_file.read()

    # In practice, stream should be a generator yielding chunks of audio data.
    stream = [content]    
    print(len(stream[0]))
    for chunk in stream:
        a = np.frombuffer(chunk, np.int16)
    
#     x = 0
#     sum = 0
#     count = 0
#     check = True
#     new_content = content
#     stream = [content]
# #     print(len(a))
#     for i in range(len(a)-22):
#         index = i + 22
#         if(abs(a[index]) < 1000) :
#             sum = sum + 1
#             if(sum > 8000):
#                 if(check):
#                     check = False
#                     print(i)
#                     point = (index-11)*2 + (24000*count)
#                     new_content = new_content[44:point] + (new_content[point-8000:point]*3) + new_content[point:len(new_content)]
#                     count = count +1
                              
#         else:
#             sum = 0
#             check = True
# #         with open('kkk.txt', 'a') as f:
# #             f.writelines(str(sum)+'\n')
    
#     print(len(stream[0]))
#     content = new_content
    stream = [content]
    print(len(stream[0]))
    for chunk in stream:
        a = np.frombuffer(chunk, np.int16)
        with open('a.txt', 'w') as f:
            for line in a:
                f.writelines(str(line)+'\n')

    requests = (
        speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in stream
    )

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ko-KR",
    )

    streaming_config = speech.StreamingRecognitionConfig(config=config)

    # streaming_recognize returns a generator.
    # [START speech_python_migration_streaming_response]
    responses = client.streaming_recognize(
        config=streaming_config,
        requests=requests,
    )
    # [END speech_python_migration_streaming_request]
    
    for response in responses:
        # Once the transcription has settled, the first result will contain the
        # is_final result. The other results will be for subsequent portions of
        # the audio.
        for result in response.results:
            print("Finished: {}".format(result.is_final))
            print("Stability: {}".format(result.stability))
            alternatives = result.alternatives
            # The alternatives are ordered from most likely to least.
            for alternative in alternatives:
                print("Confidence: {}".format(alternative.confidence))
                print(u"Transcript: {}".format(alternative.transcript))
    # [END speech_python_migration_streaming_response]


# [END speech_transcribe_streaming]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("stream", help="File to stream to the API")
    args = parser.parse_args()
    transcribe_streaming(args.stream)