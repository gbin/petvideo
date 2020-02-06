from threading import Thread

import pygame
import numpy as np
import sigrok.core as sr
from enum import Enum
import pyximport
import numpy
pyximport.install(setup_args={"include_dirs":numpy.get_include()}, reload_support=True)
from vdecode import decode

INIT_WIDTH, INIT_HEIGHT = 640, 480


raster = None
running = True


def init_raster(w: int, h: int):
    global raster
    raster = np.ndarray(shape=(w, h), dtype=np.uint8)


gindex = 0


def _datafeed_cb(device, packet):
    global gindex
    if packet.type != sr.PacketType.LOGIC:
        return
    decode(packet.payload.data, raster, gindex)
    gindex += len(packet.payload.data)


def _stopped_cb(**kwargs):
    print('Stopped')


def setup_sigrok(driver: str = 'fx2lafw'):
    context = sr.Context_create()
    session = context.create_session()
    session.add_datafeed_callback(_datafeed_cb)
    session.set_stopped_callback(_stopped_cb)
    driver = context.drivers[driver]
    dev = driver.scan()[0]
    dev.open()
    print(dev.config_keys())
    dev.config_set(sr.ConfigKey.SAMPLERATE, 10000)
    session.add_device(dev)
    session.start()
    t = Thread(target=session.run)
    t.start()


def setup_replay():
    class FakePayload:
        def __init__(self):
            self.data = None

    class FakePacket:
        def __init__(self):
            self.type = sr.PacketType.LOGIC
            self.payload = FakePayload()
    f = open('test/raw-vid-ver-hor-x-x-x-x-x.raw', 'rb')
    packet = FakePacket()

    def stream():
        loop = 0
        while running:
            b = f.read(1000)
            if len(b) == 0:
                loop += 1
                f.seek(0)
                b = f.read(1000)
                print(f'replay frame {loop}')
            packet.payload.data = np.frombuffer(b, dtype=np.uint8)
            _datafeed_cb(None, packet)
    t = Thread(target=stream)
    t.start()


def generate_raster():
    x = np.arange(0, 200)
    y = np.arange(0, 320)
    X, Y = np.meshgrid(x, y)
    Z = X + Y
    Z = 255 * Z / Z.max()
    return pygame.surfarray.make_surface(Z)


def main():

    global running
    screen_width, screen_height = INIT_WIDTH, INIT_HEIGHT

    init_raster(screen_width, screen_height)
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height),
                                     pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE,
                                     8)
    pygame.display.set_caption('PET')
    pygame.display.flip()
    setup_replay()

    frame = 1
    while running:
        screen.blit(pygame.surfarray.make_surface(raster), (0, 0))

        # screen.fill(pygame.Color('red'))
        pygame.display.flip()
        frame += 1
        # if not frame % 60:
        #    print(frame)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
                screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
                init_raster(screen_width, screen_height)
    # session.stop()


if __name__ == '__main__':
    main()
