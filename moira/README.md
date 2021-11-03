## Evaluation of Coqui STT on New Voice Data

In this directory we are running and evaluating the Coqui STT system on a set of English voice data. 

The data consists of 286 audio files in wav form, containing quotes of Moira, a character from the multiplayer team-based first-person shooter game Overwatch. 

The audio files, along with a csv file that contains for each wav file the text of its audio, can be downloaded from the following link: https://drive.google.com/drive/folders/1nqQyZBaVbXDly6lntzY-Z0WkRyaZESlH?usp=sharing 

The pretrained model we use is the English STT v1.0.0 (Large Vocabulary) and it is available in the directory "model".

The evaluation is done by calculating the overall Word Error Rate.

### Running the code

To run the evaluation first install the requirements:

```shell
pip install -r moira/requirements.txt
```
Then get from https://drive.google.com/drive/folders/1nqQyZBaVbXDly6lntzY-Z0WkRyaZESlH?usp=sharing 
the wav files and place them in a directory /moira/wavs. From the same link take also the file "moira_quote_index.csv" and place it in /moira.

Then go to the directory /moira and execute the evaluation script:

```shell
cd moira
python stt_moira
```
The script takes the wav file of each quote and uses the stt model to infer its text. Then it compares the inferred text with the actual text (after some preprocessing) and calculates the corresponding Word  Error Rate. In the end it calculates the overall Word Error Rate.