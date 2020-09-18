# rarpd Docker container
This directory contains the files necessary to build and run an instance of
`rarpd` on a modern system. Edit `ethers` to map the Ethernet MAC address of
your workstation to the desired IP address. Then, build and run the image.

```bash
$ docker build . -t rarp:latest
$ ./start_rarpd.sh
```

Refer to the `rarpd` man page for additional setup options. This setup listens
on all interfaces and bypasses the tftp boot image processor.
