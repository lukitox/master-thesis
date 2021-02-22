# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

PLANTUML := java -Djava.awt.headless=true -jar /home/y0065120/Dokumente/Software/plantuml/plantuml.jar -tsvg -failfast2

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

plantuml:
#	alias plantuml="/home/y0065120/Dokumente/Software/plantuml/plantuml.jar -tsvg -failfast2"
	$(PLANTUML) -psvg -o ../images/uml/ ./uml/*.uml
	
html: plantuml

umllatex:
	$(PLANTUML) -psvg -tlatex -o ../images/uml/ ./uml/*.uml