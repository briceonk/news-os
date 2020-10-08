#!/usr/bin/env python3
import re
import argparse
import threading
import subprocess
import time

import news_serial_kb
import news_serial_mouse


class NewsHidTranscoder:

    mouse_id_exp = re.compile(r"[m|M]ouse.+id=([0-9]+).+\[.+]")

    def __init__(self, keyboard_sp, mouse_sp, disable_local_mouse=False):
        self.keyboard_sp = keyboard_sp
        self.mouse_sp = mouse_sp
        self.disable_local_mouse = disable_local_mouse
        self.mouse_id = None

    def disable_mouse(self):
        if self.disable_local_mouse:
            xinput = subprocess.run(["xinput", "list"], capture_output=True, encoding='utf-8', check=True).stdout
            for line in xinput.splitlines():
                m = self.mouse_id_exp.search(line)
                if m and self.mouse_id is None:
                    self.mouse_id = m.group(1)
                elif m:
                    raise RuntimeError("Found multiple mice! Not sure which to disable!")

            if self.mouse_id is None:
                print("Warning: no mice found!")
            else:
                print("Disabling mouse {} locally...".format(self.mouse_id))
                subprocess.run(["xinput", "--disable", self.mouse_id], check=True)

    def enable_mouse(self):
        if self.disable_local_mouse and self.mouse_id is not None:
            subprocess.run(["xinput", "--enable", self.mouse_id])  # Not checking since there is no way to recover

    def main(self):
        self.disable_mouse()
        try:
            kb_transcoder = news_serial_kb.NewsSerialKeyboardConverter(self.keyboard_sp)
            mouse_transcoder = news_serial_mouse.NewsSerialMouseConverter(self.mouse_sp)
            kb_thread = threading.Thread(target=kb_transcoder.main)
            mouse_thread = threading.Thread(target=mouse_transcoder.main)
            kb_thread.start()
            mouse_thread.start()
            # TODO: handle quitting in a nicer way
            while True:
                try:
                    kb_thread.join()
                    mouse_thread.join()
                except KeyboardInterrupt:
                    print("Press Control+C twice more within 1 second to quit.")
                    time.sleep(1.0)
        finally:
            self.enable_mouse()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("keyboard_serial_port", help="Path to USB->TTL device connected to NEWS KB port")
    parser.add_argument("mouse_serial_port", help="Path to USB->TTL device connected to NEWS mouse port")
    parser.add_argument("--disable_local_mouse", action="store_true", default=False,
                        help="If set, will scan xinput and disable the mouse in the local X environment until the "
                             "program terminates.")
    args = parser.parse_args()
    NewsHidTranscoder(args.keyboard_serial_port, args.mouse_serial_port, args.disable_local_mouse).main()
