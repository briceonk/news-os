# MAME emulation notes
The NWS-5000X driver can be found in [this MAME fork](https://github.com/briceonk/mame). While there are a few new files, the main driver file can be found [here](https://github.com/briceonk/mame/blob/master/src/mame/drivers/news_r4k.cpp).

## Current status
With a few hacks, the driver can boot the monitor ROM. Basic commands (memory viewing, status information, expression evaluation, etc.) are mostly functional, anything requiring non-serial I/O is not.  See the driver comments for a more exhaustive list of what is/isn't emulated.
![](img/nws5000x_mame_mrom.png)
*MAME booted to the monitor ROM prompt*
![](img/mame_memory_status.png)
*Emulated NWS-5000X's memory status from `ss -m`*
![](img/mame_tlb_dump.png)
*TLB information dumped using the hidden `mp` command*
![](img/mame_device_list.png)
*Device list. Note that a few tricks are used to get it to think the DMAC and SPIFIs are visible even though they are not emulated. The SONIC shows up regardless of if it is actually functional or not.*

## Issues
Not counting things that aren't emulated, there are a few major issues I haven't been able to solve yet.

1. Freerunning clock and general timing issues.
  - Getting the monitor ROM to boot currently requires an unrealistically fast freerunning clock (physical address 0x1f840000). According to the NetBSD source code (and my own unscientific measurements with a stopwatch), the counter should increment once per microsecond. However, in emulation, it ends up waiting an extreme amount in a loop for a huge amount of time to elapse, meaning that the serial output is extremely slow. I'm not sure if this is an issue with the freerunning clock, an issue with the serial configuration, or an issue somewhere else that just happens to manifest this way (missing a timer interrupt or something that should be happening, maybe. Or AP-Bus stuff).
- By jacking up the freerunning clock rate an extreme amount (bit shifting it to the left a bunch), it no longer spends too long in the loop and sends characters at a normal rate.
2. Physical memory mapping and general physical address issues
- It took me a very long time to find a configuration that allowed the monitor ROM to enumerate 64MB of RAM (matches what my platform has). Using a disassembler, I was able to partially reverse engineer the algorithm it uses to scan memory and I came up with a hack that hooks off of a change in a part of memory to shift the memory addresses around to stop the monitor ROM from getting lost in the weeds. This change might be a coincidence, but it happens in between the first scan (where it expects the memory to be split) and the second scan (where it expects the unified 64MB starting from 0x0).
- Because of this, I'm not sure if I am missing something in how the memory scan is supposed to work, or if one of the ASICs on the board is actually playing around with the address map to compensate for how the board and/or memory cards are physically designed.
- Also, based on the values in the TLB (and the memory status from `ss -m`, see above screenshot), I suspect that the RAM is actually mapped to physical address 0x100000000. Note that the MIPS R4400SC has a 36-bit physical address bus. I'm not sure if this is breaking things either. I haven't found a way to have an offset greater 32 bits in MAME yet, but that might help.
3. AP-Bus emulation
- Documentation is completely lacking for the AP-Bus and its associated chips. For now, I've hacked it so the monitor ROM can boot, but there is a lot that will need to be figured out on the fly as more devices are emulated.