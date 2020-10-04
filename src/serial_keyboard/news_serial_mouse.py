import argparse
import functools
import binascii

# 3rd-party libraries
# Run `pip install pyserial mouse` to install
import time

import serial
import mouse


class NewsSerialKeyboardConverter:
    """
    Class for running an interactive session that takes characters and transcodes them to NEWS keyboard characters.

    The NWS-5000X (and other NEWS machines) use a TTL serial keyboard and mouse. This can be wired up to a USB->TTY
    serial adapter to use a modern PC as a NEWS mouse if, like me, you don't have a compatible serial mouse.

    3-byte mouse protocol spec (NEWS-OS 4.2.1aR) from /sys/newsapbus/msreg.h:
    #define MS_S_BYTE	0		/* start byte */
    #define MS_X_BYTE	1		/* second byte */
    #define MS_Y_BYTE	2		/* third byte */
    #define MS_DB_SIZE	3

    #define MS_S_MARK	0x80		/* start mark (first byte)*/
    #define MS_S_X7		0x08		/* MSB(sign bit) of X */
    #define MS_S_Y7		0x10		/* MSB(sign bit) of Y */
    #define MS_S_SW1	0x01		/* left button is pressed */
    #define MS_S_SW2	0x02		/* right button is pressed */
    #define MS_S_SW3	0x04		/* middle button is pressed */

    #define MS_X_X06	0x7f		/* data bits of X (second byte) */
    #define MS_Y_Y06	0x7f		/* data bits of Y (third byte) */
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
        self.prev_x = 0
        self.prev_y = 0

    def handle_mouse_event(self, sp, event):
        start_byte = self.MS_S_MARK
        x_data = b'\x00'
        y_data = b'\x00'
        if type(event) == mouse.ButtonEvent and event.event_type == "down":
            if event.button == 'left':
                code = self.MS_S_LEFT
            elif event.button == 'right':
                code = self.MS_S_RIGHT
            else:
                code = self.MS_S_MIDDLE
            start_byte = bytes([start_byte[0] | code[0]])
        if type(event) == mouse.MoveEvent:
            dx = event.x - self.prev_x
            dy = event.y - self.prev_y
            self.prev_x = event.x
            self.prev_y = event.y
            if dx > 127:
                dx = 127
            elif dx < -128:
                dx = -128
            if dy > 127:
                dy = 127
            elif dy < -128:
                dy = -128
            if dx < 0:
                start_byte = bytes([start_byte[0] | self.MS_S_X7[0]])
                dx *= -1
            if dy < 0:
                start_byte = bytes([start_byte[0] | self.MS_S_Y7[0]])
                dy *= -1
            x_data = bytes([self.MS_DATA[0] & bytes([dx])[0]])
            y_data = bytes([self.MS_DATA[0] & bytes([dy])[0]])
        # print("Sending {}".format(binascii.hexlify(start_byte + x_data + y_data)))
        sp.write(start_byte + x_data + y_data)

    def main(self):
        with serial.Serial(self.news_sp, 1200, write_timeout=0) as sp:
            try:
                mouse.hook(functools.partial(self.handle_mouse_event, sp))
                while True:
                    time.sleep(1.0)
            finally:
                mouse.unhook_all()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("serial_port", help="Path to USB->TTL device (like /dev/ttyUSB0)")
    args = parser.parse_args()
    NewsSerialKeyboardConverter(args.serial_port).main()
