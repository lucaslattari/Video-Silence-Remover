# -*- coding: utf-8 -*-
import os, os.path
import sys
import shutil
import glob
from argparse import ArgumentParser
from moviepy import config_defaults
from load_im import get_image_magick_executable

# define o caminho do imagehack em runtime antes de importar o moviepy apos
config_defaults.IMAGEMAGICK_BINARY = get_image_magick_executable()

from moviepy.editor import *
from pydub import AudioSegment
from pydub.utils import *
from tqdm import tqdm
from termcolor import colored

def identifySilenceClips(videoFilename, rmsOfSilence, timeOfSilenceInSeconds, debug):
    fileExtension = videoFilename.split(".")
    audioFile = AudioSegment.from_file(videoFilename, fileExtension[1])
    videoFile = VideoFileClip(videoFilename)

    sizeOfEachChunk = 200.0
    chunksOfAudio = make_chunks(audioFile, sizeOfEachChunk)
    currentTime = 0.0
    startSilence = False
    fileCounter = 0

    silenceToRemoveTxt = open("silenceToRemove.txt", "w")
    if(debug):
        silenceFileTxt = open("log.txt", "w")

    it = 0
    listOfClipsToCombine = []
    print(colored("Searching intervals of silence throughout the video", "green"))

    for chunk in tqdm(chunksOfAudio):
        if(chunk.rms < rmsOfSilence and startSilence == False):
            #detecta um chunk que começa com silêncio
            startSilenceClipTime = currentTime
            startSilence = True
            if(debug):
                silenceFileTxt.write(": " + str(round(currentTime, 2)) + ":" + str(chunk.rms) + ":" + str(round(chunk.dBFS, 2)) + "\n")
        elif(chunk.rms > rmsOfSilence and startSilence == True and startSilenceClipTime < currentTime - timeOfSilenceInSeconds):
            #achou o fim de um chunk
            startSilenceClipTime += (sizeOfEachChunk / 1000.0)
            endSilenceClipTime = currentTime - (sizeOfEachChunk / 1000.0)
            silenceClip = videoFile.subclip(startSilenceClipTime, endSilenceClipTime)
            silenceFilename = "silence" + str(fileCounter) + ".mp4"
            textClip = TextClip(silenceFilename, fontsize = 80)
            compClip = CompositeVideoClip([silenceClip, textClip]).set_duration(endSilenceClipTime - startSilenceClipTime)
            if(debug and not os.path.exists(silenceFilename)):
                compClip.write_videofile(silenceFilename, logger = None)
            listOfClipsToCombine.append(compClip)

            startSilence = False
            fileCounter += 1
            if(debug):
                silenceFileTxt.write(silenceFilename + "\n")
            silenceToRemoveTxt.write(silenceFilename + ":" + str(startSilenceClipTime) + ":" + str(endSilenceClipTime) + "\n")
        elif(chunk.rms > rmsOfSilence and startSilence == True):
            #achou um chunk de exatamente x segundos, sendo x o tamanho do chunk. nesse caso ignora
            startSilence = False
            if(debug):
                silenceFileTxt.write("Interrompido: " + str(round(currentTime, 2)) + ":" + str(chunk.rms) + ":" + str(round(chunk.dBFS, 2)) + "\n")
        elif(it == len(chunksOfAudio) - 1 and startSilenceClipTime < currentTime - timeOfSilenceInSeconds):
            #última iteração
            if startSilence == True:
                endSilenceClipTime = currentTime - (sizeOfEachChunk / 1000.0)
                silenceClip = videoFile.subclip(startSilenceClipTime)
                silenceFilename = "silence" + str(fileCounter) + ".mp4"
                textClip = TextClip(silenceFilename, fontsize = 80)
                compClip = CompositeVideoClip([silenceClip, textClip]).set_duration(endSilenceClipTime - startSilenceClipTime)
                listOfClipsToCombine.append(compClip)

                if(debug and not os.path.exists(silenceFilename)):
                    compClip.write_videofile(silenceFilename, logger = None)
                if(debug):
                    silenceFileTxt.write("fim: " + silenceFilename)
                silenceToRemoveTxt.write(silenceFilename + ":" + str(startSilenceClipTime) + ":" + str(endSilenceClipTime))
        elif(startSilence == True):
            #fins de debug
            if(debug):
                silenceFileTxt.write(str(round(currentTime, 2)) + ":" + str(chunk.rms) + ":" + str(round(chunk.dBFS, 2)) + "\n")

        currentTime += round(sizeOfEachChunk / 1000.0, 2)
        it += 1

    if(not os.path.exists("silence.mp4") and debug):
        silenceClips = concatenate_videoclips(listOfClipsToCombine)
        silenceClips.write_videofile("silence.mp4")
        silenceClips.close()

    if(debug):
        silenceFileTxt.close()
    silenceToRemoveTxt.close()
    videoFile.close()

    #if os.path.exists("silenceToRemoveCOPY.txt") == False:
    #    shutil.copyfile("silenceToRemove.txt", "silenceToRemoveCOPY.txt")

def trimSilence(videoFilename, txtFile, debug = True):
    silenceToRemoveFile = open(txtFile, "r")
    videoFile = VideoFileClip(videoFilename)

    print(colored("Trimming intervals of silence of the video...", "green"))
    firstIt = True
    listOfClipsToCombine = []
    i = 0
    startTime = 0.0
    endTime = 0.0
    for line in list(silenceToRemoveFile):
        if line[0] == "#":
            continue

        file, startTime, endTime = line.rstrip().split(":")
        startTime = float(startTime)
        endTime = float(endTime)

        if(startTime == 0.0 and firstIt == True):
            firstIt = False
            lastEndTime = endTime
        elif(firstIt == True):
            clip = videoFile.subclip(0, startTime)
            listOfClipsToCombine.append(clip)
            if debug:
                filename = "clip" + str(i) + ".mp4"
                clip.write_videofile(filename)
            lastEndTime = endTime
            firstIt = False
        else:
            clip = videoFile.subclip(lastEndTime, startTime)
            listOfClipsToCombine.append(clip)
            if debug:
                filename = "clip" + str(i) + ".mp4"
                clip.write_videofile(filename)
            lastEndTime = endTime
        i += 1

    #add the end
    clip = videoFile.subclip(endTime, float(videoFile.duration))
    listOfClipsToCombine.append(clip)
    if debug:
        filename = "clip" + str(i) + ".mp4"
        clip.write_videofile(filename)

    finalVideoClips = concatenate_videoclips(listOfClipsToCombine)
    finalVideoClips.write_videofile("final.mp4")
    finalVideoClips.close()

    videoFile.close()
    silenceToRemoveFile.close()

def deleteTempFiles():
    for file in os.listdir(os.getcwd()):
        if file.endswith("silenceToRemove.txt"):
            os.remove(file)
        if file.endswith("silenceToRemoveCOPY.txt"):
            os.remove(file)
        if file.endswith("log.txt"):
            os.remove(file)
        if file.endswith(".mp3"):
            os.remove(file)
        if file.endswith(".mp4"):
            if "clip" in file:
                os.remove(file)
            if "silence" in file:
                os.remove(file)

def parse_args():
    parser = ArgumentParser(description = 'Remove all sections with silence')
    parser.add_argument('file', help = 'Video file path')
    parser.add_argument('-r', action = 'store', dest = 'rs', type = int, default = 900, required = False,
                        help = 'Threshold that marks the measure of silence')
    parser.add_argument('-t', action = 'store', dest = 'ts', type = float, default = 2.0, required = False,
                        help = 'Minimum silence time in seconds')
    parser.add_argument('--d', action = 'store_true', dest = 'debug', required = False, help = 'Debug mode')

    return parser.parse_args()

def main():
    arguments = parse_args()

    print("Temporary files have been deleted")
    deleteTempFiles()

    if not os.path.exists(arguments.file):
        print(f'{arguments.file} not found')
        return

    identifySilenceClips(arguments.file, arguments.rs, arguments.ts, debug = arguments.debug)

    #essa função abaixo clipa o vídeo original passado por parâmetro de acordo com a informação de silêncio no arquivo de log
    trimSilence(arguments.file, "silenceToRemove.txt", debug = arguments.debug)

if __name__ == "__main__":
    main()
