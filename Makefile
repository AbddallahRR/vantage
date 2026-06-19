.PHONY: install uninstall

install:
	chmod +x ./install.sh
	./install.sh
	cp ./icon.png /usr/share/icons/hicolor/scalable/apps/vantage.png
	cp ./vantage.desktop /usr/share/applications/vantage.desktop
	install -d /usr/lib/vantage
	install -m 755 ./vantage-helper.sh /usr/lib/vantage/vantage-helper.sh
	install -m 440 ./vantage.sudoers /etc/sudoers.d/vantage
	cp ./vantage.py /usr/bin/vantage
	chmod a+rx /usr/bin/vantage

uninstall:
	rm -f /usr/share/icons/hicolor/scalable/apps/vantage.png
	rm -f /usr/share/applications/vantage.desktop
	rm -f /usr/lib/vantage/vantage-helper.sh
	rm -f /etc/sudoers.d/vantage
	rmdir /usr/lib/vantage 2>/dev/null || true
	rm -f /usr/bin/vantage
