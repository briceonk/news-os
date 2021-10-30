# MAME emulation notes

The NWS-5000X driver can be found in [this MAME fork](https://github.com/briceonk/mame). While there are a few new files, the main driver file can be found [here](https://github.com/briceonk/mame/blob/master/src/mame/drivers/news_r4k.cpp).

## Current status

### Monitor ROM

With a few workarounds related to memory and APbus initialization, the driver can boot the monitor ROM. Basic commands (memory viewing, status information, expression evaluation, etc.) are mostly functional.
![MAME booted to the monitor ROM prompt](img/nws5000x_mame_mrom.png)

![Emulated NWS-5000X's memory status from `ss -m`](img/mame_memory_status.png)

![TLB information dumped using the hidden `mp` command](img/mame_tlb_dump.png)

![Device list](img/mame_device_list.png)

### NEWS-OS 4.2.1aRD

NEWS-OS 4 can successfully install and boot. SXDM, the NEWS X11 session manager, works in MAME. Using a TAP/TUN virtual NIC to connect to the emulated platform, you can use an application like Xephyr to connect to and use the emulator.

![NEWS-OS 4 booted to the login prompt](img/421aRD-mame.png)

![SXDM login viewed with Xephyr, connected to MAME via TAP/TUN](img/mame_sxdm_login.png)

![X11 session over TAP/TUN](img/mame_applications_running.png)

![X11 session with other applications running](img/mame_more_applications_running.png)

### NetBSD

The floppy "miniroot" used to install the newsmips NetBSD port can boot without any workarounds beyond what is required for the monitor ROM. For now, I've only implemented enough of the APbus FIFOQ chip logic to read from devices like the FDC, but that is all the NetBSD installer needs.

![NetBSD booted to the floppy installer](img/netbsd-floppy.png)

With the current SPIFI3 and DMAC3 emulation, it can also detect and enumerate emulated hard drives. However, something still seems to be buggy in the SPIFI3 emulation, since NetBSD seems to think there are multiple LUNs attached, when there is just one. NEWS-OS doesn't have this problem.

### NEWS-OS 6.1.2

For now, I am focusing on 4.2.1aRD but will move on to 6.1.2 (and NetBSD from a hard drive, for that matter) after that.

## Other Issues

### Physical memory mapping and general physical address issues

- It took me a very long time to find a configuration that allowed the monitor ROM to enumerate 64MB of RAM (matches what my platform has). Using a disassembler, I was able to partially reverse engineer the algorithm it uses to scan memory and I came up with a hack that hooks off of a change in a part of memory to shift the memory addresses around to stop the monitor ROM from getting lost in the weeds. This change might be a coincidence, but it happens in between the first scan (where it expects the memory to be split) and the second scan (where it expects the unified 64MB starting from 0x0), and touches regions of the address space that seem to be the memory controller (or similar platform hardware).
- Note that the MIPS R4400SC has a 36-bit physical address bus. I'm not sure if this is breaking things either. I haven't found a way to have an offset greater 32 bits in MAME yet, but that might help. The MSB of the physical address (bit 33) seems to be influenced by the memory region used to access it. See the below section for more details. The memory base from the status command `ss -m` (see above screenshot) has the RAM base set to 0x100000000.

### APbus emulation

- For now, I've done the minimum for the monitor ROM to boot, but there is a lot that will need to be figured out on the fly as more devices are emulated. Miraculously, the APbus specs are available on the [OCMP website](https://web.archive.org/web/19970713173157/http%3A%2F%2Fwww1.sony.co.jp%2FOCMP%2F), courtesy of the Internet Archive.

## Installing NEWS-OS 4.2.1aRD

### Requirements

- MAME build with NWS-5000X driver
- NEWS-OS 4.2.1aRD install CD/ISO (you can use `dd` to create an ISO from the CD-ROM)
- NWS-5000 firmware (see `src/rom_extractor.py` for an example of getting ROM images from your own NWS-5000).

### Booting to the APmonitor (NEWS ROM monitor)

- Put firmware images in `roms/nws5000x`
- Make an empty hard disk image. The NEWS-OS installer is picky about sizes, so you can use the `chdman` command below to get a ~2GB image. Feel free to experiment, though :)
- Launch MAME with the following command line. I recommend using `pty` for serial over `terminal` because Linux terminals support the special characters that the installer uses. It is messy and hard to use on the MAME terminal emulator. If you want to use X Windows, be sure to use taputil to set up your network TAP/TUN device before launching MAME. For now, the NWS-5000X driver does not have any framebuffer emulation, so you must connect over the network to use the GUI.

```sh
cd /path/to/mame/repo
sudo src/osd/sdl/taputil.sh -c $USER 192.168.5.5 192.168.5.99 # only if planning on using networking
chdman createhd -o test.chd -s 2088960000
./mame nws5000x -scsi0:0 harddisk -scsi0:2 cdrom -cdrom <path-to-iso> -harddisk test.chd -log -nodrc -debug
```

- If all goes well, you should get to the APmonitor prompt.

### Booting to the install kit

- Boot from the CD-ROM drive by running `bo scsi(,20)`
- The default root disklabel is fine to use.
- This should boot into the NEWS-OS installer. Follow the prompts and select your desired packages. You might need to adjust the partition size to fit everything.
- I'd recommend not selecting the option to start X automatically. You can enable that later (see `news-os-42.md`), and you'll want the option of a serial login to debug network issues.
- After a long time, the installer will hopefully succeed and halt, bringing you back to the APmonitor prompt.

### Booting NEWS-OS 4.2.1aRD for the first time

- Boot from the hard disk by running `bo` or `bo scsi(0,0)`
- If all goes well, this will boot to the login prompt. This will take a very long time due to the disk check. See `news-os-42.md` for instructions on bypassing the disk check for future boots.
- You should be able to log in (`root`, no password by default) and use the emulated platform!
- Setting up networking can be a bit tricky. Make sure that you have selected "TAP/TUN device" in the MAME UI (Press Scroll Lock to disable special key passthrough, then press Tab, then scroll down to `Network Devices`). Then, you should be able to reach the emulator at the configured IP address, as long as you used TAP. Make sure you add your host as the default route, otherwise XDMCP (and some other applications) may not work: `route add default <TAP/TUN host IP> 1`

## Using a modified ROM image in MAME

The monitor ROM does a basic checksum of itself before booting. You can patch this out by changing the code at offset 0x70C to:

```assembly
bne $0, $0, $bfc009c4  ; 0x140000AD in hex
```

The monitor ROM will still run the checksum, but when it fails it will not branch to the boot halt address (0xbfc009c4, which just branches to itself).
