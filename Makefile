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
HAVE_PYQT4=true
else
HAVE_PYQT4=false
endif

ifneq (,$(wildcard $(PYUIC5)))
HAVE_PYQT5=true
else
HAVE_PYQT5=false
endif

# ifneq ($(HAVE_PYQT4),true)
ifneq ($(HAVE_PYQT5),true)
$(error PyQt5 is not available, please install it)
endif
# endif

ifeq ($(HAVE_PYQT5),true)
PYUIC ?= pyuic5
PYRCC ?= pyrcc5
else
PYUIC ?= pyuic4 -w
PYRCC ?= pyrcc4 -py3
endif

# ----------------------------------------------------------------------------------------------------------------------------

all: RES UI host utils

# ----------------------------------------------------------------------------------------------------------------------------
# Resources

RES = \
	source/resources_rc.py

RES: $(RES)

source/resources_rc.py: resources/resources.qrc resources/*/*.png # resources/*/*.svg
	$(PYRCC) $< -o $@

bin/resources/%.py: source/%.py
	$(LINK) $(CURDIR)/source/$*.py bin/resources/

# ----------------------------------------------------------------------------------------------------------------------------
# UI code

UIs = \
	source/ui_mod_connect.py \
#	source/ui_mod_pedalboard_open.py \
#	source/ui_mod_pedalboard_save.py \
	source/ui_mod_host.py \
	source/ui_mod_settings.py

UI: $(UIs)

source/ui_%.py: resources/ui/%.ui
	$(PYUIC) $< -o $@

# ----------------------------------------------------------------------------------------------------------------------------
# host (mod-host submodule, if present)

ifneq (,$(wildcard source/modules/mod-host/Makefile))
host: source/modules/mod-host/mod-host
else
host:
endif

source/modules/mod-host/mod-host: source/modules/mod-host/src/*.c source/modules/mod-host/src/*.h
	$(MAKE) -C source/modules/mod-host

# ----------------------------------------------------------------------------------------------------------------------------
# utils (from mod-ui, if present)

ifneq (,$(wildcard source/modules/mod-ui/utils/Makefile))
utils: source/modules/mod-ui/utils/libmod_utils.so
else
utils:
endif

source/modules/mod-ui/utils/libmod_utils.so: source/modules/mod-ui/utils/*.cpp source/modules/mod-ui/utils/*.h
	$(MAKE) -C source/modules/mod-ui/utils

# ----------------------------------------------------------------------------------------------------------------------------

clean:
	rm -f $(RES) $(UIs)
	rm -f *~ source/*~ source/*.pyc source/*_rc.py source/ui_*.py
ifneq (,$(wildcard source/modules/mod-host/Makefile))
	$(MAKE) clean -C source/modules/mod-host
endif
ifneq (,$(wildcard source/modules/mod-ui/utils/Makefile))
	$(MAKE) clean -C source/modules/mod-ui/utils
endif

# ----------------------------------------------------------------------------------------------------------------------------

run:
	./source/mod-app

# ----------------------------------------------------------------------------------------------------------------------------

install:
	# Create directories
	install -d $(DESTDIR)$(PREFIX)/bin/
	install -d $(DESTDIR)$(PREFIX)/share/applications/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/16x16/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/24x24/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/32x32/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/48x48/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/64x64/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/96x96/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/128x128/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/256x256/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/
	install -d $(DESTDIR)$(PREFIX)/share/mime/packages/
	install -d $(DESTDIR)$(PREFIX)/share/mod-app/

	# Install desktop files
	install -m 755 data/*.desktop          $(DESTDIR)$(PREFIX)/share/applications/

	# Install icons, 16x16
	install -m 644 resources/16x16/mod.png    $(DESTDIR)$(PREFIX)/share/icons/hicolor/16x16/apps/
	install -m 644 resources/24x24/mod.png    $(DESTDIR)$(PREFIX)/share/icons/hicolor/24x24/apps/
	install -m 644 resources/32x32/mod.png    $(DESTDIR)$(PREFIX)/share/icons/hicolor/32x32/apps/
	install -m 644 resources/48x48/mod.png    $(DESTDIR)$(PREFIX)/share/icons/hicolor/48x48/apps/
	install -m 644 resources/64x64/mod.png    $(DESTDIR)$(PREFIX)/share/icons/hicolor/64x64/apps/
	install -m 644 resources/96x96/mod.png    $(DESTDIR)$(PREFIX)/share/icons/hicolor/96x96/apps/
	install -m 644 resources/128x128/mod.png  $(DESTDIR)$(PREFIX)/share/icons/hicolor/128x128/apps/
	install -m 644 resources/256x256/mod.png  $(DESTDIR)$(PREFIX)/share/icons/hicolor/256x256/apps/
	install -m 644 resources/scalable/mod.svg $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/

	# Install mime package
	install -m 644 data/mod-app.xml $(DESTDIR)$(PREFIX)/share/mime/packages/

	# Install script files
	install -m 755 \
		data/mod-app \
		data/mod-remote \
		$(DESTDIR)$(PREFIX)/bin/

	# Install python code
	install -m 644 \
		source/mod-app \
		source/mod-remote \
		source/*.py \
		$(DESTDIR)$(PREFIX)/share/mod-app/

	# Adjust PREFIX value in script files
	sed -i "s?X-PREFIX-X?$(PREFIX)?" \
		$(DESTDIR)$(PREFIX)/bin/mod-app \
		$(DESTDIR)$(PREFIX)/bin/mod-remote

# ----------------------------------------------------------------------------------------------------------------------------

uninstall:
	rm -f  $(DESTDIR)$(PREFIX)/bin/mod-app
	rm -f  $(DESTDIR)$(PREFIX)/bin/mod-remote
	rm -f  $(DESTDIR)$(PREFIX)/share/applications/mod-app.desktop
	rm -f  $(DESTDIR)$(PREFIX)/share/applications/mod-remote.desktop
	rm -f  $(DESTDIR)$(PREFIX)/share/mime/packages/mod-app.xml
	rm -f  $(DESTDIR)$(PREFIX)/share/icons/hicolor/*/apps/mod.png
	rm -f  $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/mod.svg
	rm -rf $(DESTDIR)$(PREFIX)/share/mod-app/

# ----------------------------------------------------------------------------------------------------------------------------
