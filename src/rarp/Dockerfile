from ubuntu:focal
RUN apt-get update && apt-get install rarpd
COPY ethers /etc/ethers

ENTRYPOINT ["/usr/sbin/rarpd", "-aeodv", "tap-mess-1000-0"]

