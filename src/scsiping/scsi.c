/*
 * SONY NEWS SCSIデバイス情報表示プログラム
 * Program to display SCSI Device information for Sony NEWS workstations
 *
 * kurita@nippon-control-system.co.jp
 *
 * 取扱は GPL(GNU Public License) に準じます。
 *
 * $Id: scsi.c,v 0.7 1994/02/14 08:36:40 kurita Exp $
 *
 * Change log:
 * 2021/05/01 (briceonk) - Convert file to UTF-8
 * 2021/05/02 (briceonk) - Tab to space, formatting unification
 * 2021/05/02 (briceonk) - Add English translation of function docstrings
 */

#ifndef lint
static char rcsid[] = "@(#)$Id: scsi.c,v 0.7 1994/02/14 08:36:40 kurita Exp $";
#endif

#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/ioctl.h>
#ifdef __svr4
#include <sys/dkio.h>
#include <sys/scu.h>
#include <sys/sdreg.h>
#include <sys/scsireg.h>
#else /* __svr4  */
#include <newsiodev/dkio.h>
#include <newsiodev/scu.h>
#if defined(__news5900) || defined(__news5000) || defined(__news3100)
#include <newsapbus/sdreg.h>
#include <newsapbus/scsireg.h>
#else /*    HAVE AP_BUS */
#include <newsiodev/sdreg.h>
#include <newsiodev/scsireg.h>
#endif /*   HAVE AP_BUS */
#endif /*   __svr4  */

/* MODE SENSE コマンドのレスポンスデータ構造 */
typedef struct
{
    u_char len;        /* 00 データ長 */
    u_char type;       /* 01 メディアタイプ */
    u_char spec;       /* 02 device specific */
    u_char page;       /* 03 ページ  */
    u_int denc : 8;    /* 04 デンシティコード  */
    u_int nblock : 24; /* 05 ブロック数  */
    u_int r1 : 8;      /* 08  */
    u_int bsize : 24;  /* 09 ブロックサイズ  */
    u_char buf[256];   /* 12 ページデータ  */
} MSENS_RES;

/* MODE SENSE PAGE2 (format page) 構造 */
typedef struct
{
    u_short zone;    /* 00 ゾーンあたりのトラック数 */
    u_short asect;   /* 02 ゾーンあたりの代替セクタ数 */
    u_short atrack;  /* 04 ゾーンあたりの代替トラック数 */
    u_short autrack; /* 06 ユニットあたりの代替トラック数 */
    u_short nsect;   /* 08 トラックあたりのセクタ数 */
    u_short size;    /* 10 セクタサイズ */
    u_short intl;    /* 12 インターリーブファクタ */
    u_short tskew;   /* 14 トラックスキュー */
    u_short cskew;   /* 16 シリンダスキュー */
    u_short r;       /* 18 */
} PG_FMT1;

/* MODE SENSE PAGE3 (geometry page) 構造 */
typedef struct
{
    u_int ncyl : 24;   /* 00 シリンダ数 */
    u_int nhed : 8;    /* 03 ヘッド数 */
    u_int pcyl : 24;   /* 04 precomp シリンダ */
    u_int rcyl : 24;   /* 07 reduced シリンダ */
    u_int srate : 16;  /* 10 ステップレート */
    u_int lzone : 16;  /* 12 ランディングゾーン */
                       /*  u_int r1:16; */
    u_int roffset : 8; /* 14 ローテーションオフセット */
    u_int r2 : 8;      /* 15 */
    u_int rpm : 16;    /* 16 回転数 */
} PG_GEOM;

/* MODE SENSE PAGE1 (error recovery page) 構造 */
typedef struct
{
    u_int awre : 1; /* 00 Automatic Write Reallocate Enable */
    u_int arre : 1; /* 00 Automatic Read Reallocate Enable */
    u_int tb : 1;   /* 00 Transfer Block */
    u_int rc : 1;   /* 00 Read Continuous */
    u_int eer : 1;  /* 00 Enable Early Correction */
    u_int per : 1;  /* 00 Post Error */
    u_int dte : 1;  /* 00 Disable Transfer on Error */
    u_int dcr : 1;  /* 00 Disable Correction */
    u_int rcnt : 8; /* 01 Read retry count */
    u_int cspn : 8; /* 02 Correction span */
    u_int hofs : 8; /* 03 Head offset count */
    u_int dofs : 8; /* 04 Data strobe count */
    u_int wcnt : 8; /* 05 Write retry count */
    u_int rtim : 8; /* 06 Recovery time limit */
} PG_ERR;

/* SCSI INQUIRY コマンドに対するレスポンスデータ構造 */
typedef struct scsi_inqdat
{
    u_char rsvd1 : 3;     /* 00 */
    u_char dev_type : 5;  /* 00 デバイスタイプ */
    u_char dev_rmbl : 1;  /* 01 リムーバブル */
    u_char dev_mod : 1;   /* 01 デバイスモディファイア */
    u_char rsvd2 : 6;     /* 01 */
    u_char ver_iso : 2;   /* 02 ISO バージョン */
    u_char ver_ecma : 3;  /* 02 ECMA バージョン */
    u_char ver_ansi : 3;  /* 02 ANSI バージョン */
    u_char aenc : 1;      /* 03 AENC */
    u_char trmiop : 1;    /* 03 TrmIOP */
    u_char rsvd3 : 2;     /* 03 */
    u_char res_dtype : 4; /* 03 応答データ形式 */
    u_char rsvd4 : 8;     /* 04 */
    u_char dlen : 8;      /* 05 */
    u_char drinfo : 8;    /* 06 ドライブ情報 */
    u_char amode : 1;     /* 07 相対アドレスモード */
    u_char bit32 : 1;     /* 07 32ビットバス */
    u_char bit16 : 1;     /* 07 16ビットバス */
    u_char sync : 1;      /* 07 同期モード */
    u_char link : 1;      /* 07 リンク/アンリンクサポート */
    u_char rsvd5 : 1;     /* 07 */
    u_char cmd_que : 1;   /* 07 コマンドキューイング */
    u_char s_reset : 1;   /* 07 ソフトウェアリセット */
    u_char vendor[8];     /* 08 ベンダID */
    u_char prodid[16];    /* 16 プロダクトID */
    u_char revision[4];   /* 32 ファームウェアリビジョン */
} INQ_DAT;

struct sc_ureq ureq;

/*
 * MODE SENSE PAGE データを16進ダンプする
 * 入力: p  ページデータへのポインタ
 *
 * Dump the results of the MODE SENSE page command as a hex string
 * Input: p  Pointer to the MODE SENSE page data
 */
void hexdump(char *p)
{
    int i;

    printf("            ");
    for (i = 0; i < *(p + 1); i++)
    {
        printf("%2.2X ", *(p + 2 + i) & 0xff);
    }
    printf("\n");
}

/*
 * MODE SENSE コマンドを発行する
 * 入力: fd     デバイスファイルのファイルディスクリプタ
 *      pcode  読み出すページグループ(SDM_PC_xxxx)
 *
 * Execute the MODE SENSE command
 * Input: fd     Device file descriptor
 *        pcode  Page group to read (SDM_PC_XXXX)
*/
void mode_sense(int fd, int pcode)
{
    MSENS_RES *m;
    PG_ERR errpg;
    PG_FMT1 fmt1pg;
    PG_GEOM geompg;
    char buf[256];
    char *p;

    m = (MSENS_RES *)buf;
    memset(buf, 0, 255);
    ureq.scu_identify = 0xc0;
    ureq.scu_bytesec = -1;
    ureq.scu_cdb[0] = SCOP_MSENSE;
    ureq.scu_cdb[2] = pcode | SDM_PCODE_ALL;
    ureq.scu_cdb[4] = 255;
    ureq.scu_count = 255;
    ureq.scu_addr = (u_char *)buf;
    if (ioctl(fd, SCSIIOCCMD, &ureq))
    {
        perror("SCSI Mode sense");
        return;
    }
    if (pcode == SDM_PC_CUR)
    {
        printf("      Medium type: %2.2x, Device specific: %2.2x,\n", m->type, m->spec);
        printf("      Pages: %d, Dencity code: %2.2x\n", m->page, m->denc);
        printf("      Number of blocks: %d, Block size: %d\n", m->nblock, m->bsize);
    }
    p = (char *)&m->buf[0];
    switch (pcode)
    {
    case SDM_PC_CUR:
        printf("      Current page:\n");
        break;
    case SDM_PC_CHG:
        printf("      Changeable page:\n");
        break;
    case SDM_PC_DEF:
        printf("      Default page:\n");
        break;
    case SDM_PC_SAVE:
        printf("      Saved page:\n");
        break;
    }
    while (p < (char *)m + m->len)
    {
        switch (*p & SDM_PCODE_ALL)
        {
        case SDM_PG_ERR:
            memcpy(&errpg, (p + 2), sizeof(errpg));
            printf("         Error recovery parameters:\n");
            hexdump(p);
            if (*(p + 2))
            {
                printf("            ");
                if (errpg.awre)
                {
                    printf("AWRE ");
                }
                if (errpg.arre)
                {
                    printf("ARRE ");
                }
                if (errpg.tb)
                {
                    printf("TB ");
                }
                if (errpg.rc)
                {
                    printf("RC ");
                }
                if (errpg.eer)
                {
                    printf("EER ");
                }
                if (errpg.per)
                {
                    printf("PER ");
                }
                if (errpg.dte)
                {
                    printf("DTE ");
                }
                if (errpg.dcr)
                {
                    printf("DCR");
                }
                printf("\n");
            }
            printf("            Read retry count: %d, ", errpg.rcnt);
            printf("Correction span: %d, ", errpg.cspn);
            printf("Head offset count: %d\n", errpg.hofs);
            printf("            Data strobe offset: %d, ", errpg.dofs);
            printf("Write retry count: %d, ", errpg.wcnt);
            printf("Recovery time limit: %d\n", errpg.rtim);
            break;
        case SDM_PG_FMT1:
            memcpy(&fmt1pg, (p + 2), sizeof(fmt1pg));
            printf("         Format parameters 1:\n");
            hexdump(p);
            printf("            Tracs/zone: %d, ", fmt1pg.zone);
            printf("AltSect/zone: %d, ", fmt1pg.asect);
            printf("AltTrack/zone: %d, ", fmt1pg.atrack);
            printf("AltTrack/LU: %d\n", fmt1pg.autrack);
            printf("            Sect/track: %d, ", fmt1pg.nsect);
            printf("Byte/sect: %d\n", fmt1pg.size);
            printf("            InterLeave: %d, ", fmt1pg.intl);
            printf("Track skew: %d, ", fmt1pg.tskew);
            printf("Cylinder skew: %d\n", fmt1pg.cskew);
            break;
        case SDM_PG_GEOM:
            memcpy(&geompg, (p + 2), sizeof(geompg));
            printf("         Geometry parameters:\n");
            hexdump(p);
            printf("            Cylinders: %d, ", geompg.ncyl);
            printf("Head: %d, ", geompg.nhed);
            printf("rpm: %d\n", geompg.rpm);
            break;
        case SDM_PG_CNCT:
            printf("         Disconnect/reconnect controls:\n");
            hexdump(p);
            break;
        case SDM_PG_CACHE1:
            printf("         Cache controls 1:\n");
            hexdump(p);
            break;
        case SDM_PG_CACHE2:
            printf("         Cache controls 2:\n");
            hexdump(p);
            break;
        case SDM_PG_FMT2:
            printf("         Format parameters 2:\n");
            hexdump(p);
            break;
        default:
            printf("         Other page(%2.2x):\n", *p & SDM_PCODE_ALL);
            hexdump(p);
        }
        p += *(p + 1) + 2;
    }
    return;
}

/*
 * INQUIRY コマンドを発行する
 * 入力: dev    デバイスファイルのファイルディスクリプタ
 *
 * Execute the INQUIRY command
 * Input: dev  Device file descriptor
 */
void scsi_inq(int dev)
{
    static char *d_type[0x20] =
        {
            "Hard disk", "Tape drive", "Printer", "Processor",
            "WO disk", "Read only disk", "Scanner", "Optical disk",
            "Changer", "Communication", "0x0a", "0x0b", "0x0c", "0x0d", "0x0e",
            "0x0f", "0x10", "0x11", "0x12", "0x13", "0x14", "0x15", "0x16",
            "0x17", "0x18", "0x19", "0x1a", "0x1b", "0x1c", "0x1d",
            "Target", "Undefined"};
    INQ_DAT inq_dat;
    u_char temp[100];

    ureq.scu_identify = 0xc0;
    ureq.scu_bytesec = 512;
    ureq.scu_cdb[0] = SCOP_INQUIRY;
    ureq.scu_cdb[2] = 0;
    ureq.scu_cdb[3] = 0;
    ureq.scu_cdb[4] = sizeof(INQ_DAT);
    ureq.scu_addr = (u_char *)&inq_dat;
    ureq.scu_count = sizeof(INQ_DAT);

    if (ioctl(dev, SCSIIOCCMD, &ureq))
    {
        perror("SCSI Inquiry");
        return;
    }
    printf("   Inquiry:\n");
    printf("      %8.8s%16.16s%4.4s\n",
           inq_dat.vendor, inq_dat.prodid, inq_dat.revision);
    if (inq_dat.dev_type < 0x20)
    {
        printf("      %s(%2.2x)", d_type[inq_dat.dev_type], inq_dat.dev_type);
    }
    else
    {
        printf("      0x%2.2x", inq_dat.dev_type);
    }
    if (inq_dat.dev_rmbl)
    {
        printf(", removable");
    }
    printf(", SCSI%d, ECMA=%d, ISO=%d\n",
           inq_dat.ver_ansi, inq_dat.ver_ecma, inq_dat.ver_iso);
    printf("      Options: ");
    if (inq_dat.aenc)
        printf("AENC ");
    if (inq_dat.trmiop)
        printf("TrmIOP ");
    /* printf("\n応答データ形式:    0x%2.2x\n", inq_dat.res_dtype); */
    /* printf("ドライブ情報:    0x%2.2x\n", inq_dat.drinfo); */
    /* printf("相対アドレスモード: "); */
    /* print_yn(inq_dat.amode); */
    if (inq_dat.bit32)
        printf("32bit ");
    if (inq_dat.bit16)
        printf("16bit ");
    if (inq_dat.sync)
        printf("SYNC ");
    if (inq_dat.link)
        printf("LinkCtl ");
    if (inq_dat.cmd_que)
        printf("CmdQueue ");
    if (inq_dat.s_reset)
        printf("SoftReset");
    printf("\n");
}

/*
 * READ CAPACITY コマンドを発行する
 * 入力: dev    デバイスファイルのファイルディスクリプタ
 *
 * Execute the READ CAPACITY command
 * Input: dev  Device file descriptor
 */
void scsi_rcap(int dev)
{
    struct sc_rcap rcap;

    ureq.scu_identify = 0xc0;
    ureq.scu_bytesec = -1;
    ureq.scu_cdb[0] = SCOP_RCAP;
    ureq.scu_cdb[2] = 0;
    ureq.scu_cdb[3] = 0;
    ureq.scu_cdb[4] = 0;
    ureq.scu_addr = (u_char *)&rcap;
    ureq.scu_count = sizeof(struct sc_rcap);
    memset(&rcap, 0, sizeof(struct sc_rcap));

    if (ioctl(dev, SCSIIOCCMD, &ureq))
    {
        perror("SCSI Read capacity");
        return;
    }
    rcap.scr_nblock++;

    printf("   Read capacity:\n");
    printf("      %.0fbytes (", (double)rcap.scr_nblock * (double)rcap.scr_blocklen);
    printf("%dblocks, ", rcap.scr_nblock);
    printf("%dbytes/block)\n", rcap.scr_blocklen);
}

/*
 * usageメッセージを表示する
 * 入力: nam    プログラム名
 *
 * Display the usage message
 * Input: nam  Program name string
 */
void usage(char *nam)
{
    fprintf(stderr, "Usage: %s <device>...\n", nam);
}

/*
 * 指定された SCSI デバイスに対して、
 *      READ CAPACITY
 *      INQUIRY
 *      MODE SENSE
 *  コマンドを発行し、結果を標準出力に出力する。
 *  引数に SCSI デバイスのキャラクタデバイス名を指定する。
 *  例)  # scsi /dev/rsd/b0i0u0p2 /dev/rsd/b0i1u0p2
 *  もちろん、プロセスのオーナに該当デバイスのアクセス件が必要。
 *
 * Executes the READ CAPACITY, INQUIRY, and MODE SENSE commands on the
 * user-specified SCSI devices and prints the results to stdout.
 * The desired device path(s) should be passed in as an argument.
 * For example: # scsi /dev/rsd/b0i0u0p2 /dev/rsd/b0i1u0p2
 * You must have the appropriate access to the provided devices for this
 * program to function correctly.
 */
int main(int argc, char *argv[])
{
    int i;
    int fd;
    char buf[256];

    if (argc <= 1)
    {
        usage(argv[0]);
        return (1);
    }
    for (i = 1; i < argc; i++)
    {
        fd = open(argv[i], O_RDONLY);
        if (fd < 0)
        {
            sprintf(buf, "open: %s", argv[i]);
            perror(buf);
            continue;
        }
        printf("Information of %s:\n", argv[i]);
        scsi_rcap(fd);
        scsi_inq(fd);
        printf("   Mode sense:\n");
        mode_sense(fd, SDM_PC_CUR);
        mode_sense(fd, SDM_PC_CHG);
        mode_sense(fd, SDM_PC_DEF);
        mode_sense(fd, SDM_PC_SAVE);
        printf("\n\n");
        close(fd);
    }
    return (0);
}
