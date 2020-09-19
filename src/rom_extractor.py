#!/usr/bin/env python3
import re
import os
import sys
import hashlib


class ImageChecksumError(Exception):
    def __init__(self, msg, chksums):
        super().__init__(msg)
        self.chksums = chksums


class RomValidator:
    """
    Class with functions for validating memory backups

    This should probably be less... hacky?
    """

    # Regular expression for parsing the output of the NEWS ROM Monitor's md command
    md_regexp = re.compile(r"([0-9a-fA-F]+): ([0-9a-fA-F]{8}) ([0-9a-fA-F]{8}) ([0-9a-fA-F]{8}) ([0-9a-fA-F]{8}) (.+)")

    @classmethod
    def convert_text(cls, raw_data: list) -> dict:
        memory = {}  # This isn't the most space-efficient, but handles non-contiguous regions without much fuss
        for line in raw_data:
            match = cls.md_regexp.match(line)
            if match:  # Anything that doesn't match regex due to corruption will be caught in validate_rom_backup
                addr = int(match.group(1), 16)
                val = bytearray.fromhex("".join([match.group(x) for x in range(2, 6)]))
                if len(val) != 16:
                    raise RuntimeError("Corrupt data at location {}! Data: {}".format(hex(addr), val))
                elif addr in memory and val != memory[addr]:
                    raise RuntimeError("Conflicting values found for data at location {}!".format(hex(addr)))
                memory[addr] = val

        return memory

    @staticmethod
    def validate_rom_backup(memory: dict, ranges: list) -> tuple:
        images = []
        for r in ranges:
            image = bytearray()
            print("r[0] = {}, r[1] = {}, r[1] + 16 = {}".format(hex(r[0]), hex(r[1]), hex(r[1] + 16)))
            for lw_addr in range(r[0], r[1], 16):
                try:
                    image.extend(memory[lw_addr])
                except KeyError:
                    raise KeyError("Didn't get data for address {}".format(hex(lw_addr)))
            chksum = hashlib.md5()
            chksum.update(image)
            images.append((r, chksum.hexdigest(), image))

        if not all([images[0][2] == img_data[2] for img_data in images]):
            print("Failed image verification!")
            print("Range: MD5 Checksum")
            for img_data in images:
                print("{}: {}".format(img_data[0], img_data[1]))
            raise ImageChecksumError("Failed image verification!", [imgdata[1] for imgdata in images])

        return images[0][1], images[0][2]

    @classmethod
    def dump_memory(cls, memory: dict):
        for key in sorted(memory.keys()):
            print("{}: {}".format(hex(key), memory[key]))

    @staticmethod
    def image_debug(memory, start_a, start_b, length):
        for i in range(0, length, 16):
            if memory[start_a + i] != memory[start_b + i]:
                print("Offset {} mismatch! A = {} B = {}".format(hex(i), hex(memory[start_a + i]),
                                                                 hex(memory[start_b + i])))

    @staticmethod
    def write_files_to_disk(results, directory):
        for image in results:
            # Write ROM to disk
            with open(os.path.join(directory, image) + ".rom", "xb") as rom_file:
                rom_file.write(results[image][1])

            # Write ROM checksum to disk
            with open(os.path.join(directory, image) + ".md5", "x") as rom_file:
                rom_file.write(results[image][0])


def nws_5000x(memory):
    results = {}
    results_dir = "./nws-5000x"
    os.mkdir(results_dir)

    # Monitor ROM
    mrom_base_address, mrom_length = 0x9fc00000, 0x3FFF0  # 256kB ROM
    mrom_mirrors = [((mrom_base_address + (mrom_length + 16) * n),
                     (mrom_base_address + (mrom_length + 16) * (n + 1)))
                    for n in range(0, 4)]  # Mirrored 3 additional times
    results["monitor_rom"] = RomValidator.validate_rom_backup(memory, mrom_mirrors)

    RomValidator.write_files_to_disk(results, results_dir)


if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        data = RomValidator.convert_text(f.readlines())
    nws_5000x(data)
