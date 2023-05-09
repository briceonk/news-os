#!/usr/bin/env python3
import os
import argparse
import subprocess


class XdmcpClient:
    """Quick helper class to make it easier to launch XDMCP sessions. Uses Xephyr for the connection."""

    # Map of resolution names to sizes that Xephyr can understand
    display_resolution_map = {
        "SVGA": "800x600",
        "XGA": "1024x768",
        "WXGA": "1280x720",
        "SXGA": "1280x1024",
        "WXGA+": "1440x900",
        "HD+": "1600x900",
        "WSXGA+": "1680x1050",
        "FHD": "1920x1080",
        "QHD": "2560x1440"
    }

    def __init__(self, arg_source=None):
        self._args = self._get_arguments(arg_source)

    @classmethod
    def _generate_res_help_string(cls):
        help_str = "Options: "
        help_str += ", ".join(["{} ({})".format(k, v) for k, v in cls.display_resolution_map.items()])
        return help_str

    @classmethod
    def _get_arguments(cls, arg_source=None):
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--display_size", default="FHD", choices=cls.display_resolution_map.keys(),
                            help=cls._generate_res_help_string())
        parser.add_argument("--no_local_fonts", default=False, action="store_true",
                            help="If set, don't add ~/.local/share/fonts to X11's font path")
        parser.add_argument("--no_8bit_color", default=False, action="store_true",
                            help="If set, don't use Xephyr's 8-bit color mode")
        parser.add_argument("--display", default=":2", help="X display to create, defaults to :2")
        parser.add_argument("--no_byteswap_option", default=False, action="store_true",
                            help="If set, don't add +byteswappedclients (needed for newer Xorg versions)")
        parser.add_argument("server", help="Hostname from /etc/hosts or IP to connect to.")

        return parser.parse_args(arg_source)

    def _build_xephyr_cmd(self):
        cmd = ["Xephyr"]

        # Set client to connect to based on user input
        cmd.extend(["-query", self._args.server])

        # Set resolution to the desired size
        display_spec = self.display_resolution_map[self._args.display_size]
        if not self._args.no_8bit_color:
            display_spec += "x8"
        cmd.extend(["-screen", display_spec])

        # Set font path if needed
        # Japanese fonts must be copied from NEWS-OS to ~/.local/share/fonts for X11 to render Japanese text correctly.
        if not self._args.no_local_fonts:
            fp = subprocess.run('xset q | grep -A 1 "Font Path"',
                                shell=True, capture_output=True).stdout.split()[2].decode('utf-8')
            fp += "," + os.path.expanduser("~/.local/share/fonts")
            cmd.extend(["-fp", fp])

        # For newer Xorg servers, allow byteswapped clients
        if not self._args.no_byteswap_option:
            cmd.extend(["+byteswappedclients"])

        # Finally, set display
        cmd.extend([self._args.display])

        return cmd

    def main(self):
        subprocess.run(self._build_xephyr_cmd())


if __name__ == '__main__':
    XdmcpClient().main()
