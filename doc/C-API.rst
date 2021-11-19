.. _c-api:

C API
=====

.. toctree::
   :maxdepth: 2

   Structs

See also the list of error codes including descriptions for each error in :ref:`error-codes`.

.. doxygenfunction:: STT_CreateModel
   :project: stt-c

.. doxygenfunction:: STT_FreeModel
   :project: stt-c

.. doxygenfunction:: STT_EnableExternalScorer
   :project: stt-c

.. doxygenfunction:: STT_DisableExternalScorer
   :project: stt-c

.. doxygenfunction:: STT_AddHotWord
   :project: stt-c

.. doxygenfunction:: STT_EraseHotWord
   :project: stt-c

.. doxygenfunction:: STT_ClearHotWords
   :project: stt-c

.. doxygenfunction:: STT_SetScorerAlphaBeta
   :project: stt-c

.. doxygenfunction:: STT_GetModelSampleRate
   :project: stt-c

.. doxygenfunction:: STT_SpeechToText
   :project: stt-c

.. doxygenfunction:: STT_SpeechToTextWithMetadata
   :project: stt-c

.. doxygenfunction:: STT_CreateStream
   :project: stt-c

.. doxygenfunction:: STT_FeedAudioContent
   :project: stt-c

.. doxygenfunction:: STT_IntermediateDecode
   :project: stt-c

.. doxygenfunction:: STT_IntermediateDecodeWithMetadata
   :project: stt-c

.. doxygenfunction:: STT_FinishStream
   :project: stt-c

.. doxygenfunction:: STT_FinishStreamWithMetadata
   :project: stt-c

.. doxygenfunction:: STT_FreeStream
   :project: stt-c

.. doxygenfunction:: STT_FreeMetadata
   :project: stt-c

.. doxygenfunction:: STT_FreeString
   :project: stt-c

.. doxygenfunction:: STT_Version
   :project: stt-c
