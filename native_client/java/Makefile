.PHONY: clean apk-clean

include ../definitions.mk

ARCHS := $(shell grep 'ABI_FILTERS' libstt/gradle.properties | cut -d'=' -f2 | sed -e 's/;/ /g')
GRADLE ?= ./gradlew

all: apk

clean: apk-clean
	rm -rf *.java jni/stt_wrap.cpp

apk-clean:
	$(GRADLE) clean

libs-clean:
	rm -fr libstt/libs/*/libstt.so

libstt/libs/%/libstt.so:
	-mkdir libstt/libs/$*/
	cp ${TFDIR}/bazel-out/$*-*/bin/native_client/libstt.so libstt/libs/$*/

apk: apk-clean bindings $(patsubst %,libstt/libs/%/libstt.so,$(ARCHS))
	$(GRADLE) build

maven-bundle: apk
	$(GRADLE) uploadArchives
	$(GRADLE) zipMavenArtifacts

bindings: clean ds-swig
	$(DS_SWIG_ENV) swig -c++ -java -package ai.coqui.libstt -outdir libstt/src/main/java/ai/coqui/libstt/ -o jni/stt_wrap.cpp jni/stt.i
