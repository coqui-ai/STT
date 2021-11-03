import wave
import shlex
import csv

import jiwer
import numpy as np
from stt import Model
import subprocess
from jiwer import wer

try:
    from shhlex import quote
except ImportError:
    from pipes import quote

# method to convert the samole rate of the input audio to the sample rate of the model
def convert_samplerate(audio_path, desired_sample_rate):
    sox_cmd = "sox {} --type raw --bits 16 --channels 1 --rate {} --encoding signed-integer --endian little --compression 0.0 --no-dither - ".format(
        quote(audio_path), desired_sample_rate
    )
    try:
        output = subprocess.check_output(shlex.split(sox_cmd), stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("SoX returned non-zero status: {}".format(e.stderr))
    except OSError as e:
        raise OSError(
            e.errno,
            "SoX not found, use {}hz files or install it: {}".format(
                desired_sample_rate, e.strerror
            ),
        )

    return desired_sample_rate, np.frombuffer(output, np.int16)

# a method that takes as input a model and an audio file and returns the text of the audio
def speech_to_text(model, audio_file):
    #Get the sample rate of the model
    desired_sample_rate = model.sampleRate()
    # Extract the audio from the audio file and resample it to the model's sample rate
    fin = wave.open(audio_file, "rb")
    fs_new, audio = convert_samplerate(audio_file, desired_sample_rate)
    fin.close()
    # Get the text of the audio
    text = model.stt(audio)
    return text

# a method that preprocesses text for more accurate comparison
def jiwer_transform(text):

    text = jiwer.ToLowerCase().process_string(text) # lower-case
    text = jiwer.SubstituteRegexes({r'\([^)]*\)':r''}).process_string(text) #remove text in parentheses
    text = jiwer.ExpandCommonEnglishContractions().process_string(text) # Expand contractions (e.g. "I'm" becomes "I am"
    text = jiwer.RemoveMultipleSpaces().process_string(text) # Remove multiple spaces
    text = jiwer.RemovePunctuation().process_string(text) # Remove punctuation
    text = jiwer.RemoveWhiteSpace(replace_by_space=True).process_string(text) # Remove redundant white spaces
    text = jiwer.Strip().process_string(text) # Strip tailing spaces

    return text

# A method that extracts the texts of a set of audio files and compares them with the actual texts
def evaluate_stt(model_file):

    # Load the pretrained model
    ds = Model(model_file)

    audio_texts = []
    recognized_texts = []

    with open('moira_quote_index.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader)
        count =0
        for row in csv_reader:
            count+=1

            # Get the actual audio text and preprocess it
            audio_text = row[0]
            transformed_audio_text = jiwer_transform(audio_text)
            audio_texts.append(transformed_audio_text)

            # Extract the text of the audio file using the pre-trained model and preprocess it
            audio_file = f"wavs/{row[1]}"
            recognized_text = speech_to_text(ds,audio_file)
            transformed_recognized_text = jiwer_transform(recognized_text)
            recognized_texts.append(transformed_recognized_text)

            # Calculate and print the Word Error Rate
            error = wer(transformed_audio_text, transformed_recognized_text)
            print(f"{count}. The audio with text '{audio_text}' is recognized by the  model as '{recognized_text}': WER = {error}" )

    # Calculate and print the overall Word Error Rate
    total_error = wer(audio_texts,recognized_texts)
    print(f"Overall Word Error Rate: {total_error}")


evaluate_stt("model/model.tflite")
