# NEWS-OS 4.2.1aR
NEWS-OS 4.2.1aR is the APbus RISC release of Sony's BSD-based OS. The CISC and
non-APbus RISC versions should be similar in operation.

## Installing NEWS-OS 4.2.1aR
On an APbus-based system, insert the CD-ROM (or flash the image to a SCSI2SD
or similar device), then boot into it from the NEWS ROM Monitor.

The bootloader will ask for information about the disk attached to SCSI ID 0 (it
can format the disk or use an existing disk label). Then, it will copy the
miniroot filesystem from the CD-ROM to the swap space on disk and boot from it.
Miniroot contains the installation script and programs. Once the miniroot image
has booted, the installation program will start automatically.

## X-Windows setup
When installing NEWS-OS 4.2.1aR, unless you have a fully working monitor, mouse,
and keyboard setup, I recommend installing the desired X11 packages but not
selecting the option to start X-Windows automatically at startup. This way, the
serial console will remain available in /etc/ttys. Then, `sxdm` or `xdm` can be
selected in `/etc/rc.custom` after the system install and will be started
automatically on subsequent boots.

### Selecting an X11 display manager
Sony included two X11 display managers with NEWS-OS 4.2.1, the standard `xdm` as
well as the Sony `sxdm` manager. The `sxdm` manager has a NEWS-specific login
screen, uses `mwm` as the default window manager, and has `sxsession` as the
login application. `xdm` uses `twm` for the window manager, and has an `xterm`
session as the login application.

![](img/sxdm_login_screen.png)
*sxdm login prompt*
