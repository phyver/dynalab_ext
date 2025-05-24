PYTHON_FILES=$(wildcard src/*.py src/lib/*.py)

install:
	mkdir -p  "$(HOME)/.config/inkscape/extensions/FablabExt/"
	cp -r src/*.py src/*.inx src/lib/ src/locales/ "$(HOME)/.config/inkscape/extensions/FablabExt/"

restore_svg:
	git restore svg_testfiles/*.svg

i18n: i18n/fablabext.pot i18n/fr.po src/locales/fr/LC_MESSAGES/fablabext.mo

i18n/fablabext.pot: $(PYTHON_FILES)
	xgettext -language=Python --from-code=UTF-8 -omit-header --indent --no-wrap --no-location --sort-output --join-existing --output $@ $?

i18n/fr.po: i18n/fablabext.pot
	msgmerge --quiet --update --indent --no-wrap --no-location --sort-output $@ $<

src/locales/fr/LC_MESSAGES/fablabext.mo: i18n/fr.po
	msgfmt $< -o $@

clean:
	rm -rf __pycache__
	rm -rf "$(HOME)"/.config/inkscape/extensions/FablabExt/__pycache__
	rm -rf "$(HOME)"/.config/inkscape/extensions/FablabExt/lib
	rm -rf "$(HOME)"/.config/inkscape/extensions/FablabExt/locales
	rm -f "$(HOME)"/.config/inkscape/extensions/FablabExt/*

.PHONY: clean install restore_test_svg i18n FORCE
