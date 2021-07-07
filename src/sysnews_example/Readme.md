# `sysnews_example`
This program demonstrates how to make NEWS-specific system calls from a C program.

To use, run the following commands:
```sh
$ cc sysnews.c -o sysnews
$ ./sysnews
```

This should result in output like the below.
```
Active NEWS-OS Version: NEWS-OS Release 4.2.1R FCS#2 #0: Mon Jun 28 20:27:05 JST 1993
    root@wsrel11:/MAKE4.XR/src/sys/NEWS5000

NEWS Machine ID
  Model name: 33
  Model code: 7
  Serial number: <your system's serial number>
  Reserved[0]: 0
  Reserved[1]: 0
NEWS Machine Type Data
  Model name = NWS-5000
  Machine name = news5000
  CPU = r4000
  I/O Processor = none
  Floating point Processor = r4010
  Data cache size = 1048576
  Instruction cache size = 1048576
  Cache control data = 0
  Reserved = 0
NEWS Machine Parameters
  Physical memory size = 67108864
  Avaliable mem = 60776448
  Max users = 128
  CPU speed = 37
  Boot device = 1342205952
  Boot switch settings = 0
  Reserved[1] = 0
  Reserved[2] = 0
Sysctld info: 65536
```

