# For more information about using CMake with Android Studio, read the
# documentation: https://d.android.com/studio/projects/add-native-code.html

# Sets the minimum version of CMake required to build the native library.

cmake_minimum_required(VERSION 3.4.1)

# Creates and names a library, sets it as either STATIC
# or SHARED, and provides the relative paths to its source code.
# You can define multiple libraries, and CMake builds them for you.
# Gradle automatically packages shared libraries with your APK.

add_library( # Sets the name of the library.
             stt-jni

             # Sets the library as a shared library.
             SHARED

             # Provides a relative path to your source file(s).
             ../jni/stt_wrap.cpp )

add_library(stt-lib SHARED IMPORTED)
set_target_properties(stt-lib PROPERTIES
    IMPORTED_LOCATION ${CMAKE_SOURCE_DIR}/libs/${ANDROID_ABI}/libstt.so)

add_library(kenlm-lib SHARED IMPORTED)
set_target_properties(kenlm-lib PROPERTIES
    IMPORTED_LOCATION ${CMAKE_SOURCE_DIR}/libs/${ANDROID_ABI}/libkenlm.so)

add_library(tensorflowlite-lib SHARED IMPORTED)
set_target_properties(tensorflowlite-lib PROPERTIES
    IMPORTED_LOCATION ${CMAKE_SOURCE_DIR}/libs/${ANDROID_ABI}/libtensorflowlite.so)

add_library(tflitedelegates-lib SHARED IMPORTED)
set_target_properties(tflitedelegates-lib PROPERTIES
    IMPORTED_LOCATION ${CMAKE_SOURCE_DIR}/libs/${ANDROID_ABI}/libtflitedelegates.so)

add_custom_command(TARGET stt-jni POST_BUILD
             COMMAND ${CMAKE_COMMAND} -E copy
             ${CMAKE_SOURCE_DIR}/libs/${ANDROID_ABI}/libstt.so
             ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}/libstt.so)

add_custom_command(TARGET stt-jni POST_BUILD
             COMMAND ${CMAKE_COMMAND} -E copy
             ${CMAKE_SOURCE_DIR}/libs/${ANDROID_ABI}/libkenlm.so
             ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}/libkenlm.so)

add_custom_command(TARGET stt-jni POST_BUILD
             COMMAND ${CMAKE_COMMAND} -E copy
             ${CMAKE_SOURCE_DIR}/libs/${ANDROID_ABI}/libtensorflowlite.so
             ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}/libtensorflowlite.so)

add_custom_command(TARGET stt-jni POST_BUILD
             COMMAND ${CMAKE_COMMAND} -E copy
             ${CMAKE_SOURCE_DIR}/libs/${ANDROID_ABI}/libtflitedelegates.so
             ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}/libtflitedelegates.so)

# Searches for a specified prebuilt library and stores the path as a
# variable. Because CMake includes system libraries in the search path by
# default, you only need to specify the name of the public NDK library
# you want to add. CMake verifies that the library exists before
# completing its build.

find_library( # Sets the name of the path variable.
              log-lib

              # Specifies the name of the NDK library that
              # you want CMake to locate.
              log )

# Specifies libraries CMake should link to your target library. You
# can link multiple libraries, such as libraries you define in this
# build script, prebuilt third-party libraries, or system libraries.

target_link_libraries( # Specifies the target library.
                       stt-jni

                       stt-lib

                       # Links the target library to the log library
                       # included in the NDK.
                       ${log-lib} )
