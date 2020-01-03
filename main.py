import os
import sys
import shutil
import glob
from argparse import ArgumentParser
from moviepy.editor import *
from moviepy import config_defaults
from pydub import AudioSegment
from pydub.utils import *
from tqdm import tqdm
import subprocess
from termcolor import colored

from load_im import get_image_magick_executable

def install(package):
    subprocess.call([sys.executable, "-m", "pip", "install", package])

def upgrade(package):
    subprocess.call(['pip', "install", "--upgrade", package])

def installModule(package):
    install(package)
    upgrade(package)

def initializeMoviePy():
    installModule("moviepy")

def identifySilenceMomentsOfVideo(videoFilename, rmsOfSilence, timeOfSilenceInMilliseconds, debug):
    audioFile = AudioSegment.from_file(videoFilename, "mp4")
    videoFile = VideoFileClip(videoFilename)

    chunksOfAudio = make_chunks(audioFile, timeOfSilenceInMilliseconds)
    currentTime = 0.0
    startSilence = False
    fileCounter = 0

    silenceToRemoveTxt = open("silenceToRemove.txt", "w")
    if(debug):
        silenceFileTxt = open("log.txt", "w")
    it = 0
    listOfClipsToCombine = []
    print(colored("Buscando instantes de silêncio ao longo do vídeo...", "green"))
    for chunk in tqdm(chunksOfAudio):
        if(chunk.rms < rmsOfSilence and startSilence == False):
            #detecta um chunk que começa com silêncio
            startSilenceClipTime = currentTime
            startSilence = True
            if debug:
                silenceFileTxt.write("Começou: " + str(currentTime) + ":" + str(chunk.rms) + ":" + str(round(chunk.dBFS, 2)) + "\n")
        elif(chunk.rms > rmsOfSilence and startSilence == True and startSilenceClipTime < currentTime - 1.5):
            #achou o fim de um chunk que possui no mínimo 2x segundos, sendo x o tamanho do chunk
            endSilenceClipTime = currentTime - (timeOfSilenceInMilliseconds / 1000.0)
            silenceClip = videoFile.subclip(startSilenceClipTime, endSilenceClipTime)
            silenceFilename = "silence" + str(fileCounter) + ".mp4"
            textClip = TextClip(silenceFilename, fontsize = 80)
            compClip = CompositeVideoClip([silenceClip, textClip]).set_duration(endSilenceClipTime - startSilenceClipTime)
            if debug:
                if os.path.exists(silenceFilename) == False:
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
                silenceFileTxt.write("Interrompido: " + str(currentTime) + ":" + str(chunk.rms) + ":" + str(round(chunk.dBFS, 2)) + "\n")
        elif(it == len(chunksOfAudio) - 1):
            #última iteração
            if startSilence == True:
                endSilenceClipTime = currentTime - (timeOfSilenceInMilliseconds / 1000.0)
                silenceClip = videoFile.subclip(startSilenceClipTime)
                silenceFilename = "silence" + str(fileCounter) + ".mp4"
                textClip = TextClip(silenceFilename, fontsize = 80)
                compClip = CompositeVideoClip([silenceClip, textClip]).set_duration(endSilenceClipTime - startSilenceClipTime)
                if debug:
                    if os.path.exists(silenceFilename) == False:
                        compClip.write_videofile(silenceFilename, logger = None)
                listOfClipsToCombine.append(compClip)

                #silenceFileTxt.write("Final: " + str(currentTime) + ":" + str(chunk.rms) + ":" + str(round(chunk.dBFS, 2)) + "\n")
                if(debug):
                    silenceFileTxt.write(silenceFilename)
                silenceToRemoveTxt.write(silenceFilename + ":" + str(startSilenceClipTime) + ":" + str(endSilenceClipTime))
        elif(startSilence == True):
            #fins de debug
            if(debug):
                silenceFileTxt.write(str(currentTime) + ":" + str(chunk.rms) + ":" + str(round(chunk.dBFS, 2)) + "\n")

        currentTime += round(timeOfSilenceInMilliseconds / 1000.0, 2)
        it += 1

    if not os.path.exists("silence.mp4") and debug:
        silenceClips = concatenate_videoclips(listOfClipsToCombine)
        silenceClips.write_videofile("silence.mp4")
        silenceClips.close()

    if(debug):
        silenceFileTxt.close()
    silenceToRemoveTxt.close()
    videoFile.close()

    if os.path.exists("silenceToRemoveCOPY.txt") == False:
        shutil.copyfile("silenceToRemove.txt", "silenceToRemoveCOPY.txt")

def clipSilenceBasedOnTxtFile(videoFilename, txtFile, debug = True):
    silenceToRemoveFile = open(txtFile, "r")
    videoFile = VideoFileClip(videoFilename)

    print(colored("Recortando momentos de silêncio do vídeo...", "green"))
    firstIt = True
    listOfClipsToCombine = []
    i = 0
    for line in list(silenceToRemoveFile):
        if line[0] == "#":
            continue

        file, startTime, endTime = line.rstrip().split(":")
        startTime = float(startTime)
        endTime = float(endTime)

        filename = "clip" + str(i) + ".mp4"
        if(startTime == 0.0 and firstIt == True):
            firstIt = False
            lastEndTime = endTime
        elif(firstIt == True):
            #from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
            #ffmpeg_extract_subclip(videoFilename, 0, startTime, targetname=filename)
            clip = videoFile.subclip(0, startTime)
            listOfClipsToCombine.append(clip)
            if debug:
                clip.write_videofile(filename)
            lastEndTime = endTime
            firstIt = False
        else:
            #ffmpeg_extract_subclip(videoFilename, lastEndTime, startTime, targetname=filename)
            clip = videoFile.subclip(lastEndTime, startTime)
            listOfClipsToCombine.append(clip)
            if debug:
                clip.write_videofile(filename)
            lastEndTime = endTime
        i += 1

    totalClips = i

    if os.path.exists("original_without_silence.mp4") == False:
        finalVideoClips = concatenate_videoclips(listOfClipsToCombine)
        finalVideoClips.write_videofile("original_without_silence.mp4")
        finalVideoClips.close()

    videoFile.close()
    silenceToRemoveFile.close()

def deleteTempFiles():
    for file in os.listdir(os.getcwd()):
        if file.endswith(".txt"):
            os.remove(file)
        if file.endswith(".mp4"):
            if "clip" in file:
                os.remove(file)
            if "silence" in file:
                os.remove(file)


def parse_args():
    parser = ArgumentParser(description = 'Remove os pedaços silenciosos do video.')
    parser.add_argument('file', help = 'arquivo de vídeo mp4')
    parser.add_argument('-r', action = 'store', dest = 'rs', type = int, default = 900, required = False,
                        help = 'limiar que demarca intensidade de silêncio')
    parser.add_argument('-t', action = 'store', dest = 'ts', type = int, default = 250, required = False,
                        help = 'tempo mínimo de silêncio em milissegundos')
    parser.add_argument('--d', action = 'store_true', dest = 'debug', required = False, help = 'mode debug')
    
    return parser.parse_args()


def main():
    arguments = parse_args()
    
    if not os.path.exists(arguments.file):
        print(f'{arguments.file} não existe.')
        return
    
    #initializeMoviePy() # TODO: descomentar e adc flag no settings para só executar isso na 1a vez
	
	# define o caminho do imagehack em runtime
    config_defaults.IMAGEMAGICK_BINARY = get_image_magick_executable()
    
    identifySilenceMomentsOfVideo(arguments.file, arguments.rs, arguments.ts, debug = arguments.debug)

    #essa função abaixo clipa o vídeo original passado por parâmetro de acordo com a informação de silêncio no arquivo de log
    clipSilenceBasedOnTxtFile("pythonfazpramim1-2.mp4", "silenceToRemoveCOPY.txt", debug = arguments.debug)

    deleteTempFiles()


if __name__ == "__main__":
    main()
