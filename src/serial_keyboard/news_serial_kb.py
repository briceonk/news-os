import queue
import argparse

# 3rd-party libraries
# Run `pip install pyserial keyboard` to install
import serial
import keyboard


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
        'P*': '64', 'P*--1÷': '65', 'P+': '52',
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

    def main(self):
        try:
            with serial.Serial(port=self.news_sp) as sp:
                while True:
                    key_input = self.in_q.get(block=True)  # type: keyboard.KeyboardEvent
                    key_name = key_input.name if not key_input.is_keypad else "P" + key_input.name
                    try:
                        news_key_code = bytes.fromhex(self.nwp5461_map[key_name])
                    except KeyError:
                        print("Warning: unimplemented key {}, scan code {}. Ignoring...".format(key_name,
                                                                                                key_input.scan_code))
                    else:
                        if key_input.event_type == "up":
                            news_key_code = bytes([b'\x80'[0] | news_key_code[0]])
                            pass
                        sp.write(news_key_code)
        finally:
            keyboard.stop_recording()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("serial_port", help="Path to USB->TTL device (like /dev/ttyUSB0)")
    args = parser.parse_args()
    NewsSerialKeyboardConverter(args.serial_port).main()
