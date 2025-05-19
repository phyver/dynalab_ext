install:
	mkdir -p  "$(HOME)/.config/inkscape/extensions/FablabExt/"
	cp *.py *.inx "$(HOME)/.config/inkscape/extensions/FablabExt/"

.PHONY: install
