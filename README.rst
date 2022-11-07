🐸How to use the pre-trained model to simply run inference
---------------
 

🐸Download trained Coqui STT models and run the inference on it. Though the old README file has told us how to do it, but I still get some errors in the process. And I find the guidance lack of picture example and error-fixed solution, so I create the new README file just to guide people facing the same error as me.


* You can use the 🐸STT Model Manager by following these steps.
      # Create a virtual environment

         $ python3 -m venv venv-stt
         
         $ source venv-stt/bin/activate

      # Install 🐸STT model manager

         $ python -m pip install -U pip
          
         $ python -m pip install coqui-stt-model-manager

      # Run the model manager. A browser tab will open and you can then download and test models from the Model Zoo.

         $ stt-model-manager

      # Problem occurs when I use this method:
      
         *When using the provided way to create virtual environment, it can not find the bin file. So I change to use the mkvirtualenv
         *After creating the enviroment, error still occurs when I want to download STT manager

.. |doc-img| image:: https://github.com/ZhengkunMei/STT/blob/main/images/virtual%20environment.png
   :target: https://github.com/ZhengkunMei/STT/blob/main/images/virtual%20environment.png
   :alt: Documentation

         
.. |covenant-img| image:: https://github.com/ZhengkunMei/STT/blob/main/images/STT%20manager%20(2).png
   :target: https://github.com/ZhengkunMei/STT/blob/main/images/STT%20manager%20(2).png
   :alt: Contributor Covenant


        
|doc-img| |covenant-img| 




* If you face the same error as me, you can choose the second way to get the model

         *Using `STT model <https://coqui.ai/models/>`_ to download your model



* Then installing the stt to virtual environment

         *(coqui-stt-venv)$ python -m pip install -U pip && python -m pip install stt
         
* Use the command below to test your inference

         *(coqui-stt-venv)$ stt --model model.tflite --scorer huge-vocabulary.scorer --audio my_audio_file.wav


* SoX lacking error and its solution

         *When we use the last command to run the model, there is an error showing we did not install the SoX
         *Solution and result: the audio file need to be 16000Hz instead of 44100Hz, so I record my own voice "Hello world" and test it.
         *The result is a little bit different than I expected but still close to it
.. |doc-img| image:: https://github.com/ZhengkunMei/STT/blob/main/images/output.png
   :target: https://github.com/ZhengkunMei/STT/blob/main/images/output.png
   :alt: Documentation        
|doc-img|
