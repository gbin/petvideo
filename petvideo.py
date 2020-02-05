from threading import Thread

import pygame
import numpy as np
import sigrok.core as sr

INIT_WIDTH, INIT_HEIGHT = 640, 480

VIDEO_MASK     = 0b00000001
HOR_DRIVE_MASK = 0b00000010
VER_DRIVE_MASK = 0b00000100

raster = np.ndarray(shape=(INIT_WIDTH * INIT_HEIGHT,), dtype=np.uint8)


def _datafeed_cb(device, packet):
    if packet.type != sr.PacketType.LOGIC:
        return
    decoded_signal = np.packbits(np.bitwise_and(packet.payload.data, VIDEO_MASK))
    # incoming_length =
    # right = len(decoded_signal) + current_index if current_index +
    # raster[current_index:len(decoded_signal)] = decoded_signal
    # print(packet.payload.data)


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
    class FakePacket:
        def __init__(self):
            self.type = sr.PacketType.LOGIC
            self.payload = object()
    f = open('test/raw-vid-ver-hor-x-x-x-x-x.raw', 'rb')
    packet = FakePacket()

    def stream():
        while True:
            b = f.read(100)
            if len(b) == 0:
                f.seek(0)
                b = f.read(100)
            packet.payload.data = b
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
    pygame.init()
    screen = pygame.display.set_mode((INIT_WIDTH, INIT_HEIGHT),
                                     pygame.DOUBLEBUF | pygame.HWSURFACE,
                                     8)
    pygame.display.set_caption('PET')
    screen.fill(pygame.Color('red'))
    pygame.display.flip()

    running = True
    frame = 1
    while running:
        screen.blit(pygame.surfarray.make_surface(raster.reshape((320, 200))), (0, 0))
        pygame.display.flip()
        frame += 1
        # if not frame % 60:
        #    print(frame)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
    # session.stop()


if __name__ == '__main__':
    main()
