install:
	mkdir -p  "$(HOME)/.config/inkscape/extensions/FablabExt/"
	cp *.py *.inx "$(HOME)/.config/inkscape/extensions/FablabExt/"

restore_svg:
	git restore svg_tests/*.svg

.PHONY: install restore_test_svg
