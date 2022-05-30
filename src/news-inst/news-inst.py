"""
news-inst: Installer script for NEWS-OS

This script provides an out-of-band method for installing NEWS-OS onto a disk image without using the native
installer binaries. This is mostly useful for creating NEWS-OS installs without the boot floppy disks or a tape drive,
since the lack of availability is an issue both for real NEWS workstations and MAME.

Requirements:
- NetBSD system or VM (Other operating systems will work out of the box only if they support vndconfig and writing FFS)
- NEWS-OS installer files
- Python3 and PyYAML

Supported installer kits:
- NWF-671C: NEWS-OS 4.1C (m68k NEWS systems, see nwf671c.yml)

Planned support for:
- NWF-683RD1: NEWS-OS 4.2.1aRD (NWS-5000/5900 series)
  The NWF-683RD1 CD-ROM is bootable, so it is much easier to use both on real and emulated NWS-5000 series systems.
  Therefore, it is lower priority.

Of course, I am more than happy to help anyone with an install kit not listed here, so feel free to contact me or file
a GitHub issue in this repository.

To run, simply run the script on a NetBSD system with the desired install kit and pointer to your machine config file.
 # /usr/pkg/bin/python3.10 news-inst.py nwf671c machconf.yml

Run the script with `-h` to see all options.

TODO:
Allow SCSI IDs other than 0
More installer options (language, timezone, etc)
"""
import os
import sys
import yaml
import logging
import argparse
import subprocess


# noinspection SpellCheckingInspection
class NEWSOSInstaller(object):
    # Supported installer kits
    # NWF-683RD1 (NEWS-OS 4.2.1aRD for NWS-5000 and 5900 series) is not supported yet
    INSTALL_KITS = ["nwf671c"]

    # Known NEWS system families (not all are supported by every install kit)
    SYSTEMS = ["nws700",  # NEWS diskless workstation (m68020)
               "nws800",  # Original NEWS workstation family (m68020, with m68020 IOP)
               "nws900",  # NEWS server (m68020, with m68020 IOP)
               "nws1200",  # NEWS laptop (m68030)
               "nws1400",  # NEWS workstation (m68030)
               "nws1500",  # NEWS workstation (m68030), also has POP variety (PWS-1500 series)
               "nws1600",  # NEWS workstation (m68030), also has POP variety (PWS-1600 series)
               "nws1700",  # NEWS workstation (m68030)
               "nws1800",  # NEWS workstation (m68030, with m68030 IOP)
               "nws1900",  # NEWS server (m68030, with m68030 IOP)
               "nws3100",  # bigNEWS laptop (R3000, APbus architecture)
               "nws3200",  # NEWS laptop (R3000)
               "nws3400",  # NEWS workstation (R3000)
               "nws3700",  # NEWS workstation (R3000)
               "nws3800",  # NEWS workstation (R3000, with m68030 IOP)
               "nws4000",  # NEWS workstation (R4600/R4700, APbus architecture)
               "nws5000",  # NEWS workstation (R4000/R4400, APbus architecture)
               "nws5900",  # NEWS server (R4400, APbus architecture)
               "nws7000"]  # Final NEWS workstation (R10000, APbus architecture)

    # loop device to create for mounting the image in NetBSD
    LOOP_DEVICE = "vnd0"

    @staticmethod
    def convert_partition_letter(newsos_letter):
        return newsos_letter if newsos_letter != "d" else "c"

    def __init__(self, dry_run: bool, verbose: int, install_kit: str,  machine_config: str, mount_point: str):
        self._dry_run = dry_run
        self._log = logging.getLogger()
        self._configure_logging(dry_run, verbose)

        # Load installer config file
        if install_kit not in self.INSTALL_KITS:
            raise ValueError("unsupported install kit provided!")
        with open(install_kit + ".yml") as config_stream:
            self.install_config = yaml.safe_load(config_stream)

        # Load machine config file
        with open(machine_config) as config_stream:
            self.machine_config = yaml.safe_load(config_stream)
        self.system = self.machine_config['system']

        if os.path.exists(mount_point):
            raise ValueError("mount_point should not already exist!")
        self.mount_point = mount_point

    def _configure_logging(self, dry_run, verbose) -> None:
        self._log.setLevel(logging.DEBUG)
        stdout_handler = logging.StreamHandler(sys.stdout)
        if dry_run or verbose > 0:
            stdout_handler.setLevel(logging.DEBUG)
        else:
            stdout_handler.setLevel(logging.INFO)
        self._log.addHandler(stdout_handler)

    def _run(self, cmd: str, check=True, cwd=None):
        self._log.debug("Running %s", cmd)
        if not self._dry_run:
            subprocess.run(cmd, shell=True, check=check, cwd=cwd)

    def _mount_image(self):
        self._run("vndconfig {} {}.img".format(self.LOOP_DEVICE, self.machine_config['disklabel']))
        for partition in sorted(self.machine_config['fstab'], key=self.machine_config['fstab'].get):
            if partition == "swap":
                pass
            else:
                mount_path = os.path.join(self.mount_point, partition) if partition != "root" else self.mount_point
                # NetBSD uses 'd' for the full-disk disklabel, NEWS-OS uses 'c'. So, we have to flip 'd'.
                partition_letter = self.convert_partition_letter(self.machine_config['fstab'][partition])
                self._run("mkdir {}".format(mount_path))
                self._run("mount /dev/{}{} {}".format(self.LOOP_DEVICE, partition_letter, mount_path))

    def _unmount_image(self):
        for partition in sorted(self.machine_config['fstab'], key=self.machine_config['fstab'].get, reverse=True):
            if partition != "swap":
                mount_path = os.path.join(self.mount_point, partition) if partition != "root" else self.mount_point
                self._run("umount {}".format(mount_path), check=False)

    def _copy_file_or_archive(self, path: str):
        # Check if Z archive?
        with open(path, "rb") as fbin:
            is_z_archive = fbin.read(1) == b'\x1f' and fbin.read(1) == b'\x9d'

        # If so, extract it to the target directory
        if is_z_archive:
            self._log.debug("Extracting %s", path)
            # Two-step cat | zcat to avoid damaging archive files on disk (even with -k, zcat can misbehave on error)
            self._run("cat {} | zcat - | tar -C {} -xf -".format(path, self.mount_point))
        # Otherwise, we'll just move it over.
        else:
            self._log.info("Copying %s", path)
            self._run("cp -a {} {}".format(path, self.mount_point))

    def _synthesize_fstab(self):
        fstab_contents = ""
        fstab_config = self.machine_config['fstab']
        counter = 2
        for partition in fstab_config:
            if partition == "swap":
                pass  # TODO: swap support
            elif partition == "root":
                fstab_contents += "/dev/sd00{} / 4.3 rw 1 1\n".format(fstab_config[partition])
            elif partition == "tmp":
                fstab_contents += "/dev/sd00{} /{} 4.3 rw,delay 1 9\n".format(fstab_config[partition], partition)
                counter += 1
            else:
                fstab_contents += "/dev/sd00{} /{} 4.3 rw 1 9\n".format(fstab_config[partition], partition)
                counter += 1

        self._log.debug("Updating fstab:\n%s", fstab_contents)
        if not self._dry_run:
            with open(os.path.join(self.mount_point, "etc/fstab"), "w") as fstab:
                fstab.write(fstab_contents)

    def _customize(self):
        self._run("sed -i 's/myname.my.domain/{}/' etc/rc.custom".format(self.machine_config['hostname']),
                  cwd=self.mount_point)
        hostname = str.split(self.machine_config['hostname'], ".")[0]
        self._run("sed -i 's/myname/{}/' etc/hosts".format(hostname), cwd=self.mount_point)
        self._run("echo '{}  {}' >> etc/hosts".format(self.machine_config['ip'], hostname), cwd=self.mount_point)
        self._run("sed -i 's/my.domain/{}/' etc/rc.custom".format(self.machine_config['domain-name']),
                  cwd=self.mount_point)
        self._run("sed -i 's/my-netmask/{}/' etc/rc.custom".format(self.machine_config['netmask']),
                  cwd=self.mount_point)
        self._run("sed -i 's/my-router/{}/' etc/rc.custom".format(self.machine_config['gateway']),
                  cwd=self.mount_point)
        self._run("sed -i 's/DM=/DM={}/' etc/rc.custom".format(self.machine_config['dm']), cwd=self.mount_point)
        self._run("sed -i 's/NET=off/NET=/' etc/rc.custom", cwd=self.mount_point)

    def install(self):
        try:
            self._log.info("Installing %s using %s", self.install_config['os-version'], self.install_config['name'])
            self._log.debug("Installer config: %s", self.install_config)
            self._log.debug("Machine config: %s", self.machine_config)

            # Remove old image, if present, then extract a new one
            disklabel = self.machine_config['disklabel']
            self._run("rm {}.img".format(disklabel), check=False)
            self._run("gunzip -ck blank-images/{}.img.gz > {}.img".format(disklabel, disklabel))

            # Set up loop device
            self._mount_image()

            # Extract install kit components
            for volume in range(1, self.install_config['volumes'] + 1):
                volume_key = "vol" + str(volume)
                volume_path = self.install_config[volume_key]['path']
                for source_file in self.install_config[volume_key]['install-files']:
                    self._copy_file_or_archive(os.path.join(volume_path, source_file))

            # Extract kernel for configured system
            kernel_path = self.install_config[self.system]['kernel']['path']
            for kernel_file in self.install_config[self.system]['kernel']['install-files']:
                self._copy_file_or_archive(os.path.join(kernel_path, kernel_file))

            # Copy system-specific files
            for system_file in self.install_config[self.system]['copy']:
                # Avoid path.join so leading / doesn't kill it
                source = os.path.normpath(self.mount_point + os.sep + system_file['source'])
                destination = os.path.normpath(self.mount_point + os.sep + system_file['destination'])
                self._run("cp -a {} {}".format(source, destination), cwd=self.mount_point)

            # Fix links
            for link_spec in self.install_config[self.system]['links']:
                cwd = os.path.join(self.mount_point, link_spec['cwd'])
                self._run("rm {}".format(link_spec['link']), check=False, cwd=cwd)
                self._run("ln -s {} {}".format(link_spec['source'], link_spec['link']), cwd=cwd)

            # Update fstab with partition mapping
            self._synthesize_fstab()

            # Make device nodes
            for device in self.install_config[self.system]['devices']:
                # Under NetBSD, mknod is stored in /sbin
                self._run("cat MAKEDEV | sed 's/etc/sbin/g' | sh -s -- {}".format(device),
                          cwd=os.path.join(self.mount_point, "dev"))

            # Customize installation with user-provided parameters
            self._customize()

        finally:
            # unmount everything
            self._unmount_image()

            # remove mount dir
            self._run("rm -r {}".format(self.mount_point), check=False)

            # remove loop device config
            self._run("vndconfig -u {}".format(self.LOOP_DEVICE), check=False)

        self._log.info("Complete! Final image: %s", self.machine_config['disklabel'] + ".img")


# noinspection SpellCheckingInspection
def script_main():
    arg_parser = argparse.ArgumentParser(description="Utility for setting up Sony NEWS-OS hard drive images")
    arg_parser.add_argument("-v", "--verbose", action="count", default=0, help="Control debug output level")
    arg_parser.add_argument("-m", "--mount_point", default="/tmp/newsos", help="Mount point for image")
    arg_parser.add_argument("-d", "--dry_run", action="store_true", default=False,
                            help="Don't actually run anything if set. Automatically enables verbose mode")
    arg_parser.add_argument("install_kit", help="Install kit code")
    arg_parser.add_argument("machine_config", help="Machine config file")
    args = arg_parser.parse_args()

    installer = NEWSOSInstaller(args.dry_run, args.verbose, args.install_kit, args.machine_config, args.mount_point)
    installer.install()


if __name__ == "__main__":
    script_main()
