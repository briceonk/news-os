#	This is a part of scsi for NEWS-OS
#	$Id: Makefile,v 1.6 1994/02/14 04:39:11 kurita Exp $

MAKE=		make
SHELL=		/bin/sh
BINDIR=		/usr/local/bin

#uncomment under 7 lines if your os is NEWS-OS 4.2
MANSUFFIX=	8
MANPAGE=	8
MANALSO=	4
INSTALL=	install
BINGRP=	staff
MANOWN=	root
MANGRP=	staff

# comment under 7 lines if your os is NEWS-OS 4.2
#MANSUFFIX=	1m
#MANPAGE=	1M
#MANALSO=	7
#INSTALL=	/usr/ucb/install
#BINGRP=		bin
#MANOWN=		bin
#MANGRP=		bin

MANDIR=		/usr/local/man/C/man$(MANSUFFIX)
JMANDIR=	/usr/local/man/ja_JP.EUC/man$(MANSUFFIX)

CFLAGS= -O2

all:	scsi

scsi:	scsi.c
	$(CC) $(CFLAGS) -o scsi scsi.c

install:	all
	$(INSTALL) -s -m 4755 -o root -g $(BINGRP) scsi $(BINDIR)

install.man:	scsi.man scsi.jman
	sed -e 's/__MANPAGE__/$(MANPAGE)/g' \
		-e 's/__MANALSO__/$(MANALSO)/g' < scsi.man > scsi.tmp
	$(INSTALL) -c -m 744 -o $(MANOWN) -g $(MANGRP) scsi.tmp $(MANDIR)/scsi.$(MANSUFFIX)
	sed -e 's/__MANPAGE__/$(MANPAGE)/g' \
		-e 's/__MANALSO__/$(MANALSO)/g' < scsi.jman > scsi.tmp
	$(INSTALL) -c -m 744 -o $(MANOWN) -g $(MANGRP) scsi.tmp $(JMANDIR)/scsi.$(MANSUFFIX)
	rm -f scsi.tmp

clean:
	rm -f *.o *.*~ core *.tmp
