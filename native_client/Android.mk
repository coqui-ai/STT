LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE    := stt-prebuilt
LOCAL_SRC_FILES := $(ROOT_DIR)/bazel-bin/native_client/libstt.so
include $(PREBUILT_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_CPP_EXTENSION    := .cc .cxx .cpp
LOCAL_MODULE           := stt
LOCAL_SRC_FILES        := client.cc
LOCAL_SHARED_LIBRARIES := stt-prebuilt
LOCAL_LDFLAGS          := -Wl,--no-as-needed
include $(BUILD_EXECUTABLE)
