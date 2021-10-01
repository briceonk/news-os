# DMAC3 notes
The NWS-5000X has two Hewlett Packard SPIFI3 SCSI controllers. Sony also included a DMA controller called the DMAC3, which seems to have two onboard DMA controllers and offboard DMA mapping RAM. I have not been able to find datasheets for either the DMAC3 (not surprising) nor the SPIFI3 (slightly more surprising since it isn't a Sony chip).

## DMAC3 Memory Mapping (DRAFT)
Note: this section is a draft. I'm still in the middle of developing emulation for this part.

The DMAC3 has its own virtual->physical addressing scheme. Like the R4400 CPU's TLB, the host OS is responsible for populating the DMAC3's TLB.
Each entry in the page table is structured as follows:
```
0x xxxx xxxx xxxx xxxx
  |   pad   |  entry  |
```

The entry field is packed as follows:
```
0b    x      x     xxxxxxxxxx xxxxxxxxxxxxxxxxxxxx
   |valid|coherent|    pad2  |       pfnum        |
```

The DMAC3 requires RAM to hold its page table/TLB. On the NWS-5000X, this is 128KiB starting at physical address 0x14c20000.

The monitor ROM populates the first two PTEs as follows in response to a `dl` command.
```
Addr       PTE1             PTE2
0x14c20000 0000000080103ff5 0000000080103ff6
```

It also loads the `address` register with 0xd60. This will cause the DMAC3 to start mapping from virtual address 0xd60 to physical address 0x3ff5d60.
If the address register goes beyond 0xFFF, bit 12 will increment. This will increase the page number so the virtual address will be
0x1000, and will cause the DMAC to use the next PTE (in this case, the next sequential page, 0x3ff6000).

NetBSD splits the mapping RAM into two sections, one for each DMAC3 controller. If the OS does not keep track, the DMACs
could end up in a configuration that would cause them to overwrite each other's data.

Another note: NetBSD mentions that the `pad2` section of the register is 10 bits. However, this might not be fully accurate.
On the NWS-5000X, the physical address bus is 36 bits because it has an R4400SC. The 32nd bit is sometimes set, depending
on the virtual address being used (maybe it goes to the memory controller). It doesn't impact the normal operation of the
computer, but does mean that the `pad2` section might only be 6 bits, not 10 bits. See `nws5000x-mame.md` for more details
on the NWS-5000's memory mapping scheme.

### Direct-access mode
The DMAC3 will bypass the DMA map and use the `address` register as the physical page when the MSB of the `address` register is set.
NEWS-OS uses this feature during boot, and it is mentioned in passing in a [NetBSD mailing list thread](http://www.jp.netbsd.org/ja/JP/ml/port-mips-ja/200005/msg00005.html).

## DMAC3 NetBSD source annotated
All source below annotated by me, everything else is copyrighted by the original authors and reproduced here under the terms of the BSD license (https://www.netbsd.org/about/redistribution.html)
```
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. The name of the author may not be used to endorse or promote products
 *    derived from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
 * IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
 * OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
 * IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
 * NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

### dmac3reg.h
```C
/* Copyright (c) 2000 Tsubai Masanari.  All rights reserved. */

// This struct defines the register file for the DMAC3
// It has two of them, one for each controller/SCSI bus.
struct dmac3reg {
	volatile uint32_t csr;  // Status and control register
	volatile uint32_t intr; // Interrupt control register
	volatile uint32_t len;  // TRC register (Transfer count)
	volatile uint32_t addr; // TRA register (Transfer address)
	volatile uint32_t conf; // Configuration register
};

// CSR (Control and Status Register)
#define DMAC3_CSR_DBURST	0x0020
#define DMAC3_CSR_MBURST	0x0010
#define DMAC3_CSR_APAD		0x0008
#define DMAC3_CSR_RESET		0x0004
#define DMAC3_CSR_RECV		0x0002
#define DMAC3_CSR_SEND		0x0000
#define DMAC3_CSR_ENABLE	0x0001

// ICTL (Interrupt Control Register)
#define DMAC3_INTR_PERR		0x8000
#define DMAC3_INTR_DRQI		0x4000
#define DMAC3_INTR_DRQIE	0x2000
#define DMAC3_INTR_DREQ		0x1000
#define DMAC3_INTR_EOPI		0x0400
#define DMAC3_INTR_EOPIE	0x0200
#define DMAC3_INTR_EOP		0x0100
#define DMAC3_INTR_TCI		0x0040
#define DMAC3_INTR_TCIE		0x0020
#define DMAC3_INTR_INTEN	0x0002
#define DMAC3_INTR_INT		0x0001

// CONF (Configuration register)
#define DMAC3_CONF_IPER		0x8000
#define DMAC3_CONF_MPER		0x4000
#define DMAC3_CONF_PCEN		0x2000
#define DMAC3_CONF_DERR		0x1000
#define DMAC3_CONF_DCEN		0x0800
#define DMAC3_CONF_ODDP		0x0200
#define DMAC3_CONF_WIDTH	0x00ff
#define DMAC3_CONF_SLOWACCESS	0x0020 // Configure DMAC to talk to SPIFI
#define DMAC3_CONF_FASTACCESS	0x0001 // Default speed


#define DMAC3_PAGEMAP	0xb4c20000 // DMA mapping RAM location
#define DMAC3_MAPSIZE	0x20000 // Size of DMA mapping ram

// Page table entry structure (64 bits)
struct dma_pte {
	uint32_t pad1;
	uint32_t valid:1,
	      coherent:1,	/* ? */
	      pad2:10,		/* ? */
	      pfnum:20;
};
```

### dmac3var.h
```C
/* Copyright (c) 2000 Tsubai Masanari.  All rights reserved. */

// Software-defined controller
struct dmac3_softc {
	device_t sc_dev;
	struct dmac3reg *sc_reg;
	vaddr_t sc_dmaaddr;
	volatile uint32_t *sc_dmamap;
	int sc_conf;
	int sc_ctlnum;
};

struct dmac3_softc *dmac3_link(int);
void dmac3_reset(struct dmac3_softc *);
void dmac3_start(struct dmac3_softc *, vaddr_t, int, int);
int dmac3_intr(void *);
void dmac3_misc(struct dmac3_softc *, int);
```

### dmac3.c
```C
/* Copyright (c) 2000 Tsubai Masanari.  All rights reserved. */

#include <sys/cdefs.h>
__KERNEL_RCSID(0, "$NetBSD: dmac3.c,v 1.13 2009/12/14 00:46:09 matt Exp $");

#include <sys/param.h>
#include <sys/device.h>
#include <sys/kernel.h>
#include <sys/systm.h>

#include <uvm/uvm_extern.h>

#include <machine/locore.h>

#include <newsmips/apbus/apbusvar.h>
#include <newsmips/apbus/dmac3reg.h>
#include <newsmips/apbus/dmac3var.h>

#include <mips/cache.h>

#include "ioconf.h"

#define DMA_BURST
#define DMA_APAD_OFF

#ifdef DMA_APAD_OFF
#define APAD_MODE	0
#else
#define APAD_MODE	DMAC3_CSR_APAD
#endif

#ifdef DMA_BURST
#define BURST_MODE	(DMAC3_CSR_DBURST | DMAC3_CSR_MBURST)
#else
#define BURST_MODE	0
#endif

int dmac3_match(device_t, cfdata_t, void *);
void dmac3_attach(device_t, device_t, void *);

extern paddr_t kvtophys(vaddr_t);

CFATTACH_DECL_NEW(dmac, sizeof(struct dmac3_softc),
    dmac3_match, dmac3_attach, NULL, NULL);

/**
 * Returns true if the specified device is a DMAC3, false otherwise.
 * Used during AP-Bus probe.
 */
int
dmac3_match(device_t parent, cfdata_t cf, void *aux)
{
	struct apbus_attach_args *apa = aux;

	if (strcmp(apa->apa_name, "dmac3") == 0)
		return 1;

	return 0;
}

/**
 * Perform initial setup of the software-defined controller once 
 * a match is confirmed.
 */
void
dmac3_attach(device_t parent, device_t self, void *aux)
{
	struct dmac3_softc *sc = device_private(self);
	struct apbus_attach_args *apa = aux;
	struct dmac3reg *reg;
	static paddr_t dmamap = DMAC3_PAGEMAP; // Pointer to DMA mapping ram 
                                           // (physical address)
	static vaddr_t dmaaddr = 0; // Virtual address for DMA start (?) TBD

	sc->sc_dev = self;
	reg = (void *)apa->apa_hwbase; // HW base address = DMAC3 register
	sc->sc_reg = reg;
	sc->sc_ctlnum = apa->apa_ctlnum; // AP-Bus controller number
	sc->sc_dmamap = (uint32_t *)dmamap;
	sc->sc_dmaaddr = dmaaddr;
	dmamap += 0x1000; // Static, so the first 0x1000 bytes are for DMAC3-0, 
                      // the next 0x1000 are for DMAC3-1
	dmaaddr += 0x200000; // Ditto

    // Initial reset sequence. See MROM notes for how this compares.

    // Set PCEN, DCEN, and DEFAULT access 
	sc->sc_conf = DMAC3_CONF_PCEN | DMAC3_CONF_DCEN | DMAC3_CONF_FASTACCESS;

    // Reset the DMAC3
	dmac3_reset(sc);

    // Print the attach message.
    // My 5000x yields:
    // dmac0 at ap0 slot0 addr 0xbe200000: ctlnum = 0, map = 0xb4c20000, va = 0
    // dmac1 at ap0 slot0 addr 0xbe300000: ctlnum = 1, map = 0xb4c21000, va = 0x200000
	aprint_normal(" slot%d addr 0x%lx", apa->apa_slotno, apa->apa_hwbase);
	aprint_normal(": ctlnum = %d, map = %p, va = %#"PRIxVADDR,
	       apa->apa_ctlnum, sc->sc_dmamap, sc->sc_dmaaddr);
	aprint_normal("\n");
}

/**
 * Find specified DMAC3 (called during SPIFI init to link the DMAC with the SPIFI)
 */
struct dmac3_softc *
dmac3_link(int ctlnum)
{
	struct dmac3_softc *sc;
	int unit;

	for (unit = 0; unit < dmac_cd.cd_ndevs; unit++) {
		sc = device_lookup_private(&dmac_cd, unit);
		if (sc == NULL)
			continue;
		if (sc->sc_ctlnum == ctlnum)
			return sc;
	}
	return NULL;
}

/**
 * Reset the specified DMAC3
 */
void
dmac3_reset(struct dmac3_softc *sc)
{
	struct dmac3reg *reg = sc->sc_reg;

	reg->csr = DMAC3_CSR_RESET; // Chip-level reset (?) TBD
	reg->csr = 0;
	reg->intr = DMAC3_INTR_EOPIE | DMAC3_INTR_INTEN; // Enable EOPIE and INTEN
	reg->conf = sc->sc_conf; // Sync conf register with software-defined controller state
}

/**
 * Instruct the DMAC3 to start a new transaction
 */
void
dmac3_start(struct dmac3_softc *sc, vaddr_t addr, int len, int direction)
{
	struct dmac3reg *reg = sc->sc_reg;
	paddr_t pa;
	vaddr_t start, end, v;
	volatile uint32_t *p;

	if (reg->csr & DMAC3_CSR_ENABLE) // Restart the DMAC if it was already enabled
		dmac3_reset(sc);

	start = mips_trunc_page(addr); // Get the start page address
	end   = mips_round_page(addr + len); // Get the end page address
	p = sc->sc_dmamap; // Start at the beginning of the allocated DMA mapping RAM
	for (v = start; v < end; v += PAGE_SIZE) {
		pa = kvtophys(v); // Get the physical address of the v-th page
		mips_dcache_wbinv_range(MIPS_PHYS_TO_KSEG0(pa), PAGE_SIZE); // Flush and invalidate cache so DMAC doesn't use stale data
		*p++ = 0; // clear the previous DMA data
		*p++ = (pa >> PGSHIFT) | 0xc0000000; // Write the page number to DMA map
	}
	*p++ = 0; // write 0 to second-to-last map slot
	*p++ = 0x003fffff; // set last map slot (why? TBD)

	addr &= PGOFSET; // Get byte offset into page
	addr += sc->sc_dmaaddr; // Add to the base of the DMA map to skip over the parts of the page that shouldn't be included

	reg->len = len; // Set DMAC3's count register
	reg->addr = addr; // Set DMAC3's base address register
	reg->intr = DMAC3_INTR_EOPIE | DMAC3_INTR_INTEN; // Enable interrupts in general and end-of-operation interrupt in particular
	reg->csr = DMAC3_CSR_ENABLE | direction | BURST_MODE | APAD_MODE; // Enable DMAC3 transaction, setting the direction as well as BURST and APAD mode, if defined.
                                                                      // Note: with the current #define settings, APAD is off, BURST is on.
}

/**
 * Interrupt handler for the DMAC3
 */
int
dmac3_intr(void *v)
{
	struct dmac3_softc *sc = v;
	struct dmac3reg *reg = sc->sc_reg;
	int intr, conf, rv = 1;

	intr = reg->intr; // Pull interrupt status from DMAC
	if ((intr & DMAC3_INTR_INT) == 0) // No interrupt (stray?)
		return 0;

	/* clear interrupt */
	conf = reg->conf;
	reg->conf = conf;
	reg->intr = intr;

	if (intr & DMAC3_INTR_PERR) { // Return failure (PERR = ? TBD)
		printf("%s: intr = 0x%x\n", device_xname(sc->sc_dev), intr);
		rv = -1;
	}

	if (conf & (DMAC3_CONF_IPER | DMAC3_CONF_MPER | DMAC3_CONF_DERR)) { // don't return a failure if one of these happens (why? TBD)
		printf("%s: conf = 0x%x\n", device_xname(sc->sc_dev), conf);
		if (conf & DMAC3_CONF_DERR) {  // Reset DMAC if DERR happened
			printf("DMA address = 0x%x\n", reg->addr);
			printf("resetting DMA...\n");
			dmac3_reset(sc);
		}
	}

	return rv;
}

/**
 * Function for setting other DMAC3 configuration settings, like the access mode (SLOW/FASTACCESS)
 */
void
dmac3_misc(struct dmac3_softc *sc, int cmd)
{
	struct dmac3reg *reg = sc->sc_reg;
	int conf;

	conf = DMAC3_CONF_PCEN | DMAC3_CONF_DCEN | cmd;
	sc->sc_conf = conf;
	reg->conf = conf;
}
```