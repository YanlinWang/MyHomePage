.PHONY: all
all: index.html zh.html en.html

index.html: en.jemdoc publications.jemdoc service-roles.jemdoc news-en.jemdoc site-en.conf jemdoc build_homepage.py
	python3 build_homepage.py en.jemdoc site-en.conf $@

zh.html: index.jemdoc publications.jemdoc service-roles.jemdoc site.conf jemdoc build_homepage.py
	python3 build_homepage.py index.jemdoc site.conf $@

# Preserve links to the original English page, including section bookmarks.
en.html: index.html
	cp $< $@
