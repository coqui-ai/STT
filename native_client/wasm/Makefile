NPM_TOOL           ?= npm
PROJECT_NAME       ?= stt-wasm
PROJECT_VERSION    ?= $(shell cat ../../training/coqui_stt_training/VERSION | tr -d '\n')

clean:
	rm -rf ./stt-wasm-*.tgz package.json
	rm -rf dist

package.json: package.json.in
	sed \
		-e 's/$$(PROJECT_NAME)/$(PROJECT_NAME)/' \
		-e 's/$$(PROJECT_VERSION)/$(PROJECT_VERSION)/' \
		package.json.in > package.json && cat package.json

dist:
	mkdir -p dist

dist/stt_wasm.js: dist ../../tensorflow/bazel-bin/native_client/stt_wasm_bindings/stt_wasm.js
	cp ../../tensorflow/bazel-bin/native_client/stt_wasm_bindings/stt_wasm.js dist

dist/stt_wasm.wasm: dist ../../tensorflow/bazel-bin/native_client/stt_wasm_bindings/stt_wasm.wasm
	cp ../../tensorflow/bazel-bin/native_client/stt_wasm_bindings/stt_wasm.wasm dist

dist/stt_wasm.worker.js: dist ../../tensorflow/bazel-bin/native_client/stt_wasm_bindings/stt_wasm.worker.js
	cp ../../tensorflow/bazel-bin/native_client/stt_wasm_bindings/stt_wasm.worker.js dist

build: package.json dist/stt_wasm.js dist/stt_wasm.wasm dist/stt_wasm.worker.js

pack: build
	${NPM_TOOL} pack
