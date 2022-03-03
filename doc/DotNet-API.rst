.NET Framework
==============


STT Class
----------------

.. doxygenclass:: STTClient::STT
   :project: stt-dotnet
   :members:

STTStream Class
----------------------

.. doxygenclass:: STTClient::Models::STTStream
   :project: stt-dotnet
   :members:

ErrorCodes
----------

See also the main definition including descriptions for each error in :ref:`error-codes`.

.. doxygenenum:: STTClient::Enums::ErrorCodes
   :project: stt-dotnet

Metadata
--------

.. doxygenclass:: STTClient::Models::Metadata
   :project: stt-dotnet
   :members: Transcripts

CandidateTranscript
-------------------

.. doxygenclass:: STTClient::Models::CandidateTranscript
   :project: stt-dotnet
   :members: Tokens, Confidence

TokenMetadata
-------------

.. doxygenclass:: STTClient::Models::TokenMetadata
   :project: stt-dotnet
   :members: Text, Timestep, StartTime

STT Interface
--------------------

.. doxygeninterface:: STTClient::Interfaces::ISTT
   :project: stt-dotnet
   :members:
