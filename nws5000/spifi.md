# SPIFI notes
The NWS-5000X has two Hewlett Packard SPIFI3 SCSI controllers. Sony also included a DMA controller called the DMAC3, which seems to have two onboard DMA controllers and offboard DMA mapping RAM. I have not been able to find datasheets for either the DMAC3 (not surprising) nor the SPIFI3 (slightly more surprising since it isn't a Sony chip).

## SPIFI NetBSD source annotated
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

### spifireg.h
```C
/* Copyright (c) 2000 Tsubai Masanari.  All rights reserved. */

// SPIFI3 register file (1 per SCSI bus)
struct spifi_reg {
	volatile uint32_t spstat;	/* RO: SPIFI state		*/
	volatile uint32_t cmlen;	/* RW: Command/message length	*/
	volatile uint32_t cmdpage;	/* RW: Command page		*/
	volatile uint32_t count_hi;	/* RW: Data count (high)	*/
	volatile uint32_t count_mid;	/* RW:            (mid)		*/
	volatile uint32_t count_low;	/* RW:            (low)		*/
	volatile uint32_t svptr_hi;	/* RO: Saved data pointer (high)*/
	volatile uint32_t svptr_mid;	/* RO:                    (mid)	*/
	volatile uint32_t svptr_low;	/* RO:                    (low) */
	volatile uint32_t intr;		/* RW: Processor interrupt	*/
	volatile uint32_t imask;	/* RW: Processor interrupt mask	*/
	volatile uint32_t prctrl;	/* RW: Processor control	*/
	volatile uint32_t prstat;	/* RO: Processor status		*/
	volatile uint32_t init_status;	/* RO: Initiator status		*/
	volatile uint32_t fifoctrl;	/* RW: FIFO control		*/
	volatile uint32_t fifodata;	/* RW: FIFO data		*/
	volatile uint32_t config;	/* RW: Configuration		*/
	volatile uint32_t data_xfer;	/* RW: Data transfer		*/
	volatile uint32_t autocmd;	/* RW: Auto command control	*/
	volatile uint32_t autostat;	/* RW: Auto status control	*/
	volatile uint32_t resel;	/* RW: Reselection		*/
	volatile uint32_t select;	/* RW: Selection		*/
	volatile uint32_t prcmd;	/* WO: Processor command	*/
	volatile uint32_t auxctrl;	/* RW: Aux control		*/
	volatile uint32_t autodata;	/* RW: Auto data control	*/
	volatile uint32_t loopctrl;	/* RW: Loopback control		*/
	volatile uint32_t loopdata;	/* RW: Loopback data		*/
	volatile uint32_t identify;	/* WO: Identify (?)		*/
	volatile uint32_t complete;	/* WO: Command complete (?)	*/
	volatile uint32_t scsi_status;	/* WO: SCSI status (?)		*/
	volatile uint32_t data;		/* RW: Data register (?)	*/
	volatile uint32_t icond;	/* RO: Interrupt condition	*/
	volatile uint32_t fastwide;	/* RW: Fast/wide enable		*/
	volatile uint32_t exctrl;	/* RW: Extended control		*/
	volatile uint32_t exstat;	/* RW: Extended status		*/
	volatile uint32_t test;		/* RW: SPIFI test register	*/
	volatile uint32_t quematch;	/* RW: Queue match		*/
	volatile uint32_t quecode;	/* RW: Queue code		*/
	volatile uint32_t quetag;	/* RW: Queue tag		*/
	volatile uint32_t quepage;	/* RW: Queue page		*/
	uint32_t image[88];		/* (image of the above)		*/
	struct {
		volatile uint32_t cdb[12]; /* RW: Command descriptor block */
		volatile uint32_t quecode; /* RW: Queue code		*/
		volatile uint32_t quetag;  /* RW: Queue tag		*/
		volatile uint32_t idmsg;   /* RW: Identify message     	*/
		volatile uint32_t status;  /* RW: SCSI status		*/
	} cmbuf[8];
};

/* spstat */
#define SPS_IDLE	0x00
#define SPS_SEL		0x01
#define SPS_ARB		0x02
#define SPS_RESEL	0x03
#define SPS_MSGOUT	0x04
#define SPS_COMMAND	0x05
#define SPS_DISCON	0x06
#define SPS_NXIN	0x07
#define SPS_INTR	0x08
#define SPS_NXOUT	0x09
#define SPS_CCOMP	0x0a
#define SPS_SVPTR	0x0b
#define SPS_STATUS	0x0c
#define SPS_MSGIN	0x0d
#define SPS_DATAOUT	0x0e
#define SPS_DATAIN	0x0f

/* cmlen */
#define CML_LENMASK	0x0f
#define CML_AMSG_EN	0x40
#define CML_ACOM_EN	0x80

/* intr and imask */
#define INTR_BSRQ	0x01
#define INTR_COMRECV	0x02
#define INTR_PERR	0x04
#define INTR_TIMEO	0x08
#define INTR_DERR	0x10
#define INTR_TGSEL	0x20
#define INTR_DISCON	0x40
#define INTR_FCOMP	0x80

#define INTR_BITMASK \
    "\20\10FCOMP\07DISCON\06TGSEL\05DERR\04TIMEO\03PERR\02COMRECV\01BSRQ"

/* prstat */
#define PRS_IO		0x08
#define PRS_CD		0x10
#define PRS_MSG		0x20
#define PRS_ATN		0x40
#define PRS_Z		0x80
#define PRS_PHASE	(PRS_MSG | PRS_CD | PRS_IO)

#define PRS_BITMASK "\20\10Z\07ATN\06MSG\05CD\04IO"

/* init_status */
#define IST_ACK		0x40

/* fifoctrl */
#define FIFOC_FSLOT	0x0f	/* Free slots in FIFO */
#define FIFOC_SSTKACT	0x10	/* Synchronous stack active (?) */
#define FIFOC_RQOVRN	0x20
#define FIFOC_CLREVEN	0x00
#define FIFOC_CLRODD	0x40
#define FIFOC_FLUSH	0x80
#define FIFOC_LOAD	0xc0

/* config */
#define CONFIG_PGENEN	0x08	/* Parity generation enable */
#define CONFIG_PCHKEN	0x10	/* Parity checking enable */
#define CONFIG_WORDEN	0x20
#define CONFIG_AUTOID	0x40
#define CONFIG_DMABURST	0x80

/* select */
#define SEL_SETATN	0x02
#define SEL_IRESELEN	0x04
#define SEL_ISTART	0x08
#define SEL_WATN	0x80

/* prcmd */
#define PRC_DATAOUT	0
#define PRC_DATAIN	1
#define PRC_COMMAND	2
#define PRC_STATUS	3
#define PRC_TRPAD	4
#define PRC_MSGOUT	6
#define PRC_MSGIN	7
#define PRC_KILLREQ	0x08
#define PRC_CLRACK	0x10
#define PRC_NJMP	0x80

/* auxctrl */
#define AUXCTRL_DMAEDGE	0x04
#define AUXCTRL_SETRST	0x20	/* Bus reset (?) */
#define AUXCTRL_CRST	0x40
#define AUXCTRL_SRST	0x80

/* autodata */
#define ADATA_IN	0x40
#define ADATA_EN	0x80

/* icond */
#define ICOND_ADATAOFF	0x02
#define ICOND_AMSGOFF	0x06
#define ICOND_ACMDOFF	0x0a
#define ICOND_ASTATOFF	0x0e
#define ICOND_SVPTEXP	0x10
#define ICOND_ADATAMIS	0x20
#define ICOND_CNTZERO	0x40
#define ICOND_UXPHASEZ	0x80
#define ICOND_UXPHASENZ	0x81
#define ICOND_NXTREQ	0xa0
#define ICOND_UKMSGZ	0xc0
#define ICOND_UKMSGNZ	0xc1
#define ICOND_UBF	0xe0	/* Unexpected bus free */

/* fastwide */
#define FAST_FASTEN	0x01

/* exctrl */
#define EXC_IPLOCK	0x04	/* Initiator page lock */

/* exstat */
#define EXS_UBF		0x08	/* Unexpected bus free */
```

### spifi.c
```C
/* Copyright (c) 2000 Tsubai Masanari.  All rights reserved. */

#include <sys/cdefs.h>
__KERNEL_RCSID(0, "$NetBSD: spifi.c,v 1.20 2018/10/14 00:10:11 tsutsui Exp $");

#include <sys/param.h>
#include <sys/buf.h>
#include <sys/device.h>
#include <sys/errno.h>
#include <sys/kernel.h>
#include <sys/queue.h>
#include <sys/systm.h>

#include <uvm/uvm_extern.h>

#include <dev/scsipi/scsi_all.h>
#include <dev/scsipi/scsi_message.h>
#include <dev/scsipi/scsipi_all.h>
#include <dev/scsipi/scsiconf.h>

#include <newsmips/apbus/apbusvar.h>
#include <newsmips/apbus/spifireg.h>
#include <newsmips/apbus/dmac3reg.h>
#include <newsmips/apbus/dmac3var.h>

#include <machine/adrsmap.h>

/* #define SPIFI_DEBUG */

#ifdef SPIFI_DEBUG
# define DPRINTF printf
#else
# define DPRINTF while (0) printf
#endif

// SCB definition
struct spifi_scb {
	TAILQ_ENTRY(spifi_scb) chain;
	int flags;
	struct scsipi_xfer *xs;
	struct scsipi_generic cmd;
	int cmdlen;
	int resid;
	vaddr_t daddr;
	uint8_t target;
	uint8_t lun;
	uint8_t lun_targ;
	uint8_t status;
};
/* scb flags */
#define SPIFI_READ	0x80
#define SPIFI_DMA	0x01

// Software-defined controller for the SPIFI
struct spifi_softc {
	device_t sc_dev;
	struct scsipi_channel sc_channel;
	struct scsipi_adapter sc_adapter;

	struct spifi_reg *sc_reg;
	struct spifi_scb *sc_nexus;
	void *sc_dma;			/* attached DMA softc */
	int sc_id;			/* my SCSI ID */
	int sc_msgout;
	uint8_t sc_omsg[16];
	struct spifi_scb sc_scb[16];
	TAILQ_HEAD(, spifi_scb) free_scb;
	TAILQ_HEAD(, spifi_scb) ready_scb;
};

#define SPIFI_SYNC_OFFSET_MAX	7

// Commands (cmbuf)
#define SEND_REJECT	1
#define SEND_IDENTIFY	2
#define SEND_SDTR	4

// SCSI phase definitions from prstat
#define SPIFI_DATAOUT	0
#define SPIFI_DATAIN	PRS_IO
#define SPIFI_COMMAND	PRS_CD
#define SPIFI_STATUS	(PRS_CD | PRS_IO)
#define SPIFI_MSGOUT	(PRS_MSG | PRS_CD)
#define SPIFI_MSGIN	(PRS_MSG | PRS_CD | PRS_IO)

int spifi_match(device_t, cfdata_t, void *);
void spifi_attach(device_t, device_t, void *);

void spifi_scsipi_request(struct scsipi_channel *, scsipi_adapter_req_t,
    void *);
struct spifi_scb *spifi_get_scb(struct spifi_softc *);
void spifi_free_scb(struct spifi_softc *, struct spifi_scb *);
int spifi_poll(struct spifi_softc *);
void spifi_minphys(struct buf *);

void spifi_sched(struct spifi_softc *);
int spifi_intr(void *);
void spifi_pmatch(struct spifi_softc *);

void spifi_select(struct spifi_softc *);
void spifi_sendmsg(struct spifi_softc *, int);
void spifi_command(struct spifi_softc *);
void spifi_data_io(struct spifi_softc *);
void spifi_status(struct spifi_softc *);
int spifi_done(struct spifi_softc *);
void spifi_fifo_drain(struct spifi_softc *);
void spifi_reset(struct spifi_softc *);
void spifi_bus_reset(struct spifi_softc *);

static int spifi_read_count(struct spifi_reg *);
static void spifi_write_count(struct spifi_reg *, int);

// Shortcuts for setting the DMAC3 into SPIFI comms mode and back
#define DMAC3_FASTACCESS(sc)  dmac3_misc((sc)->sc_dma, DMAC3_CONF_FASTACCESS)
#define DMAC3_SLOWACCESS(sc)  dmac3_misc((sc)->sc_dma, DMAC3_CONF_SLOWACCESS)

// Link the device with the methods used to match and attach it
CFATTACH_DECL_NEW(spifi, sizeof(struct spifi_softc),
    spifi_match, spifi_attach, NULL, NULL);

/**
 * Check if specified device is SPIFI (during AP-Bus init)
 */
int
spifi_match(device_t parent, cfdata_t cf, void *aux)
{
	struct apbus_attach_args *apa = aux;

	if (strcmp(apa->apa_name, "spifi") == 0)
		return 1;

	return 0;
}

/**
 * Init SPIFI softc once match is found
 */
void
spifi_attach(device_t parent, device_t self, void *aux)
{
	struct spifi_softc *sc = device_private(self);
	struct apbus_attach_args *apa = aux;
	struct dmac3_softc *dma;
	int intr, i;

	sc->sc_dev = self;

	/* Initialize scbs. */
	TAILQ_INIT(&sc->free_scb);
	TAILQ_INIT(&sc->ready_scb);
	for (i = 0; i < __arraycount(sc->sc_scb); i++)
		TAILQ_INSERT_TAIL(&sc->free_scb, &sc->sc_scb[i], chain);

	sc->sc_reg = (struct spifi_reg *)apa->apa_hwbase; // Register file starts at APbus base address
	sc->sc_id = 7; // On NEWS platforms, SPIFI is always ID 7

	/* Find my dmac3. */
	dma = dmac3_link(apa->apa_ctlnum);
	if (dma == NULL) {
		aprint_error(": cannot find slave dmac\n");
		return;
	}
	sc->sc_dma = dma;

    // Print out attach message
    // On my 5000X:
    // spifi0 at ap0 slot0 addr 0xbe280000: SCSI ID = 7, using dmac0
    // scsibus0 at spifi0: 8 targets, 8 luns per target
    // spifi1 at ap0 slot0 addr 0xbe380000: SCSI ID = 7, using dmac1
    // scsibus1 at spifi1: 8 targets, 8 luns per target
	aprint_normal(" slot%d addr 0x%lx", apa->apa_slotno, apa->apa_hwbase);
	aprint_normal(": SCSI ID = %d, using %s\n",
	    sc->sc_id, device_xname(dma->sc_dev));

    // Reset sequence (happens after DMAC attach, so this resets DMAC again
	dmac3_reset(sc->sc_dma);

    // Reset the SPIFI itself.
    // This is the first example of how a SPIFI transaction works
    // The requester must set the DMAC3 into SLOWACCESS mode, send the SPIFI command, then switch back to FASTACCESS mode.
    // The SPIFI transactions might all go through the DMAC3 if it is also acting as the APbus interface for the SPIFI chips.
    // Note that this would match the other APbus devices, which are all normal, off-the-shelf devices (SONIC, ESCC, etc) paired with an AP-Bus interface (WSC-SONIC3, WSC-ESCCF, etc).
	DMAC3_SLOWACCESS(sc);
	spifi_reset(sc);
	DMAC3_FASTACCESS(sc);

    // Initial SPIFI configuration to tell the kernel the specs of the
	// SCSI controller as well as the methods to call when it needs to
	// start a SCSI transaction.
	sc->sc_adapter.adapt_dev = self;
	sc->sc_adapter.adapt_nchannels = 1;
	sc->sc_adapter.adapt_openings = 7;
	sc->sc_adapter.adapt_max_periph = 1;
	sc->sc_adapter.adapt_ioctl = NULL;
	sc->sc_adapter.adapt_minphys = minphys;
	sc->sc_adapter.adapt_request = spifi_scsipi_request; // This is what the kernel will call when it wants the SPIFI to do something

	// Set the rest of the channel parameters
	memset(&sc->sc_channel, 0, sizeof(sc->sc_channel));
	sc->sc_channel.chan_adapter = &sc->sc_adapter;
	sc->sc_channel.chan_bustype = &scsi_bustype;
	sc->sc_channel.chan_channel = 0;
	sc->sc_channel.chan_ntargets = 8;
	sc->sc_channel.chan_nluns = 8;
	sc->sc_channel.chan_id = sc->sc_id;

    // The interrupt used depends on the APbus slot. SPIFI on slot 0 will share the DMAC's interrupt. Presumably, off-board SPIFIs from APbus expansion cards don't, but I don't know yet how that works. TBD
	if (apa->apa_slotno == 0)
		intr = NEWS5000_INT0_DMAC;	/* XXX news4000 */
	else
		intr = SLOTTOMASK(apa->apa_slotno);
	apbus_intr_establish(0, intr, 0, spifi_intr, sc, device_xname(self),
	    apa->apa_ctlnum);

	config_found(self, &sc->sc_channel, scsiprint);
}

/*
 * Handle a new SCSI request from the kernel
 * 
 * See the [NetBSD man page](https://man.netbsd.org/scsipi.9) for 
 * more information about the SCSI subsystem.
 */
spifi_scsipi_request(struct scsipi_channel *chan, scsipi_adapter_req_t req, void *arg)
{
	struct scsipi_xfer *xs;
	struct scsipi_periph *periph;
	struct spifi_softc *sc = device_private(chan->chan_adapter->adapt_dev);
	struct spifi_scb *scb;
	u_int flags;
	int s;

	switch (req) {
	case ADAPTER_REQ_RUN_XFER:
		xs = arg; // kernel passes in the transfer details as the argument for this request type
		periph = xs->xs_periph; // Set the target

		DPRINTF("spifi_scsi_cmd\n");

	    /* 
		 * Pull the flags out from the request. Per NetBSD man page, the possible flags are:
		 * XS_CTL_POLL: poll in the HBA driver for request completion (most likely 
		 *              because interrupts are disabled)
         * XS_CTL_RESET: reset the device
         * XS_CTL_DATA_UIO: xs_data points to a struct uio buffer
    	 * XS_CTL_DATA_IN: data is transferred from HBA to memory
         * XS_CTL_DATA_OUT: data is transferred from memory to HBA
         * XS_CTL_DISCOVERY: this xfer object is part of a device discovery done by the 
		 *                   middle layer
         * XS_CTL_REQSENSE: xfer is a request sense
		 */
		flags = xs->xs_control; // Pull the flags out from the request

		scb = spifi_get_scb(sc); // Get the SCB needed for the request
		if (scb == NULL) {
			panic("spifi_scsipi_request: no scb");
		}

		scb->xs = xs; // xs = scsipi_xfer = command send from high-level SCSI layer to the driver
		scb->flags = 0;
		scb->status = 0;
		scb->daddr = (vaddr_t)xs->data; // Virtual address for DMA
		scb->resid = xs->datalen; // length in bytes
		memcpy(&scb->cmd, xs->cmd, xs->cmdlen); // Copy command from request to the SCB
		scb->cmdlen = xs->cmdlen; // Length of the command to execute

		// Set target data
		scb->target = periph->periph_target;
		scb->lun = periph->periph_lun;
		scb->lun_targ = scb->target | (scb->lun << 3);

		if (flags & XS_CTL_DATA_IN) // HBA -> memory
			scb->flags |= SPIFI_READ;

		s = splbio(); // Disable mass-storage interrupts

		// Add to the end of the list of SCBs to be executed
		TAILQ_INSERT_TAIL(&sc->ready_scb, scb, chain);

		// If it wasn't already running, run the function that actually does the SPIFI command scheduling
		if (sc->sc_nexus == NULL)	/* IDLE */
			spifi_sched(sc);

		splx(s); // Restore mass-storage interrupts if previously enabled

		/*
		 * If the kernel requested the operation to be done with polling (interrupts were already disabled, etc),
		 * then call spifi_poll instead of waiting for the interrupt handler to complete the request.
		 */
		if (flags & XS_CTL_POLL) {
			if (spifi_poll(sc)) {
				printf("spifi: timeout\n");
				if (spifi_poll(sc))
					printf("spifi: timeout again\n");
			}
		}
		return;
	case ADAPTER_REQ_GROW_RESOURCES:
		/* XXX Not supported. */
		return;
	case ADAPTER_REQ_SET_XFER_MODE:
		/* XXX Not supported. */
		return;
	}
}

/*
 * Get the first free SCB and remove it from the list of free SCBs so it can be used for a transfer
 */
struct spifi_scb *
spifi_get_scb(struct spifi_softc *sc)
{
	struct spifi_scb *scb;
	int s;

	s = splbio();
	scb = TAILQ_FIRST(&sc->free_scb);
	if (scb)
		TAILQ_REMOVE(&sc->free_scb, scb, chain);
	splx(s);

	return scb;
}

/*
 * Release the specified SCB back into the pool of free SCBs that can be used for future transfers
 */
void
spifi_free_scb(struct spifi_softc *sc, struct spifi_scb *scb)
{
	int s;

	s = splbio();
	TAILQ_INSERT_HEAD(&sc->free_scb, scb, chain);
	splx(s);
}

/*
 * Poll the SPIFI instead of waiting for an interrupt. This appears to be non-functional and just waits
 * for awhile before returning the status as complete (error would have to be detected and handled upstream
 * if the requested operation didn't actually complete)
 */
int
spifi_poll(struct spifi_softc *sc)
{
	struct spifi_scb *scb = sc->sc_nexus; // Currently executing SCB
	struct scsipi_xfer *xs;
	int count;

	printf("%s: not implemented yet\n", __func__);
	delay(10000);
	scb->status = SCSI_OK;
	scb->resid = 0;
	spifi_done(sc);
	return 0;

	// Below this comment is unreachable code
	if (xs == NULL)
		return 0;

	// Get the active transfer and its associated timeout
	xs = scb->xs;
	count = xs->timeout;

	/* 
	 * Until the timeout is complete, ping the DMAC3's interrupt status bit
	 * If it is set, that means that the SPIFI has completed the transfer and it is time
	 * to handle the results (which can be done by manually invoking the interrupt handler
	 * since the transaction flow should be the same).
	 */
	while (count > 0) {
		if (dmac3_intr(sc->sc_dma) != 0)
			spifi_intr(sc);

		if (xs->xs_status & XS_STS_DONE)
			return 0;
		DELAY(1000);
		count--;
	};
	return 1;
}

/*
 * Trim buffer bp to the max size allowed for SPIFI transfers
 */
void
spifi_minphys(struct buf *bp)
{

	if (bp->b_bcount > 64 * 1024)
		bp->b_bcount = 64 * 1024;

	minphys(bp);
}

void
spifi_sched(struct spifi_softc *sc)
{
	struct spifi_scb *scb;
	
	// Get the first waiting SCB
	scb = TAILQ_FIRST(&sc->ready_scb);
start:
	if (scb == NULL || sc->sc_nexus != NULL)
		return;
#if 0
	if (sc->sc_targets[scb->target] & (1 << scb->lun))
		goto next;
#endif
	TAILQ_REMOVE(&sc->ready_scb, scb, chain);

#ifdef SPIFI_DEBUG
{
	int i;

	printf("spifi_sched: ID:LUN = %d:%d, ", scb->target, scb->lun);
	printf("cmd = 0x%x", scb->cmd.opcode);
	for (i = 0; i < 5; i++)
		printf(" 0x%x", scb->cmd.bytes[i]);
	printf("\n");
}
#endif

	DMAC3_SLOWACCESS(sc);
	sc->sc_nexus = scb; // Set the nexus to the next SCB
	spifi_select(sc); // Run the selected SCB
	DMAC3_FASTACCESS(sc);

	scb = scb->chain.tqe_next; // grab the next scb (if it exists, will check @ start)
	goto start;
}

/*
 * Get the full count by assembling it from the 3 count registers
 */
static inline int
spifi_read_count(struct spifi_reg *reg)
{
	int count;

	count = (reg->count_hi  & 0xff) << 16 |
		(reg->count_mid & 0xff) <<  8 |
		(reg->count_low & 0xff);
	return count;
}

/*
 * Set the full count by disassembling it into the 3 count registers
 */
static inline void
spifi_write_count(struct spifi_reg *reg, int count)
{

	reg->count_hi  = count >> 16;
	reg->count_mid = count >> 8;
	reg->count_low = count;
}


#ifdef SPIFI_DEBUG
static const char scsi_phase_name[][8] = {
	"DATAOUT", "DATAIN", "COMMAND", "STATUS",
	"", "", "MSGOUT", "MSGIN"
};
#endif

/*
 * Handle the results from a SPIFI request once it signals it has completed via an interrupt.
 */
int
spifi_intr(void *v)
{
	struct spifi_softc *sc = v; // SPIFI controller that set the interrupt
	struct spifi_reg *reg = sc->sc_reg;
	int intr, state, icond;
	struct spifi_scb *scb;
	struct scsipi_xfer *xs;
#ifdef SPIFI_DEBUG
	char bitmask[64];
#endif

	// Check the DMAC3 interrupt status
	switch (dmac3_intr(sc->sc_dma)) {
	case 0:
		DPRINTF("spurious DMA intr\n");
		return 0;
	case -1:
		// If the DMAC3 reported a parity error, then send the TRPAD command
		// to the SPIFI3. I have no idea what that does (beyond the obvious of padding the data somehow).
		printf("DMAC parity error, data PAD\n");

		DMAC3_SLOWACCESS(sc);
		reg->prcmd = PRC_TRPAD;
		DMAC3_FASTACCESS(sc);
		return 1;

	default:
		break;
	}

	// Set the DMAC3 into SPIFI access mode
	DMAC3_SLOWACCESS(sc);

	intr = reg->intr & 0xff;
	if (intr == 0) {
		DMAC3_FASTACCESS(sc);
		DPRINTF("spurious intr (not me)\n");
		return 0;
	}

	// Now that we are here, we know we got a real SPIFI interrupt, so now we need to decode the results
	scb = sc->sc_nexus; // Currently executing SCB
	xs = scb->xs; // Currently executing command
	state = reg->spstat; // SCSI phase
	icond = reg->icond; // Granular interrupt data

	/* clear interrupt */
	reg->intr = ~intr;

#ifdef SPIFI_DEBUG
	snprintb(bitmask, sizeof bitmask, INTR_BITMASK, intr);
	printf("spifi_intr intr = %s (%s), ", bitmask,
		scsi_phase_name[(reg->prstat >> 3) & 7]);
	printf("state = 0x%x, icond = 0x%x\n", state, icond);
#endif

	if (intr & INTR_FCOMP) { // Transfer completed
		spifi_fifo_drain(sc); // Drain the data FIFO to ensure all data is transferred
		scb->status = reg->cmbuf[scb->target].status; // Pull the status out of the corresponding command buffer
		scb->resid = spifi_read_count(reg); // Get the count of the read

		DPRINTF("datalen = %d, resid = %d, status = 0x%x\n",
			xs->datalen, scb->resid, scb->status);
		DPRINTF("msg = 0x%x\n", reg->cmbuf[sc->sc_id].cdb[0]);

		DMAC3_FASTACCESS(sc);
		spifi_done(sc); // Mark the transfer complete!
		return 1;
	}
	if (intr & INTR_DISCON) // Unexpected disconnect, kill the kernel
		panic("%s: disconnect", __func__);

	if (intr & INTR_TIMEO) { // Request timed out, set the error so the kernel can handle it appropriately
		xs->error = XS_SELTIMEOUT;
		DMAC3_FASTACCESS(sc);
		spifi_done(sc);
		return 1;
	}
	if (intr & INTR_BSRQ) { // Some other kind of interrupt
		if (scb == NULL) // No currently executing command, we don't know what the SPIFI is asking for here, so panic
			panic("%s: reconnect?", __func__); // NEWS-OS might have a different way of handling this

		if (intr & INTR_PERR) { // Parity error, signal the error to the kernel
			printf("%s: %d:%d parity error\n",
			     device_xname(sc->sc_dev),
			     scb->target, scb->lun);

			/* XXX reset */
			xs->error = XS_DRIVER_STUFFUP;
			spifi_done(sc);
			return 1;
		}

		if (state >> 4 == SPS_MSGIN && icond == ICOND_NXTREQ) // Some other error that kills the kernel
			panic("%s: NXTREQ", __func__);
		if (reg->fifoctrl & FIFOC_RQOVRN) // Some other error that kills the kernel (RQOVRN = Request overrun?? Receive queue overrun??)
			panic("%s: RQOVRN", __func__);
		if (icond == ICOND_UXPHASEZ) // Some other error that kills the kernel? Unexpected phase Z?
			panic("ICOND_UXPHASEZ");

		if ((icond & 0x0f) == ICOND_ADATAOFF) { // Autodata complete, need to handle it with the spifi_data_io method
			spifi_data_io(sc);
			goto done;
		}
		if ((icond & 0xf0) == ICOND_UBF) { // Unexpected bus free, clear the UBF bit from the exstat register since we are about to handle it, then do a pmatch operation
			reg->exstat = reg->exstat & ~EXS_UBF;
			spifi_pmatch(sc);
			goto done;
		}

		/*
		 * XXX Work around the SPIFI bug that interrupts during
		 * XXX dataout phase.
		 */
		if (state == ((SPS_DATAOUT << 4) | SPS_INTR) &&
		    (reg->prstat & PRS_PHASE) == SPIFI_DATAOUT) {
			reg->prcmd = PRC_DATAOUT; // Just go back to the dataout phase
			goto done;
		}
		if ((reg->prstat & PRS_Z) == 0) { // PRS_Z state (????), do a pmatch operation
			spifi_pmatch(sc);
			goto done;
		}

		panic("%s: unknown intr state", __func__); // If we get here, the SPIFI did something unexpected
	}

done:
	DMAC3_FASTACCESS(sc);
	return 1;
}

/*
 * Execute a SPIFI operation based on the current phase of execution
 */
void
spifi_pmatch(struct spifi_softc *sc)
{
	struct spifi_reg *reg = sc->sc_reg;
	int phase;

	phase = (reg->prstat & PRS_PHASE); // Determine the current bus phase

#ifdef SPIFI_DEBUG
	printf("%s (%s)\n", __func__, scsi_phase_name[phase >> 3]);
#endif

	switch (phase) {

	case SPIFI_COMMAND:
		spifi_command(sc); // SPIFI is ready to receive a command, send it.
		break;
	case SPIFI_DATAIN:
	case SPIFI_DATAOUT:
		spifi_data_io(sc); // SPIFI expects a data transfer
		break;
	case SPIFI_STATUS:
		spifi_status(sc); // SPIFI is reporting a status change
		break;

	case SPIFI_MSGIN:	/* XXX */
	case SPIFI_MSGOUT:	/* XXX */
	default:
		printf("spifi: unknown phase %d\n", phase);
	}
}

/*
 * Select the target of the current SCB and send an identify message
 */
void
spifi_select(struct spifi_softc *sc)
{
	struct spifi_reg *reg = sc->sc_reg;
	struct spifi_scb *scb = sc->sc_nexus;
	int sel;

#if 0
	if (reg->loopdata || reg->intr)
		return;
#endif

	// No command pending?
	if (scb == NULL) {
		printf("%s: spifi_select: NULL nexus\n",
		    device_xname(sc->sc_dev));
		return;
	}

	// What is this locking? Does it stop the SPIFI from responding to targets or something?
	reg->exctrl = EXC_IPLOCK;

	// Reset the DMAC3
	dmac3_reset(sc->sc_dma);

	// Determine what the select register needs to be in order to target the desired peripheral
	sel = scb->target << 4 | SEL_ISTART | SEL_IRESELEN | SEL_WATN;

	// Load the SPIFI with the Identify message
	spifi_sendmsg(sc, SEND_IDENTIFY);

	// Trigger the command with the identify message
	// This will pull the command out of the initiator's slot in the command buffer
	// after selecting the target specified by sel
	reg->select = sel;
}

/*
 * Populate cmbuf with a message for the SPIFI to process. The command will go into the buffer
 * in the slot correponding to the SCSI ID of the initiator (in this case, the SPIFI ID, 7).
 */
void
spifi_sendmsg(struct spifi_softc *sc, int msg)
{
	struct spifi_scb *scb = sc->sc_nexus; // Currently executing command
	/* struct mesh_tinfo *ti; */
	int lun, len, i;

	int id = sc->sc_id; // ID of the initiator (always 7 on NEWS platforms)
	struct spifi_reg *reg = sc->sc_reg;

	DPRINTF("%s: sending", __func__);
	sc->sc_msgout = msg; // Set message we are sending
	len = 0;

	if (msg & SEND_REJECT) { // Rejection message
		DPRINTF(" REJECT");
		sc->sc_omsg[len++] = MSG_MESSAGE_REJECT; // Construct the message
	}
	if (msg & SEND_IDENTIFY) { // Identify message
		DPRINTF(" IDENTIFY");
		lun = scb->xs->xs_periph->periph_lun; // Extract the LUN we are targeting
		sc->sc_omsg[len++] = MSG_IDENTIFY(lun, 0); // Construct the message
	}
	if (msg & SEND_SDTR) { // Synchronous data transfer request, unimplemented
		DPRINTF(" SDTR");
#if 0
		ti = &sc->sc_tinfo[scb->target];
		sc->sc_omsg[len++] = MSG_EXTENDED;
		sc->sc_omsg[len++] = 3;
		sc->sc_omsg[len++] = MSG_EXT_SDTR;
		sc->sc_omsg[len++] = ti->period;
		sc->sc_omsg[len++] = ti->offset;
#endif
	}
	DPRINTF("\n");

	// Set the length of the command and set the AMSG_EN bit (probably to signal valid command??? What does the A stand for?)
	reg->cmlen = CML_AMSG_EN | len;

	// Copy the command from the software-defined controller into the SPIFI's command buffer in the initiator's slot
	for (i = 0; i < len; i++)
		reg->cmbuf[id].cdb[i] = sc->sc_omsg[i];
}

/*
 * Populate cmbuf with a message for the SPIFI to process. The command will go into the buffer
 * in the slot correponding to the SCSI ID of the initiator (in this case, the SPIFI ID, 7).
 */
void
spifi_command(struct spifi_softc *sc)
{
	struct spifi_scb *scb = sc->sc_nexus;
	struct spifi_reg *reg = sc->sc_reg;
	int len = scb->cmdlen;
	uint8_t *cmdp = (uint8_t *)&scb->cmd;
	int i;

	DPRINTF("%s\n", __func__);

	// Tell SPIFI the LUN being targeted
	reg->cmdpage = scb->lun_targ;

	// If SPIFI has asserted the init ACK signal, negate it.
	if (reg->init_status & IST_ACK) {
		/* Negate ACK. */
		reg->prcmd = PRC_NJMP | PRC_CLRACK | PRC_COMMAND;
		reg->prcmd = PRC_NJMP | PRC_COMMAND; // NJMP = don't execute command???
	}

	reg->cmlen = CML_AMSG_EN | len; // Set command length

	// Copy command from softc to SPIFI's command buffer (ID 7)
	for (i = 0; i < len; i++)
		reg->cmbuf[sc->sc_id].cdb[i] = *cmdp++;

	// Trigger command by asserting COMMAND in prcmd (notably, this would also deassert NJMP)
	reg->prcmd = PRC_COMMAND;
}

/*
 * Start data I/O phase
 */
void
spifi_data_io(struct spifi_softc *sc)
{
	struct spifi_scb *scb = sc->sc_nexus;
	struct spifi_reg *reg = sc->sc_reg;
	int phase;

	DPRINTF("%s\n", __func__);

	// Get the current SCSI phase and reset the DMAC3
	phase = reg->prstat & PRS_PHASE;
	dmac3_reset(sc->sc_dma);

	// Set the count register (?)
	spifi_write_count(reg, scb->resid);
	reg->cmlen = CML_AMSG_EN | 1; // length of 1
	reg->data_xfer = 0; // Clear data_xfer (?)

	scb->flags |= SPIFI_DMA; // Set the DMA flag in the SCB
	if (phase == SPIFI_DATAIN) { // HBA -> host
		if (reg->fifoctrl & FIFOC_SSTKACT) { // TBD: What is the synchronous stack? How is it written? Is this for when synchronous transfers are active (unsupported atm?)
			/*
			 * Clear FIFO and load the contents of synchronous
			 * stack into the FIFO.
			 */
			reg->fifoctrl = FIFOC_CLREVEN;
			reg->fifoctrl = FIFOC_LOAD;
		}
		reg->autodata = ADATA_IN | scb->lun_targ; // Automatically recieve data from lun_targ?
		dmac3_start(sc->sc_dma, scb->daddr, scb->resid, DMAC3_CSR_RECV); // Start DMAC
		reg->prcmd = PRC_DATAIN; // Start data receive phase
	} else { // host -> HBA
		reg->fifoctrl = FIFOC_CLREVEN; // clear FIFO
		reg->autodata = scb->lun_targ; // automatically send data to lun_targ?
		dmac3_start(sc->sc_dma, scb->daddr, scb->resid, DMAC3_CSR_SEND); // Start DMAC
		reg->prcmd = PRC_DATAOUT; // Start data transmit phase
	}
}

/*
 * Get current SPIFI status
 */
void
spifi_status(struct spifi_softc *sc)
{
	struct spifi_reg *reg = sc->sc_reg;

	DPRINTF("%s\n", __func__);
	spifi_fifo_drain(sc);
	reg->cmlen = CML_AMSG_EN | 1;
	reg->prcmd = PRC_STATUS;
}

/*
 * Signal the end of a transfer
 */
int
spifi_done(struct spifi_softc *sc)
{
	struct spifi_scb *scb = sc->sc_nexus;
	struct scsipi_xfer *xs = scb->xs;

	DPRINTF("%s\n", __func__);

	// Check if we errored out
	xs->status = scb->status;
	if (xs->status == SCSI_CHECK) {
		DPRINTF("%s: CHECK CONDITION\n", __func__);
		if (xs->error == XS_NOERROR)
			xs->error = XS_BUSY;
	}

	// Set the transfer resid (difference between datalen and actual transfer count)
	xs->resid = scb->resid;

	// Trigger callback to SCSI middle layer with results
	scsipi_done(xs);

	// Release the SCB, we don't need it anymore
	spifi_free_scb(sc, scb);

	sc->sc_nexus = NULL;
	spifi_sched(sc); // If we have another pending command, kick it off

	return false;
}

/*
 * Tell the SPIFI to flush its FIFO
 */
void
spifi_fifo_drain(struct spifi_softc *sc)
{
	struct spifi_scb *scb = sc->sc_nexus;
	struct spifi_reg *reg = sc->sc_reg;
	int fifoctrl, fifo_count;

	DPRINTF("%s\n", __func__);

	if ((scb->flags & SPIFI_READ) == 0) // Reading data from SPIFI - don't flush FIFO
		return;

	fifoctrl = reg->fifoctrl;
	if (fifoctrl & FIFOC_SSTKACT) // Synchronous stack is active - don't flush FIFO
		return;

	// Get count of data in FIFO
	fifo_count = 8 - (fifoctrl & FIFOC_FSLOT);

	// If there is data in the FIFO and we are doing a DMA transfer, flush the FIFO so we don't lose data
	if (fifo_count > 0 && (scb->flags & SPIFI_DMA)) {
		/* Flush data still in FIFO. */
		reg->fifoctrl = FIFOC_FLUSH;
		return;
	}

	// Otherwise, just dump the data in the FIFO
	reg->fifoctrl = FIFOC_CLREVEN;
}

/*
 * Reset the specified SPIFI
 */
void
spifi_reset(struct spifi_softc *sc)
{
	struct spifi_reg *reg = sc->sc_reg;
	int id = sc->sc_id;

	DPRINTF("%s\n", __func__);

	reg->auxctrl = AUXCTRL_SRST;
	reg->auxctrl = AUXCTRL_CRST;

	dmac3_reset(sc->sc_dma);

	reg->auxctrl = AUXCTRL_SRST;
	reg->auxctrl = AUXCTRL_CRST;
	reg->auxctrl = AUXCTRL_DMAEDGE;

	/* Mask (only) target mode interrupts. */
	reg->imask = INTR_TGSEL | INTR_COMRECV;

	reg->config = CONFIG_DMABURST | CONFIG_PCHKEN | CONFIG_PGENEN | id; // Configure DMA burst mode, parity generation and checking, and set the initiator ID to 7.
	reg->fastwide = FAST_FASTEN; // Enable SCSI-2/fastwide mode where possible
	reg->prctrl = 0; // Zero out the control register
	reg->loopctrl = 0; // Zero out the loopctrl register (loopback?)

	/* Enable automatic status input except the initiator. */
	reg->autostat = ~(1 << id); // What does autostat do?

	reg->fifoctrl = FIFOC_CLREVEN; // Clear FIFO
	spifi_write_count(reg, 0); // Clear count

	/* Flush write buffer. */
	(void)reg->spstat;
}

/*
 * Force a SCSI bus reset
 */
void
spifi_bus_reset(struct spifi_softc *sc)
{
	struct spifi_reg *reg = sc->sc_reg;

	printf("%s: bus reset\n", device_xname(sc->sc_dev));

	sc->sc_nexus = NULL;

	reg->auxctrl = AUXCTRL_SETRST;
	delay(100);
	reg->auxctrl = 0;
}

#if 0
static uint8_t spifi_sync_period[] = {
/* 0    1    2    3   4   5   6   7   8   9  10  11 */
 137, 125, 112, 100, 87, 75, 62, 50, 43, 37, 31, 25
};

void
spifi_setsync(struct spifi_softc *sc, struct spifi_tinfo *ti) // Change the sync period???
{

	if ((ti->flags & T_SYNCMODE) == 0)
		reg->data_xfer = 0;
	else {
		uint8_t period = ti->period;
		uint8_t offset = ti->offset;
		int v;

		for (v = sizeof(spifi_sync_period) - 1; v >= 0; v--)
			if (spifi_sync_period[v] >= period)
				break;
		if (v == -1)
			reg->data_xfer = 0;			/* XXX */
		else
			reg->data_xfer = v << 4 | offset;
	}
}
#endif
```

## SPIFI transaction log from MAME (MROM SCSI probe)
 ```
<basic init>
[:dmac] dmac0 ictl_w: 0x202 <- Enable DMAC0 interrupt and EOPIE interrupt
[:dmac] dmac0 cnf_w: 0x20 <- SLOWACCESS for SPIFI register rw
[:scsi0:7:spifi3] write spifi_reg.auxctrl = 0x40 <- CRST
[:scsi0:7:spifi3] read spifi_reg.scsi_status = 0x1 <- read scsistatus and check if 0x1 - if so, SPIFI is alive. If this is 0, the SCSI buses, DMACs, and SPIFIs will not enumerate
[:dmac] dmac1 ictl_w: 0x202 < Enable DMAC1 interrupt and EOPIE interrupt
[:dmac] dmac1 cnf_w: 0x20 <- SLOWACCESS for SPIFI register rw
[:scsi1:7:spifi3] write spifi_reg.auxctrl = 0x40 <- CRST
[:scsi1:7:spifi3] read spifi_reg.scsi_status = 0x1 <- scsi status check

<repeat previous section - stability/bugs? NetBSD code mentions a few issues>
[:dmac] dmac0 ictl_w: 0x202
[:dmac] dmac0 cnf_w: 0x20
[:scsi0:7:spifi3] write spifi_reg.auxctrl = 0x40
[:scsi0:7:spifi3] read spifi_reg.scsi_status = 0x1
[:dmac] dmac1 ictl_w: 0x202
[:dmac] dmac1 cnf_w: 0x20
[:scsi1:7:spifi3] write spifi_reg.auxctrl = 0x40
[:scsi1:7:spifi3] read spifi_reg.scsi_status = 0x1

<restore default mode>
[:dmac] dmac0 ictl_w: 0x202
[:dmac] dmac0 cnf_w: 0x1
[:dmac] dmac1 ictl_w: 0x202
[:dmac] dmac1 cnf_w: 0x1
 *
 beginning of example DMAC+SPIFI transaction (running dl from the MROM)
 [:dmac] dmac0 cnf_w: 0x20 <- Set DMAC to SLOWACCESS (SPIFI register mode)
[:scsi0:7:spifi3] write spifi_reg.auxctrl = 0x80 <- SRST (does it automatically clear these bits?)
[:dmac] dmac0 cnf_w: 0x1 <-Set DMAC to FASTACCESS (normal mode)
[:dmac] dmac0 cnf_w: 0x20
[:scsi0:7:spifi3] write spifi_reg.auxctrl = 0x40 <- CRST (does it automatically clear these bits?)
[:dmac] dmac0 cnf_w: 0x1
[:dmac] dmac0 cnf_w: 0x20
[:scsi0:7:spifi3] write spifi_reg.auxctrl = 0x20 <- SETRST (does it automatically clear these bits?)
[:dmac] dmac0 cnf_w: 0x1
[:dmac] dmac0 cnf_w: 0x20
[:scsi0:7:spifi3] write spifi_reg.auxctrl = 0x0 <- clear AUXCTRL register
[:dmac] dmac0 cnf_w: 0x1
[:dmac] dmac0 cnf_w: 0x20
[:scsi0:7:spifi3] write spifi_reg.auxctrl = 0x80 <- set SRST (does it automatically clear these bits, or is low = reset?)
[:dmac] dmac0 cnf_w: 0x1
[:dmac] dmac0 cnf_w: 0x20
[:scsi0:7:spifi3] write spifi_reg.auxctrl = 0x40 <- set CRST (does it automatically clear these bits, or is low = reset?)
[:dmac] dmac0 cnf_w: 0x1
[:dmac] dmac0 cnf_w: 0x20
[:scsi0:7:spifi3] write spifi_reg.auxctrl = 0x4 <- set DMAEDGE
[:dmac] dmac0 cnf_w: 0x1
[:dmac] dmac0 cnf_w: 0x20
[:scsi0:7:spifi3] write spifi_reg.imask = 0x22 <- mask target mode interrupts (COMRECV and TGSEL) (NetBSD masks these too)
[:dmac] dmac0 cnf_w: 0x1
[:dmac] dmac0 cnf_w: 0x20
[:scsi0:7:spifi3] write spifi_reg.config = 0xf <- set config to PGENEN [3] (parity generation enable), and IID (initiator SCSI ID) [2-0]. NetBSD also enables PCHKEN (parity checking)
[:dmac] dmac0 cnf_w: 0x1
[:dmac] dmac0 cnf_w: 0x20
[:scsi0:7:spifi3] write spifi_reg.fastwide = 0x0 <- fastwide mode disable (netbsd enables this)
[:dmac] dmac0 cnf_w: 0x1
[:dmac] dmac0 cnf_w: 0x20
[:scsi0:7:spifi3] write spifi_reg.prctrl = 0x0 <-no extra processor options (matches netbsd)
[:dmac] dmac0 cnf_w: 0x1
[:dmac] dmac0 cnf_w: 0x20
[:scsi0:7:spifi3] write spifireg.loopctrl = 0x0 <- no loopback (matches netbsd)
[:dmac] dmac0 cnf_w: 0x1
[:] LED_DISK: ON
[:dmac] dmac0 cnf_w: 0x20
[:scsi0:7:spifi3] read spifi_reg.spstat = 0x380 <- need to determine what the value of this register should be
[:dmac] dmac0 cnf_w: 0x1
[:dmac] dmac0 ictl_r: 0x202 <- waiting for interrupt (watching bit 0 of ictl)
<hangs here>
```
