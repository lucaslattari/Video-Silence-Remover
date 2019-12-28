import glob
from moviepy.editor import *
from pydub import AudioSegment
from pydub.utils import *
from tqdm import tqdm
import os

def identifySilenceMomentsOfVideo(videoFilename, rmsOfSilence, timeOfSilenceInMilliseconds, mode = "DEBUG"):
    audioFile = AudioSegment.from_file(videoFilename, "mp4")
    videoFile = VideoFileClip(videoFilename)

    chunksOfAudio = make_chunks(audioFile, timeOfSilenceInMilliseconds)
    currentTime = 0.0
    startSilence = False
    fileCounter = 0

    silenceToRemoveTxt = open("silenceToRemove.txt", "w")
    if(mode == "DEBUG"):
        silenceFileTxt = open("log.txt", "w")
    it = 0
    listOfClipsToCombine = []
    print("Buscando silêncio ao longo do vídeo...")
    for chunk in tqdm(chunksOfAudio):
        if(chunk.rms < rmsOfSilence and startSilence == False):
            #detecta um chunk que começa com silêncio
            startSilenceClipTime = currentTime
            startSilence = True
            if mode == "DEBUG":
                silenceFileTxt.write("Começou: " + str(currentTime) + ":" + str(chunk.rms) + ":" + str(chunk.dBFS) + "\n")
        elif(chunk.rms > rmsOfSilence and startSilence == True and startSilenceClipTime < currentTime - 1.5):
            #achou o fim de um chunk que possui no mínimo 2x segundos, sendo x o tamanho do chunk
            endSilenceClipTime = currentTime - (timeOfSilenceInMilliseconds / 1000.0)
            silenceClip = videoFile.subclip(startSilenceClipTime, endSilenceClipTime)
            silenceFilename = "silence" + str(fileCounter) + ".mp4"
            textClip = TextClip(silenceFilename, fontsize = 80)
            compClip = CompositeVideoClip([silenceClip, textClip]).set_duration(endSilenceClipTime - startSilenceClipTime)
            if mode == "DEBUG":
                if os.path.exists(silenceFilename) == False:
                    compClip.write_videofile(silenceFilename, logger = None)
                    compClip.close()
            listOfClipsToCombine.append(compClip)

            startSilence = False
            fileCounter += 1
            if(mode == "DEBUG"):
                silenceFileTxt.write(silenceFilename + "\n")
            silenceToRemoveTxt.write(silenceFilename + ":" + str(startSilenceClipTime) + ":" + str(endSilenceClipTime) + "\n")
        elif(chunk.rms > rmsOfSilence and startSilence == True):
            #achou um chunk de exatamente x segundos, sendo x o tamanho do chunk. nesse caso ignora
            startSilence = False
            if(mode == "DEBUG"):
                silenceFileTxt.write("Interrompido: " + str(currentTime) + ":" + str(chunk.rms) + ":" + str(chunk.dBFS) + "\n")
        elif(it == len(chunksOfAudio) - 1):
            #última iteração
            if startSilence == True:
                endSilenceClipTime = currentTime - (timeOfSilenceInMilliseconds / 1000.0)
                silenceClip = videoFile.subclip(startSilenceClipTime)
                silenceFilename = "silence" + str(fileCounter) + ".mp4"
                textClip = TextClip(silenceFilename, fontsize = 80)
                compClip = CompositeVideoClip([silenceClip, textClip]).set_duration(endSilenceClipTime - startSilenceClipTime)
                if mode == "DEBUG":
                    if os.path.exists(silenceFilename) == False:
                        compClip.write_videofile(silenceFilename, logger = None)
                        compClip.close()
                listOfClipsToCombine.append(compClip)

                #silenceFileTxt.write("Final: " + str(currentTime) + ":" + str(chunk.rms) + ":" + str(chunk.dBFS) + "\n")
                if(mode == "DEBUG"):
                    silenceFileTxt.write(silenceFilename)
                silenceToRemoveTxt.write(silenceFilename + ":" + str(startSilenceClipTime) + ":" + str(endSilenceClipTime) + "\n")
        elif(startSilence == True):
            #fins de debug
            if(mode == "DEBUG"):
                silenceFileTxt.write(str(currentTime) + ":" + str(chunk.rms) + ":" + str(chunk.dBFS) + "\n")

        currentTime += timeOfSilenceInMilliseconds / 1000.0
        it += 1
    if os.path.exists("silence.mp4") == False:
        silenceClips = concatenate_videoclips(listOfClipsToCombine)
        silenceClips.write_videofile("silence.mp4")
        silenceClips.close()

        #remove clipes de silêncio temporários
        if mode == "DEBUG":
            for i in range(fileCounter):
                silenceFilename = "silence" + str(i) + ".mp4"
                os.remove(silenceFilename)

    if(mode == "DEBUG"):
        silenceFileTxt.close()
    silenceToRemoveTxt.close()
    videoFile.close()

def clipSilenceBasedOnTxtFile(videoFilename, txtFile):
    silenceToRemoveFile = open("silenceToRemove.txt", "r")
    print(videoFilename)
    videoFile = VideoFileClip(videoFilename)

    print("Recortando momentos de silêncio do vídeo...")
    firstIt = True
    listOfClipsToCombine = []
    i = 0
    for line in list(silenceToRemoveFile):
        file, startTime, endTime = line.rstrip().split(":")
        startTime = float(startTime)
        endTime = float(endTime)

        from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
        filename = "clip" + str(i) + ".mp4"
        if(startTime == 0.0 and firstIt == True):
            firstIt = False
            lastEndTime = endTime
        elif(firstIt == True):
            #ffmpeg_extract_subclip(videoFilename, 0, startTime, targetname=filename)
            clip = videoFile.subclip(0, startTime)
            listOfClipsToCombine.append(clip)
            if mode == "DEBUG":
                clip.write_videofile(filename)
                clip.close()
            lastEndTime = endTime
            firstIt = False
        else:
            #ffmpeg_extract_subclip(videoFilename, lastEndTime, startTime, targetname=filename)
            clip = videoFile.subclip(lastEndTime, startTime)
            listOfClipsToCombine.append(clip)
            if mode == "DEBUG":
                clip.write_videofile(filename)
                clip.close()
            lastEndTime = endTime
        i += 1

    totalClips = i

    if os.path.exists("original_without_silence.mp4") == False:
        finalVideoClips = concatenate_videoclips(listOfClipsToCombine)
        finalVideoClips.write_videofile("original_without_silence.mp4")
        finalVideoClips.close()

        #remove clipes de silêncio temporários
        if mode == "DEBUG":
            for i in range(fileCounter):
                silenceFilename = "clip" + str(i) + ".mp4"
                os.remove(silenceFilename)

    videoFile.close()
    silenceToRemoveFile.close()

def main():
    #passe aqui o nome do arquivo de vídeo, o limiar que demarca intensidade de silêncio (900 é um bom valor) e oq seria uma boa
    #duração de silêncio (coloquei 250 ms alí)
    identifySilenceMomentsOfVideo("pythonfazpramim1-2.mp4", 900, 250, "DEBUG")
    #essa função abaixo clipa o vídeo original passado por parâmetro de acordo com a informação de silêncio no arquivo de log
    clipSilenceBasedOnTxtFile("pythonfazpramim1-2.mp4", "silenceToRemove.txt")

if __name__ == "__main__":
    main()
