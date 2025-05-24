install:
	mkdir -p  "$(HOME)/.config/inkscape/extensions/FablabExt/"
	cp src/*.py src/*.inx "$(HOME)/.config/inkscape/extensions/FablabExt/"

restore_svg:
	git restore svg_testfiles/*.svg

clean:
	rm -rf __pycache__
	rm -rf "$(HOME)"/.config/inkscape/extensions/FablabExt/__pycache__
	rm -f "$(HOME)"/.config/inkscape/extensions/FablabExt/*

.PHONY: clean install restore_test_svg
