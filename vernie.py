# coding=utf-8
import hashlib
import os
import re
import subprocess

import gtts
import six

from pylgbst import *

forward = FORWARD = right = RIGHT = 1
backward = BACKWARD = left = LEFT = -1
straight = STRAIGHT = 0


def say(text):
    if isinstance(text, str):
        text = text.decode("utf-8")
    md5 = hashlib.md5(text.encode('utf-8')).hexdigest()
    fname = "/tmp/%s.mp3" % md5
    if not os.path.exists(fname):
        myre = re.compile('[[A-Za-z]', re.UNICODE)
        lang = 'en' if myre.match(text) else 'ru'

        logging.getLogger('requests').setLevel(logging.getLogger('').getEffectiveLevel())
        tts = gtts.gTTS(text=text, lang=lang, slow=False)
        tts.save(fname)

    with open(os.devnull, 'w') as fnull:
        subprocess.call("mplayer %s" % fname, shell=True, stderr=fnull, stdout=fnull)


class Vernie(MoveHub):
    def __init__(self):
        try:
            conn = DebugServerConnection()
        except BaseException:
            logging.debug("Failed to use debug server: %s", traceback.format_exc())
            conn = BLEConnection().connect()

        super(Vernie, self).__init__(conn)

        while True:
            required_devices = (self.color_distance_sensor, self.motor_external)
            if None not in required_devices:
                break
            log.debug("Waiting for required devices to appear: %s", required_devices)
            time.sleep(1)

        self._head_position = 0
        self.motor_external.subscribe(self._external_motor_data)

        self._color_detected = COLOR_NONE
        self._sensor_distance = 10
        self.color_distance_sensor.subscribe(self._color_distance_data)

        time.sleep(1)
        self._reset_head()
        time.sleep(1)
        log.info("Vernie is ready.")

    def _external_motor_data(self, data):
        log.debug("External motor position: %s", data)
        self._head_position = data

    def _color_distance_data(self, color, distance):
        log.debug("Color & Distance data: %s %s", COLORS[color], distance)
        self._sensor_distance = distance
        self._color_detected = color

    def _reset_head(self):
        self.motor_external.timed(1, -0.2)
        self.head(RIGHT, angle=45)

    def head(self, direction=RIGHT, angle=25, speed=0.1):
        if direction == STRAIGHT:
            angle = -self._head_position
            direction = 1

        self.motor_external.angled(direction * angle, speed)

    def turn(self, direction, degrees=90, speed=0.3):
        self.head(STRAIGHT, speed=1)
        self.head(direction, 35, 1)
        self.motor_AB.angled(225 * degrees / 90, speed * direction, -speed * direction)
        self.head(STRAIGHT, speed=1)

    def move(self, direction, distance=1, speed=0.3):
        self.head(STRAIGHT, speed=0.5)
        self.motor_AB.angled(distance * 450, speed * direction, speed * direction)

    def program_carton_board(self):
        self.move(FORWARD)
        self.move(FORWARD)
        self.turn(RIGHT)
        self.move(FORWARD)
        self.turn(LEFT)
        self.move(FORWARD)
        self.turn(RIGHT)
        self.move(BACKWARD)
        self.move(BACKWARD)
        self.turn(LEFT)
        self.move(FORWARD)
        self.move(FORWARD)
        self.turn(RIGHT)
        self.move(FORWARD)
        self.turn(RIGHT)
        self.move(FORWARD, 3)
        self.turn(LEFT)
        self.turn(LEFT)
        self.move(BACKWARD, 2)

    def read_typed_commands(self):
        say("Печатайте команды")
        while True:
            cmd = six.moves.input("COMMAND >")
            cmd = cmd.split(' ')
            if cmd[0].lower() in ("head", "голова", "голова"):
                if cmd[-1] in ("right", "вправо", "направо"):
                    say("ok")
                    self.head(RIGHT)
                elif cmd[-1] in ("left", "влево", "налево"):
                    say("ok")
                    self.head(LEFT)
                else:
                    say("ok")
                    self.head(STRAIGHT)
            elif cmd[0].lower() in ("say", "скажи", "сказать"):
                say(' '.join(cmd[1:]))
            elif cmd[0].lower() in ("forward", "вперёд", "вперед"):
                try:
                    dist = int(cmd[-1])
                except:
                    dist = 1
                say("ok")
                self.move(FORWARD, distance=dist)
            elif cmd[0].lower() in ("backward", "назад"):
                try:
                    dist = int(cmd[-1])
                except:
                    dist = 1
                say("ok")
                self.move(BACKWARD, distance=dist)
            elif cmd[0].lower() in ("turn", "поворот", 'повернуть'):
                if cmd[-1] in ("right", "вправо", "направо"):
                    say("ok")
                    self.turn(RIGHT)
                elif cmd[-1] in ("left", "влево", "налево"):
                    say("ok")
                    self.turn(LEFT)
                else:
                    say("ok")
                    self.turn(RIGHT, degrees=360)
            else:
                say("Неизвестная команда")
                say("Доступные команды это:")
                say("вперёд, назад, поворот влево, поворот вправо, голову влево, голову вправо, голову прямо, скажи")
                say("Печатайте команды")


# TODO: distance sensor game
# TODO: find and follow the lightest direction game

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    comms.log.setLevel(logging.INFO)

    vernie = Vernie()
    say("Робот Веернии 01 готов к работе")
    vernie.read_typed_commands()
