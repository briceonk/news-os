#!/usr/bin/env python3
import time
import argparse
import functools
import threading

# 3rd-party libraries
# Run `pip install pyserial` to install Pyserial
# Run `git submodule init && git submodule update` to clone the modified version of mouse that uses relative instead of
# absolute positioning. Ensure that the modified version of mouse is on the path/PYTHONPATH instead of the normal mouse.
import serial
import mouse.mouse as mouse


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

    Before using this in an X-Windows environment, you can use xinput to disable the mouse on your workstation to avoid
    sending errant mouse events to random applications. Run `xinput list`, then run `xinput --disable <mouse id>`.
    Then, run this script. When done, break out of this script and run `xinput --enable <mouse id>` to restore mouse
    functionality.

    3-byte mouse protocol spec (NEWS-OS 4.2.1aR) from /sys/newsapbus/msreg.h:
    #define MS_S_BYTE   0   /* start byte */
    #define MS_X_BYTE   1   /* second byte */
    #define MS_Y_BYTE   2   /* third byte */
    #define MS_DB_SIZE  3

    #define MS_S_MARK   0x80    /* start mark (first byte)*/
    #define MS_S_X7     0x08    /* MSB(sign bit) of X */
    #define MS_S_Y7     0x10    /* MSB(sign bit) of Y */
    #define MS_S_SW1    0x01    /* left button is pressed */
    #define MS_S_SW2    0x02    /* right button is pressed */
    #define MS_S_SW3    0x04    /* middle button is pressed */

    #define MS_X_X06    0x7f    /* data bits of X (second byte) */
    #define MS_Y_Y06    0x7f    /* data bits of Y (third byte) */
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
            dx *= -1
            dx = 128 - dx  # Two's complement
        if dy < 0:
            start_byte = self.byte_or(start_byte, self.MS_S_Y7)
            dy *= -1
            dy = 128 - dy  # Two's complement
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("serial_port", help="Path to USB->TTL device (like /dev/ttyUSB0)")
    args = parser.parse_args()
    NewsSerialMouseConverter(args.serial_port).main()
