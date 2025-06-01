EXTENSION_DIR="$(HOME)"/.config/inkscape/extensions/
DYNALAB_DIR="$(EXTENSION_DIR)"/Dynalab/

PYTHON_FILES=$(wildcard src/*.py src/lib/*.py)

install:
	@test -d "$(EXTENSION_DIR)" || ( echo "le répertoire $(EXTENSION_DIR) n'existe pas" && false )
	mkdir -p  "$(DYNALAB_DIR)"
	cp -r src/ menus-en "$(DYNALAB_DIR)"

restore_svg:
	git restore svg_testfiles/*.svg

i18n: i18n/dynalab.pot i18n/fr.po src/locales/fr/LC_MESSAGES/dynalab.mo

i18n/dynalab.pot: $(PYTHON_FILES)
	xgettext -language=Python --from-code=UTF-8 -omit-header --indent --no-wrap --sort-by-file --join-existing --output $@ $?

i18n/fr.po: i18n/dynalab.pot
	msgmerge --quiet --update --indent --no-wrap --sort-by-file $@ $<

src/locales/fr/LC_MESSAGES/dynalab.mo: i18n/fr.po
	msgfmt $< -o $@

clean:
	rm -rf __pycache__
	rm -rf  "$(DYNALAB_DIR)"/*

.PHONY: clean install restore_test_svg i18n FORCE
