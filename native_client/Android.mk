LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE    := stt-prebuilt
LOCAL_SRC_FILES := $(TFDIR)/bazel-bin/native_client/libstt.so
include $(PREBUILT_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE    := kenlm-prebuilt
LOCAL_SRC_FILES := $(TFDIR)/bazel-bin/native_client/libkenlm.so
include $(PREBUILT_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE    := tensorflowlite-prebuilt
LOCAL_SRC_FILES := $(TFDIR)/bazel-bin/tensorflow/lite/libtensorflowlite.so
include $(PREBUILT_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE    := tflitedelegates-prebuilt
LOCAL_SRC_FILES := $(TFDIR)/bazel-bin/native_client/libtflitedelegates.so
include $(PREBUILT_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_CPP_EXTENSION    := .cc .cxx .cpp
LOCAL_MODULE           := stt
LOCAL_SRC_FILES        := client.cc
LOCAL_SHARED_LIBRARIES := stt-prebuilt kenlm-prebuilt tensorflowlite-prebuilt tflitedelegates-prebuilt
LOCAL_LDFLAGS          := -Wl,--no-as-needed
include $(BUILD_EXECUTABLE)
