EXTENSION_DIR="$(HOME)"/.config/inkscape/extensions/

PYTHON_FILES=$(wildcard Dynalab/src/*.py Dynalab/src/lib/*.py)
MENU_FILES=$(wildcard Dynalab/menus-*/*.inx)

LANG ?= en

install: version
	@test -d "$(EXTENSION_DIR)" || ( echo "le répertoire $(EXTENSION_DIR) n'existe pas" && false )
	mkdir -p "$(EXTENSION_DIR)"/Dynalab
	cp -ur Dynalab/src Dynalab/menus-$(LANG) "$(EXTENSION_DIR)"/Dynalab/

version: FORCE
	printf 'tag = "%s"\n' "$$(git describe --always --dirty)" > Dynalab/src/version.py

archive: dynalab-$(LANG).zip

dynalab-$(LANG).zip: $(PYTHON_FILES) $(MENU_FILES) version
	zip -x "*/TEST.*" -x "*/__pycache__" -x "*/current_config.json" -r $@ Dynalab/src Dynalab/menus-$(LANG)

restore_svg:
	git restore svg_testfiles/*.svg

i18n: i18n/dynalab.pot i18n/fr.po Dynalab/src/locales/fr/LC_MESSAGES/dynalab.mo

i18n/dynalab.pot: $(PYTHON_FILES)
	@#xgettext -language=Python --from-code=UTF-8 -omit-header --indent --no-wrap --sort-by-file --join-existing --output $@ $?
	xgettext -language=Python --from-code=UTF-8 -omit-header --indent --no-wrap --sort-by-file --output $@ $^

i18n/fr.po: i18n/dynalab.pot
	msgmerge --quiet --update --indent --no-wrap --sort-by-file $@ $<

Dynalab/src/locales/fr/LC_MESSAGES/dynalab.mo: i18n/fr.po
	msgfmt $< -o $@

clean:
	rm -rf Dynalab/src/lib/__pycache__
	rm -f dynalab.zip dynalab-*.zip

very-clean: clean
	rm -rf  "$(EXTENSION_DIR)"/Dynalab/

.PHONY: clean very-clean install restore_test_svg i18n archive FORCE
