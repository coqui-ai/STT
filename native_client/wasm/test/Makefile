NPM_TOOL           	    ?= npm
TEST_PROJECT_NAME       ?= stt-wasm
TEST_PROJECT_VERSION    ?= $(shell cat ../../../training/coqui_stt_training/VERSION | tr -d '\n')

clean:
	rm -rf package.json package-lock.json
	rm -rf node_modules

package.json: package.json.in
	cp package.json.in package.json

install-dependencies: package.json
	${NPM_TOOL} install

install-stt-wasm: package.json
	${NPM_TOOL} install ${CI_TMP_DIR}/${TEST_PROJECT_NAME}-${TEST_PROJECT_VERSION}.tgz

test: install-dependencies install-stt-wasm
	${NPM_TOOL} run test
