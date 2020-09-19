#!/usr/bin/env python3
import os
import sys
import glob
import logging
import argparse
import subprocess


class NewsImageBuilder(object):
    """
    Class for extracting Sony NEWS-OS images from an install CD-ROM.

    Extracts all archives from a NeWS OS 4.2.1aR CD-ROM - might work on similar CDs, but I don't have them to test.
    """

    # Staging path
    TEMP_MNT_PATH = "/tmp/news_iso"

    def __init__(self, verbose, cdrom_path, output_path, preserve_permissions):
        self.cdrom_path = cdrom_path
        self.output_path = output_path
        self.log = logging.getLogger()
        self._configure_logging(self.log, verbose)
        self.preserve = preserve_permissions

    @staticmethod
    def _configure_logging(log, verbose) -> None:
        log.setLevel(logging.DEBUG)
        stdout_handler = logging.StreamHandler(sys.stdout)
        if verbose == 0:
            stdout_handler.setLevel(logging.WARNING)
        elif verbose == 1:
            stdout_handler.setLevel(logging.INFO)
        else:
            stdout_handler.setLevel(logging.DEBUG)
        log.addHandler(stdout_handler)

    def transfer_files(self) -> None:
        sudo = "" if not self.preserve else "sudo"
        for f in glob.iglob(self.TEMP_MNT_PATH + '/**/**', recursive=True):
            if not os.path.isdir(f):
                # Check if Z archive?
                with open(f, "rb") as fbin:
                    is_z_archive = fbin.read(1) == b'\x1f' and fbin.read(1) == b'\x9d'

                # If so, extract it to the target directory
                # The permissions cause issues when running as non-root
                # TODO: find a better way to handle permissions!
                if is_z_archive:
                    self.log.info("Extracting {}".format(f))

                    subprocess.run("zcat {} | {} tar -C {} -xf -".format(f, sudo, self.output_path), check=True,
                                   shell=True)
                # Otherwise, we'll just move it over.
                else:
                    self.log.info("Copying {}".format(f))
                    cmd = ["cp", "{}".format(f), self.output_path]
                    if sudo != "":
                        cmd.insert(0, sudo)
                    subprocess.run(cmd, check=True)

    def build_image(self) -> None:
        try:
            # Make a temporary mount point for the ISO
            subprocess.run(["mkdir", self.TEMP_MNT_PATH], check=True)
            # Mount the ISO - need to be root :(
            subprocess.run(["sudo", "mount", self.cdrom_path, self.TEMP_MNT_PATH], check=True)
            # Create the target directory
            os.mkdir(self.output_path)
            # Extract everything
            self.transfer_files()
        finally:
            # Clean up - have to be root again :(
            subprocess.run(["sudo", "umount", self.TEMP_MNT_PATH])
            subprocess.run(["rm", "-r", self.TEMP_MNT_PATH])


if __name__ == "__main__":
    # Collect command line arguments
    arg_parser = argparse.ArgumentParser(description="Utility for extracting Sony NEWS-OS files from CD-ROM.")
    arg_parser.add_argument("-v", "--verbose", action="count", default=0,
                            help="Control debug output level (more Vs = more output)")
    arg_parser.add_argument("cdrom", help="Pointer to ISO")
    arg_parser.add_argument("-p", "--preserve", default=False, action="store_true",
                            help="If set, will not alter the original permissions. This will require the use of sudo "
                                 "for the tar and cp commands because root owns many of the files in the archive. "
                                 "Be especially careful of the output directory if using this option. By default, "
                                 "only the ISO mount command is run as sudo. If you are only extracting files to look "
                                 "at them, avoid this option.")
    # Don't change the output directory to anything important.
    arg_parser.add_argument("-o", "--output", default="/tmp/newsos", help="Output directory name")
    args = arg_parser.parse_args()
    # Make sure the user didn't try to specify the root dir, that is especially dangerous if the -p option was used
    # as it could overwrite system files (that would be no good!)
    if args.output == "/":
        raise ValueError("Cannot extract to /!")
    # Run the script
    NewsImageBuilder(args.verbose, args.cdrom, args.output, args.preserve).build_image()
