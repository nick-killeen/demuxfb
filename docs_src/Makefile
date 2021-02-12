# Makefile for Sphinx documentation

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@echo "Use `website` or `websitewin` to build the demuxfb website."

.PHONY: help Makefile

# Build the html target, also adding ".nojekyll" so Github Pages will host
# underscore-prefixed content (we need the `_static` folder).
website: Makefile 
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	cp ".nojekyll" "$(BUILDDIR)/html/.nojekyll"
	cp -r "$(BUILDDIR)/html/." "./../docs"

# Windows version of "website" target.
websitewin: Makefile
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	copy ".nojekyll" "$(BUILDDIR)/html/.nojekyll"
	xcopy /i /y /s /e "$(BUILDDIR)/html/." "./../docs/"


# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
