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

## Enabling fastboot
By default, NEWS-OS 4.2 will run disk checks at every boot. While this is typically
a good idea, it can result in long boot times, especially if using a SCSI2SD or newer
hard drive formatted with more space than was realistic for the time. The `fastboot`
program bypasses the disk check for one boot by creating `/fastboot`, but `/etc/rc`
clears this by default, meaning that it doesn't persist, just does one reboot without
running disk checks. If you don't want to edit `/etc/rc` to bypass the check, you can
do it by creating `/fastboot` and making `/etc/rc.safs` with just an `exit 0` call.
This will cause `/etc/rc` to skip the removal of `/fastboot`, thus making every boot
skip the filesystem checks. If you do this, make sure you manually run fsck from time
to time, or after emergency power loss situations. This is a hack, so use with care :)

## X-Windows setup
When installing NEWS-OS 4.2.1aR, unless you have a fully working monitor, mouse,
and keyboard setup, I recommend installing the desired X11 packages but not
selecting the option to start X-Windows automatically at startup. This way, the
serial console will remain enabled in /etc/ttys. The `dmset` command can be used
to enable it later (see below).

### Selecting an X11 display manager
Sony included two X11 display managers with NEWS-OS 4.2.1, the standard `xdm` as
well as the Sony NEWS Desk `sxdm` manager. The `sxdm` manager has a NEWS-specific login
screen, uses `mwm` as the default window manager, and has `sxsession` as the
login application. `xdm` uses `twm` as the default window manager, and has an `xterm`
session as the login application.

![](img/sxdm_login_screen.png)

*sxdm login prompt*

![](img/sxdm_macx.png)

*sxdm login prompt as rendered by MacX*

![](img/sxsession.png)

*Sony SXsession launcher*

To launch a display manager automatically at system boot time, run the `dmset` command.
`dmset` alone will set the default to `sxdm`, `dmset -x` will set it to `xdm`, and `dmset -n`
will disable X11 display manager auto-launch. `dmset` also edits `/etc/ttys` to disable
console login, so if you want to continue to have console login access, either revert `/etc/ttys`
after running `dmset`, or edit the line `DM=` in `/etc/rc.custom` to be `DM=sxdm` or `DM=xdm`
instead of running `dmset`.

### Enabling Japanese text rendering
NEWS-OS has its own Japanese fonts. Modern installs of X11 don't include them.
To fix this, copy the contents of `/usr/lib/X11/fonts/sony` to a path on your
modern machine included on the X11 font path, like `~/.local/share/fonts`. You
can check what paths X11 has configured by running `xset q`.

Note that NEWS-OS will only work with Japanese text if the terminal is set to
use Japanese, which can be checked by using `set` to get the value of the `term`
variable. For example, `xterm` will only support ASCII, but `xterm-sjis` or `jterm` will
be able to display Shift-JIS encoded Japanese text. The `jterm` command will
launch `xterm` with `term` set to `jterm`.

### Japanese input
NEWS-OS has a few components that work together to enable Japanese input.
Additionally, terminal input is handled differently from X11. The components
have man pages in English and Japanese available, but in brief:
- `sj3serv`: Service that provides Kana to Kanji conversions
- `sj3`: Terminal that supports Japanese and English text input, and can
   communicate with `sj3serv` to provide Kana to Kanji capabilities as well.
   This includes file names. `sj3` will only work in a terminal that uses a
   Japanese encoding.

![](img/sj3.png)

*ASCII vs SJIS terminal*

There are additional components (`sjx` for X11, `sj3dic` for managing custom
conversion dictionaries) as well as older utilities (`sj2`, `sj2dic`) that may
be available depending on what settings were selected during installation.

## Rebuilding the NEWS-OS kernel
Like modern Unix and Linux systems, the kernel can be rebuilt with configuration changes.
```csh
# Switch to kernel configuration directory
% cd /sys/conf
# Edit the desired parameters in /sys/conf/NEWS5000
# Execute the required config and make commands
% config NEWS5000
% cd ../NEWS5000
% make depend
% make
```
After running make, the new kernel, `vmunix`, will be available and can be loaded from the ROM monitor, or placed at
`/vmunix`. After reboot, the kernel build date should match when `make` was run (per NEWS system clock).

## NEWS-OS 4 RTC Patch Kit
NEWS-OS 4 patches are included with the NEWS-OS 6 patch kit.

![](img/rtc_patch_kit.jpeg)
