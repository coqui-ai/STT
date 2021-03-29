# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = "Coqui STT"
SOURCEDIR     = .
BUILDDIR      = .build

PIP_INSTALL   ?= python3 -m pip install

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help python-reqs

python-reqs: requirements.txt
	$(PIP_INSTALL) -r requirements.txt

submodule:
	git submodule update --init --remote -- examples || true

# Add submodule update dependency to Sphinx's "html" target
html: Makefile submodule python-reqs
	@PATH=$$HOME/.local/bin:`pwd`/../node_modules/.bin/:$$PATH \
	     $(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

dist: html
	cd $(BUILDDIR)/html/ && zip -r9 ../../html.zip *
