# v0.1 created by vinzenz aubry
# feel free to improve it, there's so much to do, such as implementing a better/local speech rec, improved setup and doing everything async in one script
# a medium link on how to immensly improve the timestamps: https://medium.com/@valdolyon/google-speech-to-text-work-on-your-timestamps-78abf7805fe2

import wave
import subprocess
from pydub import AudioSegment
import threading
import requests
import time
import os, shutil
import socket

from google.cloud import speech_v1
from google.cloud.speech_v1 import enums
client = speech_v1.SpeechClient()
import io

audioSnippetLength = 5.0 # in seconds (everything above 5 seconds bugs)

# params
beepOffsetStart = 50
beepOffsetEnd = 200

recordingPrefix = "recordings/"
preparedPrefix = "prepared/"
resultPrefix = "result/"

# inside
globalCounter = 0
_openNewFile = False

def cleanFolder(path):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

cleanFolder(recordingPrefix)
cleanFolder(preparedPrefix)
cleanFolder(resultPrefix)

def fileTimer():
    global globalCounter
    global _openNewFile
    threading.Timer(audioSnippetLength, fileTimer).start()
    globalCounter += 1
    _openNewFile = True
fileTimer()

stream_url = 'http://rtlberlin.hoerradar.de/spreeradio-live-mp3-128'
r = requests.get(stream_url, stream=True)

# def waitingFunction():
#     print('started sleeping 4 secs')
#     time.sleep(4.0)
#     print('finished sleeping')

def convertAudio(filename):
    filepath = recordingPrefix + filename + '.mp3'
    newFilePath = "prepared/" + filename + '.flac'
    subprocess.call(['avconv', '-i', filepath, '-y', '-ar', '16000', '-ac', '1', newFilePath, '-loglevel', 'quiet'])
    #subprocess.call(['avconv', '-i', filepath, '-y', '-ar', '16000', '-ac', '1', newFilePath,  '-threads', 'auto'])
    process_Censoring = threading.Thread(target=censorSound, args=(newFilePath, filename,))
    process_Censoring.start()

def censorSound(local_file_path, filename):
    print('called censoring:')
    print(local_file_path, filename)
    # The language of the supplied audio
    language_code = "de-DE"
    enable_word_time_offsets = True

    # Sample rate in Hertz of the audio data sent
    sample_rate_hertz = 16000

    # Encoding of audio data sent. This sample sets this explicitly.
    # This field is optional for FLAC and WAV audio formats.
    encoding = enums.RecognitionConfig.AudioEncoding.FLAC
    config = {
        "enable_word_time_offsets": enable_word_time_offsets,
        "language_code": language_code,
        "sample_rate_hertz": sample_rate_hertz,
        "encoding": encoding,
    }
    with io.open(local_file_path, "rb") as f:
        content = f.read()
    audio = {"content": content}

    response = client.recognize(config, audio)
    for result in response.results:
        #print(result)
        alternative = result.alternatives[0]
        # go through each word and check for corona. If there is corona, save starting and ending point in array
        coronaWordList = []        
        for word in alternative.words:
            sWord = word.word.lower()
            if sWord == "corona":
                startTime = word.start_time.seconds + (word.start_time.nanos / 1000000000)
                endTime = word.end_time.seconds + (word.end_time.nanos / 1000000000)
                coronaWordList.append([startTime, endTime])
            elif sWord == "korona":
                startTime = word.start_time.seconds + (word.start_time.nanos / 1000000000)
                endTime = word.end_time.seconds + (word.end_time.nanos / 1000000000)
                coronaWordList.append([startTime, endTime])
            elif sWord == "coroner":
                startTime = word.start_time.seconds + (word.start_time.nanos / 1000000000)
                endTime = word.end_time.seconds + (word.end_time.nanos / 1000000000)
                coronaWordList.append([startTime, endTime])


        print(u"Transcript: {}".format(alternative.transcript))
        print(coronaWordList)

        interimSound = AudioSegment.from_file(local_file_path)

        for timeframe in coronaWordList:
            startTimeMs = timeframe[0] * 1000
            endTimeMs = timeframe[1] * 1000

            # calculate times
            startTimeMsWOffset = startTimeMs - beepOffsetStart           
            endTimeMsWOffset = endTimeMs + beepOffsetEnd
            breakTime = endTimeMsWOffset - startTimeMsWOffset
            audioDuration = len(interimSound)

            #calculate empty + relaxing audio
            #silence = AudioSegment.silent(duration=breakTime) #no more silence
            relaxingAudio = AudioSegment.from_file("assets/relaxing.mp3")
            relaxingAudio = relaxingAudio[0:breakTime]
            #relaxingAudio = relaxingAudio.fade(to_gain=-120.0, end=0, duration=0.2) #this somehow increases the length...

            # split and rebuild video
            part1 = interimSound[0:startTimeMsWOffset]
            part3 = interimSound[endTimeMsWOffset:audioDuration]
            interimSound = part1 + relaxingAudio + part3

            #crossfade alternatice
            # combinedPre = part1.append(silence)
            # interimSound = combinedPre.append(part3)
        
        savingName = resultPrefix + filename + ".mp3"
        interimSound.export(savingName, format="mp3")


def audioWritingLoop():
    print('started new audiofile')
    global globalCounter
    global _openNewFile
    _openNewFile = False

    filename = 'stream' + str(globalCounter) 
    filepath = recordingPrefix + filename + '.mp3'
    
    with open(filepath, 'wb') as f:
        for block in r.iter_content(1024):
            f.write(block)
            if _openNewFile == True:
                process_audio = threading.Thread(target=convertAudio, args=(filename,))
                process_audio.start()
                audioWritingLoop()
                return
audioWritingLoop()
