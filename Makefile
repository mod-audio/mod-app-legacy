#!/usr/bin/make -f
# Makefile for mod-app #
# -------------------- #
# Created by falkTX
#

# ----------------------------------------------------------------------------------------------------------------------------

PREFIX  := /usr
DESTDIR :=

# ----------------------------------------------------------------------------------------------------------------------------
# Set PyQt tools

PYUIC4 ?= /usr/bin/pyuic4
PYUIC5 ?= /usr/bin/pyuic5

ifneq (,$(wildcard $(PYUIC4)))
HAVE_PYQT=true
HAVE_PYQT4=true
else
HAVE_PYQT4=false
endif

ifneq (,$(wildcard $(PYUIC5)))
HAVE_PYQT=true
HAVE_PYQT5=true
else
HAVE_PYQT5=false
endif

ifneq ($(HAVE_PYQT),true)
$(error PyQt is not available, please install it)
endif

ifeq ($(HAVE_PYQT4),true)
DEFAULT_QT ?= 4
else
DEFAULT_QT ?= 5
endif

ifeq ($(DEFAULT_QT),4)
PYUIC ?= pyuic4 -w
PYRCC ?= pyrcc4 -py3
else
PYUIC ?= pyuic5
PYRCC ?= pyrcc5
endif

# ----------------------------------------------------------------------------------------------------------------------------

all: RES UI

# ----------------------------------------------------------------------------------------------------------------------------
# Resources

RES = \
	source/mod_config.py \
	source/resources_rc.py

RES: $(RES)

source/mod_config.py:
	@echo "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n" > $@
ifeq ($(DEFAULT_QT),4)
	@echo "config_UseQt5 = False" >> $@
else
	@echo "config_UseQt5 = True" >> $@
endif

source/resources_rc.py: resources/resources.qrc resources/*/*.png # resources/*/*.svg
	$(PYRCC) $< -o $@

bin/resources/%.py: source/%.py
	$(LINK) $(CURDIR)/source/$*.py bin/resources/

# ----------------------------------------------------------------------------------------------------------------------------
# UI code

UIs = \
	source/ui_mod_host.py \
	source/ui_mod_settings.py

UI: $(UIs)

source/ui_%.py: resources/ui/%.ui
	$(PYUIC) $< -o $@

# ----------------------------------------------------------------------------------------------------------------------------

clean:
	rm -f $(RES) $(UIs)
	rm -f *~ source/*~ source/*.pyc source/*_rc.py source/ui_*.py

# ----------------------------------------------------------------------------------------------------------------------------

install:
	# Create directories
	install -d $(DESTDIR)$(PREFIX)/bin/
	install -d $(DESTDIR)$(PREFIX)/share/applications/
	install -d $(DESTDIR)$(PREFIX)/share/mime/packages/
	install -d $(DESTDIR)$(PREFIX)/share/mod-app/
	install -d $(DESTDIR)$(PREFIX)/share/pixmaps/

	# Install desktop file and pixmap
	install -m 644 data/*.desktop          $(DESTDIR)$(PREFIX)/share/applications/
	install -m 644 resources/48x48/mod.png $(DESTDIR)$(PREFIX)/share/pixmaps/mod-app.png

	# Install mime package
	install -m 644 data/mod-app.xml $(DESTDIR)$(PREFIX)/share/mime/packages/

	# Install script files
	install -m 755 \
		data/mod-app \
		$(DESTDIR)$(PREFIX)/bin/

	# Install python code
	install -m 644 \
		source/mod-app \
		source/*.py \
		$(DESTDIR)$(PREFIX)/share/mod-app/

	# Adjust PREFIX value in script files
	sed -i "s?X-PREFIX-X?$(PREFIX)?" $(DESTDIR)$(PREFIX)/bin/mod-app

# ----------------------------------------------------------------------------------------------------------------------------

uninstall:
	rm -f  $(DESTDIR)$(PREFIX)/bin/mod-app
	rm -f  $(DESTDIR)$(PREFIX)/share/applications/mod-app.desktop
	rm -f  $(DESTDIR)$(PREFIX)/share/mime/packages/mod-app.xml
	rm -f  $(DESTDIR)$(PREFIX)/share/pixmaps/mod-app.png
	rm -rf $(DESTDIR)$(PREFIX)/share/mod-app/

# ----------------------------------------------------------------------------------------------------------------------------
