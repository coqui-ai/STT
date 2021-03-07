
Javadoc for Sphinx
==================

This code is only here for reference for documentation generation.

To update, please install SWIG (4.0 at least) and then run from native_client/java:

.. code-block::

   swig -c++ -java -doxygen -package ai.coqui.libstt -outdir libstt/src/main/java/ai/coqui/libstt_doc -o jni/stt_wrap.cpp jni/stt.i
