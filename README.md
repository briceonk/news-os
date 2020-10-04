# news-os
Compilation of information about setting up and using Sony NEWS Unix
workstations. There is limited information about NEWS workstations, especially
in English. Hopefully this will help preserve information about these
workstations. This is very much a work-in-progress.

The `src` folder contains source code and scripts for quick utilities I wrote
to do various tasks when working with my NWS-5000X.
- `newsos_cd_extractor.py`: Extracts archives from the NEWS-OS 4.2.1aR CD
- `xdmcp.py`: Automates launching XDMCP sessions from any machine with Xephyr installed
- `rarp/`: Docker image which can respond to RARP requests from the NEWS ROM Monitor
- `serial_keyboard/`: Script for using a modern workstation + USB->TTL adapter to emulate a NEWS serial keyboard

## Pages
- introduction.md: What is NEWS?
- nws5000x.md: Information about the NWS-5000x workstation
- news-os-42.md: Using NEWS-OS 4.2.x
- news-os-6.md: Using NEWS-OS 6.x

## Sources and Further Reading (mainly in Japanese)
- [ozuma's NEWS 5000x operations page](http://ozuma.o.oo7.jp/nws5000x.htm)
- [Sony NEWS hardware info](https://katsu.watanabe.name/doc/sonynews/)
- [NEWS World](https://web.archive.org/web/20170202100940/www3.videa.or.jp/NEWS/)
- [NEWS Keyboard Converter](https://github.com/tmk/tmk_keyboard/tree/master/converter/news_usb)
- [NetBSD newsmips page](http://wiki.netbsd.org/ports/newsmips/)
- [NetBSD news68k page](http://wiki.netbsd.org/ports/news68k/)
