STT_REPO ?= https://github.com/coqui-ai/STT.git
STT_SHA  ?= origin/main

Dockerfile%: Dockerfile%.tmpl
	sed \
		-e "s|#STT_REPO#|$(STT_REPO)|g" \
		-e "s|#STT_SHA#|$(STT_SHA)|g" \
		< $< > $@
