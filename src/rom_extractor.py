#!/usr/bin/env python3
import re
import os
import sys
import logging
import hashlib
import argparse


class ImageChecksumError(Exception):
    def __init__(self, msg, chksums):
        super().__init__(msg)
        self.chksums = chksums


class MemoryExtractor:
    """
    Class with functions for saving and validating mirrored memory dumps

    There are smarter ways to do this, but it worked well enough for this purpose.
    """

    # Regular expression for parsing the output of the NEWS ROM Monitor's md command
    md_regexp = re.compile(r"([0-9a-fA-F]+): ([0-9a-fA-F]{8}) ([0-9a-fA-F]{8}) ([0-9a-fA-F]{8}) ([0-9a-fA-F]{8}) (.+)")

    def __init__(self, verbose):
        self.log = logging.getLogger()
        self._configure_logging(self.log, verbose)

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

    def extract_memory_contents(self, raw_data: list) -> dict:
        memory = {}  # This isn't the most space-efficient, but handles non-contiguous regions without much fuss
        for line in raw_data:
            match = self.md_regexp.match(line)
            if match:  # Anything that doesn't match regex due to corruption will be caught in validate_rom_backup
                addr = int(match.group(1), 16)
                val = bytearray.fromhex("".join([match.group(x) for x in range(2, 6)]))
                if len(val) != 16:
                    raise RuntimeError("Corrupt data at location {}! Data: {}".format(hex(addr), val))
                elif addr in memory and val != memory[addr]:
                    # This case handles validating redundant dumps
                    raise RuntimeError("Conflicting values found for data at location {}!".format(hex(addr)))
                memory[addr] = val

        return memory

    def validate_memory_backup(self, memory: dict, ranges: list) -> tuple:
        images = []
        for r in ranges:
            image = bytearray()
            for lw_addr in range(r[0], r[1], 16):
                try:
                    image.extend(memory[lw_addr])
                except KeyError:
                    raise KeyError("Didn't get data for address {}".format(hex(lw_addr)))
            chksum = hashlib.md5()
            chksum.update(image)
            images.append((r, chksum.hexdigest(), image))

        if not all([images[0][2] == img_data[2] for img_data in images]):
            self.log.error("Failed image verification!")
            self.log.error("Range: MD5 Checksum")
            for img_data in images:
                self.log.error("{}: {}".format(img_data[0], img_data[1]))
            raise ImageChecksumError("Failed image verification!", [imgdata[1] for imgdata in images])

        return images[0][1], images[0][2]

    def dump_memory(self, memory: dict):
        for key in sorted(memory.keys()):
            self.log.debug("{}: {}".format(hex(key), memory[key]))

    def image_debug(self, memory, start_a, start_b, length):
        for i in range(0, length, 16):
            if memory[start_a + i] != memory[start_b + i]:
                self.log.error("Offset {} mismatch! A = {} B = {}".format(hex(i), hex(memory[start_a + i]),
                                                                          hex(memory[start_b + i])))

    @staticmethod
    def write_files_to_disk(results, directory):
        for image in results:
            # Write ROM to disk
            with open(os.path.join(directory, image) + ".rom", "xb") as rom_file:
                rom_file.write(results[image][1])

            # Write ROM checksum to disk
            with open(os.path.join(directory, image) + ".md5", "x") as chksum_file:
                chksum_file.write(results[image][0] + "\n")


class NWS5000:
    """Class that uses MemoryExtractor to extract NWS-5000X read-only memory ranges"""

    # (base_address, length, [mirror_ranges_for_validation])
    nws5k_roms = {
        # Monitor ROM - 256KiB, 0x9fc00000-0x9fc3ffff, mirrored 3 times beyond base
        "monitor_rom": (0x9fc00000, 0x40000,
                        [((0x9fc00000 + 0x40000 * n), (0x9fc00000 + 0x40000 * (n + 1))) for n in range(0, 4)])
    }

    @classmethod
    def _get_arguments(cls, arg_source=None):
        parser = argparse.ArgumentParser()
        parser.add_argument("-v", "--verbose", action="count", default=0,
                            help="Control debug output level (more Vs = more output)")
        parser.add_argument("-o", "--output", default="./nws-5000x", help="Output directory")
        parser.add_argument("-r", "--roms", default="", help="Comma-delimited list of roms to dump")
        parser.add_argument("serial_log", help="Path to serial log file with NEWS md output")
        return parser.parse_args(arg_source)

    @classmethod
    def extract_mem(cls, extractor, memory, roms, results_dir):
        # Create output directory
        os.mkdir(results_dir)

        # Extract selected ROMs
        results = {}
        rom_list = cls.nws5k_roms.keys() if roms == "" else filter(lambda x: x in roms.split(","),
                                                                   cls.nws5k_roms.keys())
        for rom in rom_list:
            results[rom] = extractor.validate_memory_backup(memory, cls.nws5k_roms[rom][2])
        extractor.write_files_to_disk(results, results_dir)

    @classmethod
    def main(cls):
        args = cls._get_arguments()
        extractor = MemoryExtractor(args.verbose)
        with open(args.serial_log) as f:
            data = extractor.extract_memory_contents(f.readlines())
        cls.extract_mem(extractor, data, args.roms, args.output)


if __name__ == '__main__':
    NWS5000.main()
