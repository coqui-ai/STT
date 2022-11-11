ASSIGNMENT 7
-----------
*by Ellemijn Galjaard*

This project is forked from the [Coqui SST GitHub model](https://github.com/coqui-ai/STT).  
You can view the original documentation under ``README.rst``.

About this Project
------------
- The project is located under the directory ``assignment7_ellemijn``. It runs a [COQUI STT model](https://github.com/coqui-ai/STT/blob/main/notebooks/train_personal_model_with_common_voice.ipynb) and fine-tunes it on a self-recorded open-source [CommonVoice](https://commonvoice.mozilla.org/) dataset containing 230 .mp3 files. 

- **To run this project**, download or clone this github repository, and execute the notebook ``assignment7_ellemijn/fine-tune_model.ipynb``.  
This directory also contains two .txt files with results from an earlier run of the pre-trained model and fine-tuned model on the self-recorded CommonVoice test set.

- The files and metadata are downloaded via [gdown](https://pypi.org/project/gdown/) within the notebook itself. This was done so users are not required to mount their Drive to access this file when working in a Colab environment. This means that you only need to run the notebook (on Colab or locally) and have a working internet connection to run this project.  

- No ``requirements.txt`` file is provided, as the packages are installed within the notebook itself.