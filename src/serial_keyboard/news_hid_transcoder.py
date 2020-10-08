#!/usr/bin/env python3
import re
import time
import queue
import argparse
import functools
import threading
import subprocess

# 3rd-party libraries
# Run `pip install pyserial keyboard` to install serial and keyboard
# Run `git submodule init && git submodule update` to clone the modified version of mouse that uses relative instead of
# absolute positioning. Ensure that the modified version of mouse is on the path/PYTHONPATH instead of the normal mouse.
import serial
import keyboard
import mouse.mouse as mouse


class NewsSerialKeyboardConverter:
    """
    Class for running an interactive session that takes characters and transcodes them to NEWS keyboard characters.

    The NWS-5000X (and other NEWS machines) use a TTL serial keyboard and mouse. This can be wired up to a USB->TTY
    serial adapter to use a modern PC as a NEWS keyboard if, like me, you don't have a compatible serial keyboard.
    """

    # NWP-5461 Keycode Map (compatible with NWP-411 too)
    # See https://github.com/tmk/tmk_keyboard/tree/master/converter/news_usb
    # TODO: make this an input file, this is not good
    nwp5461_map = {
        # Power key
        'PWR': '7A',  # TODO: Select modern key for PWR
        # Function keys
        'f1': '01', 'f2': '02', 'f3': '03', 'f4': '04', 'f5': '05', 'f6': '06', 'f7': '07', 'f8': '08', 'f9': '09',
        'f10': '0A', 'f11': '68', 'f12': '69',
        # First 3 mathematical operators
        'P×': '64', 'P÷': '65', 'P+': '52',
        # Escape
        'ESC': '0B',
        # Numbers
        '1': '0C', '2': '0D', '3': '0E', '4': '0F', '5': '10', '6': '11', '7': '12', '8': '13', '9': '14', '0': '15',
        # Top row special keys  TODO: HELP
        '-': '16', '=': '17', '\\': '18', 'backspace': '19', 'HELP': '6A',
        # Top row numpad
        'P7': '4B', 'P8': '4C', 'P9': '4D', 'P-': '4E',
        # Letters and such
        'tab': '66', 'q': '1B', 'w': '1C', 'e': '1D', 'r': '1E', 't': '1F', 'y': '20', 'u': '21', 'i': '22', 'o': '23',
        'p': '24', '[': '25', ']': '26', 'delete': '27', 'insert': '6B', 'P4': '4F', 'P5': '50', 'P6': '51',
        'P,': '56',  # TODO: Is P, enough?
        'ctrl': '28',  # Left Ctrl  TODO: Left ctrl vs right ctl?
        # More letters and such
        'a': '29', 's': '2A', 'd': '2B', 'f': '2C', 'g': '2D', 'h': '2E', 'j': '2F', 'k': '30', 'l': '31', ';': '32',
        "'": '33', '`': '34', 'enter': '35', 'CLR': '6C', 'P1': '53', 'P2': '54', 'P3': '55', 'Penter': '5A',
        'shift': '36',  # Left Shift  TODO: Left shift vs right shift?
        'z': '37', 'x': '38', 'c': '39', 'v': '3A', 'b': '3B', 'n': '3C', 'm': '3D',
        ',': '3E', '.': '3F', '/': '40',
        'RO': '41',  # TODO: Find substitute for Kana `ro` key
        'Rshift': '42',  # TODO: Right shift?
        'page up': '6D', 'P0': '57', 'P.': '59', 'up': '58',
        'alt': '45',  # Left alt  TODO: Left alt vs right alt
        'caps lock': '44',
        'space': '46',
        'Ralt': '47',  # TODO: Left alt vs right alt
        'RGUI': '48', 'APP': '49', 'RCTL': '4A',  # TODO: these
        'page down': '6E', 'left': '5B', 'down': '5C', 'right': '5D'
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
            with serial.Serial(port=self.news_sp) as sp:
                while True:
                    key_input = self.in_q.get(block=True)  # type: keyboard.KeyboardEvent
                    key_name = key_input.name if not key_input.is_keypad else "P" + key_input.name
                    key_name = self.clean_key_name(key_name)
                    try:
                        news_key_code = bytes.fromhex(self.nwp5461_map[key_name])
                    except KeyError:
                        print("Warning: unimplemented key {}, scan code {}. Ignoring...".format(key_name,
                                                                                                key_input.scan_code))
                    else:
                        if key_input.event_type == "up":
                            news_key_code = bytes([b'\x80'[0] | news_key_code[0]])
                        sp.write(news_key_code)
        finally:
            keyboard.stop_recording()


class MouseState:
    def __init__(self, x=0, y=0, left=False, right=False, middle=False):
        self.x = x
        self.y = y
        self.left = left
        self.right = right
        self.middle = middle

    def copy(self):
        return MouseState(self.x, self.y, self.left, self.right, self.middle)


class NewsSerialMouseConverter:
    """
    Class for running an interactive session that takes characters and transcodes them to NEWS keyboard characters.

    The NWS-5000X (and other NEWS machines) use a TTL serial keyboard and mouse. This can be wired up to a USB->TTY
    serial adapter to use a modern PC as a NEWS mouse if, like me, you don't have a compatible serial mouse.
    3-byte mouse protocol spec can be found in /sys/newsapbus/msreg.h on NEWS-OS 4.2.1aR.
    """

    # MS_S_BYTE
    MS_S_MARK = b'\x80'
    MS_S_X7 = b'\x08'
    MS_S_Y7 = b'\x10'
    MS_S_LEFT = b'\x01'
    MS_S_RIGHT = b'\x02'
    MS_S_MIDDLE = b'\x04'
    # MS_X_BYTE, MS_Y_BYTE
    MS_DATA = b'\x7f'

    def __init__(self, sp):
        self.news_sp = sp
        self.prev = MouseState()
        self.cur = MouseState()
        self.lock = threading.Lock()

    def handle_mouse_event(self, event):
        with self.lock:
            if type(event) == mouse.ButtonEvent:
                self.cur.__setattr__(event.button, event.event_type == "down")
            elif type(event) == mouse.MoveEvent:
                self.cur.x += event.x
                self.cur.y += event.y

    @staticmethod
    def byte_or(a, b):
        return bytes([a[0] | b[0]])

    @staticmethod
    def byte_and(a, b):
        return bytes([a[0] & b[0]])

    def get_update(self):
        with self.lock:
            self.prev = self.cur.copy()
            self.cur = MouseState()

        start_byte = self.MS_S_MARK
        if self.prev.left:
            start_byte = self.byte_or(start_byte, self.MS_S_LEFT)
        if self.prev.right:
            start_byte = self.byte_or(start_byte, self.MS_S_RIGHT)
        if self.prev.middle:
            start_byte = self.byte_or(start_byte, self.MS_S_MIDDLE)

        dx = self.prev.x
        dy = self.prev.y
        if dx > 127:
            dx = 127
        elif dx < -128:
            dx = -128
        if dy > 127:
            dy = 127
        elif dy < -128:
            dy = -128
        if dx < 0:
            start_byte = self.byte_or(start_byte, self.MS_S_X7)
            dx = 128 + dx  # Two's complement
        if dy < 0:
            start_byte = self.byte_or(start_byte, self.MS_S_Y7)
            dy = 128 + dy  # Two's complement
        x_data = self.byte_and(self.MS_DATA, bytes([dx]))
        y_data = self.byte_and(self.MS_DATA, bytes([dy]))
        return start_byte + x_data + y_data

    def main(self):
        with serial.Serial(self.news_sp, 1200, write_timeout=0) as sp:
            try:
                mouse.hook(functools.partial(self.handle_mouse_event))
                while True:
                    time.sleep(0.05)  # Periodically send updates to avoid overwhelming the serial port (1200bps)
                    packet = self.get_update()
                    if packet != b'\x80\x00\x00':
                        sp.write(packet)
            finally:
                mouse.unhook_all()


class NewsHidTranscoder:
    mouse_id_exp = re.compile(r"[m|M]ouse.+id=([0-9]+).+\[.+]")

    def __init__(self, keyboard_sp, mouse_sp, disable_local_mouse=False):
        self.keyboard_sp = keyboard_sp
        self.mouse_sp = mouse_sp
        self.disable_local_mouse = disable_local_mouse
        self.mouse_id = None

    def disable_mouse(self):
        if self.disable_local_mouse and self.mouse_sp is not None:
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
            kb_thread, mouse_thread = None, None
            if self.keyboard_sp is not None:
                kb_transcoder = NewsSerialKeyboardConverter(self.keyboard_sp)
                kb_thread = threading.Thread(target=kb_transcoder.main)
                kb_thread.start()
            if self.mouse_sp is not None:
                mouse_transcoder = NewsSerialMouseConverter(self.mouse_sp)
                mouse_thread = threading.Thread(target=mouse_transcoder.main)
                mouse_thread.start()
            while True:
                try:
                    if kb_thread is not None:
                        kb_thread.join()
                    if mouse_thread is not None:
                        mouse_thread.join()
                except KeyboardInterrupt:
                    print("Press Control+C twice more within 1 second to quit.")
                    time.sleep(1.0)
        finally:
            self.enable_mouse()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")  # TODO: Fill in description
    parser.add_argument("-k", "--keyboard_serial_port", default=None,
                        help="Path to USB->TTL device connected to NEWS KB port")
    parser.add_argument("-m", "mouse_serial_port", default=None,
                        help="Path to USB->TTL device connected to NEWS mouse port")
    parser.add_argument("-d", "--disable_local_mouse", action="store_true", default=False,
                        help="If set, will scan xinput and disable the mouse in the local X environment until the "
                             "program terminates.")
    args = parser.parse_args()
    NewsHidTranscoder(args.keyboard_serial_port, args.mouse_serial_port, args.disable_local_mouse).main()
