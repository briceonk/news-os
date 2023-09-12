#!/usr/bin/env python3
import re
import time
import queue
import argparse
import threading

# 3rd-party libraries
# Run `pip install pyserial keyboard` to install serial and keyboard
# Run `git submodule init && git submodule update` to clone the modified version of mouse that uses relative instead of
# absolute positioning. Ensure that the modified version of mouse is on the path/PYTHONPATH instead of the normal mouse.
import serial
import keyboard


class MvmeSerialKeyboardConverter:
    """
    This should be in the same program as the NEWS one, but this is just a quick hack until it works
    """

    CODES = {
        "XK_Mode_switch": 0x0003,
        "XK_Num_Lock": 0x0011,
        "XK_Pause": 0x00e9,
        "XK_Shift_R": 0x004d,
        "[0]": 0x00ef,
    }

    nwp5461_map = {
        # Function keys
        'f1': 0x00f5, 'f2': 0x00f3, 'f3': 0x00f7, 'f4': 0x00e7, 'f5': 0x00f9,
        # 'f6': '06', TODO: F6?
        'f7': 0x00fb, 'f8': 0x00eb, 'f9': 0x00fd,
        'f10': 0x00ed, 'f11': 0x000f, 'f12': 0x00f1,
        # First 3 mathematical operators
        'P×': 0x0007,
        # 'P÷': '65',
        'P+': 0x000d,
        # Escape
        'esc': 0x0013,
        # Numbers
        '1': 0x00d3, '2': 0x00c3, '3': 0x00b3, '4': 0x00b5, '5': 0x00a3, '6': 0x0093, '7': 0x0085, '8': 0x0083, '9': 0x0073, '0': 0x0075,
        # Top row special keys  TODO: HELP
        '-': 0x0063, '=': 0x0055, '\\': 0x0045, 'backspace': 0x0033,
        # 'HELP': '6A',
        # Top row numpad
        'P7': 0x0027, 'P8': 0x0015, 'P9': 0x0005, 'P-': 0x0009,
        # Letters and such
        'tab': 0x00e5, 'q': 0x00d5, 'w': 0x00c5, 'e': 0x00b7, 'r': 0x00a5, 't': 0x00a7, 'y': 0x0095, 'u': 0x0087,
        'i': 94, 'o': 0x0077,
        'p': 89, '[': 0x0057, ']': 0x0049,
        # 'delete': '27', 'insert': '6B',
        'P4': 0x0029, 'P5': 0x0019, 'P6': 0x0017,
        # 'P,': '56',  # TODO: Is P, enough?
        'ctrl': 0x00d7,  # Left Ctrl  TODO: Left ctrl vs right ctl?
        # More letters and such
        'a': 0x00c7, 's': 0x00c9, 'd': 0x00b9, 'f': 0x00a9, 'g': 0x0097, 'h': 0x0099, 'j': 0x0089, 'k': 0x007b, 'l': 0x0069, ';': 0x0067,
        "'": 0x005b, '`': 0x00e3, 'enter': 86, 'CLR': '6C', 'P1': 0x002d, 'P2': 0x001b, 'P3': 0x000b,
        # 'Penter': '5A',
        'shift': 0x00db,  # Left Shift  TODO: Left shift vs right shift?
        'z': 0x00cb, 'x': 0x00bb, 'c': 0x00bd, 'v': 0x00ab, 'b': 0x009b, 'n': 0x009d, 'm': 0x008b,
        ',': 0x007d, '.': 0x006d, '/': 0x006b,
        # 'RO': '41',  # TODO: Find substitute for Kana `ro` key
        # 'Rshift': '42',  # TODO: Right shift?
        # 'page up': '6D',
        'P0': 0x001f,
        'P.': 0x001d,
        # 'up': '58',
        'alt': 0x00dd,  # Left alt
        'caps lock': 0x004f,
        'space': 0x00ad,
        'Ralt': 0x008d,  # right alt
        # 'RGUI': '48', 'APP': '49', 'RCTL': '4A',  # TODO: these
        # 'page down': '6E', 'left': '5B', 'down': '5C', 'right': '5D'
    }

    def __init__(self, sp):
        # Make queue to receive kb events
        self.in_q = queue.Queue()
        keyboard.start_recording(self.in_q)
        self.news_sp = sp

    @staticmethod
    def clean_key_name(key_name):
        # So far, only found the minus sign, but I put this into a function in case it needs to be expanded.
        result = key_name
        if key_name == b'\xe2\x88\x92'.decode("utf-8"):  # keyboard module returns some unicode - instead of ASCII
            result = "-"
        return result

    def main(self):
        try:
            with serial.Serial(port=self.news_sp, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS) as sp:
                while True:
                    key_input = self.in_q.get(block=True)  # type: keyboard.KeyboardEvent
                    key_name = key_input.name if not key_input.is_keypad else "P" + key_input.name
                    key_name = self.clean_key_name(key_name)
                    try:
                        news_key_code = self.nwp5461_map[key_name].to_bytes(2, 'big')
                    except KeyError:
                        print("Warning: unimplemented key {}, scan code {}. Ignoring...".format(key_name,
                                                                                                key_input.scan_code))
                    else:
                        if key_input.event_type == "up":
                            news_key_code = bytes([b'\x80'[0] | news_key_code[0]])
                        sp.write(news_key_code)
        finally:
            keyboard.stop_recording()


class NewsHidTranscoder:
    mouse_id_exp = re.compile(r"[m|M]ouse.+id=([0-9]+).+\[.+]")

    def __init__(self, keyboard_sp):
        self.keyboard_sp = keyboard_sp
        self.mouse_id = None

    def main(self):
        kb_thread = None
        if self.keyboard_sp is not None:
            kb_transcoder = MvmeSerialKeyboardConverter(self.keyboard_sp)
            kb_thread = threading.Thread(target=kb_transcoder.main)
            kb_thread.start()
        while True:
            try:
                if kb_thread is not None:
                    kb_thread.join()
            except KeyboardInterrupt:
                print("Press Control+C twice more within 1 second to quit.")
                time.sleep(1.0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")  # TODO: Fill in description
    parser.add_argument("-k", "--keyboard_serial_port", default=None,
                        help="Path to USB->TTL device connected to NEWS KB port")

    args = parser.parse_args()
    NewsHidTranscoder(args.keyboard_serial_port).main()
