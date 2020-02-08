from threading import Thread

import click
import pygame
import numpy as np
from enum import Enum
import pyximport
import numpy
pyximport.install(setup_args={"include_dirs":numpy.get_include()}, reload_support=True)
from vdecode import decode
import sigrok.core as sr

INIT_WIDTH, INIT_HEIGHT = 640, 480
EMULATED_READ_RATE = 240000

running = True
render_clock = pygame.time.Clock()
decoder_clock = pygame.time.Clock()

decoded_frames = 0
displayed_frames = 0


class DecodedSurface(object):
    def __init__(self, shape):
        self.max_width = 1000
        self.surface = pygame.Surface(shape, depth=8)


decoded_surface = DecodedSurface((3200, 500))


def _datafeed_cb(device, packet):
    global decoded_frames
    if packet.type != sr.PacketType.LOGIC:
        return
    buffer = packet.payload.data
    # having a vector instead of a weird 2d buffer that sigrok gives us improves drastically the performance.
    decode(buffer.reshape((buffer.shape[0], )), decoded_surface, decoder_clock)


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
    dev.config_set(sr.ConfigKey.SAMPLERATE, 24000000)
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
            b = f.read(EMULATED_READ_RATE)
            if len(b) == 0:
                loop += 1
                f.seek(0)
                b = f.read(EMULATED_READ_RATE)
                # print(f'replay loop {loop}')
            buffer = np.frombuffer(b, dtype=np.uint8)
            buffer = buffer.reshape((buffer.shape[0], 1))  # This emulates the shape sigrok is giving us in real life.
            packet.payload.data = buffer
            _datafeed_cb(None, packet)
    t = Thread(target=stream)
    t.start()


@click.command()
@click.option('--test/--no-test', default=False, help='Start petvideo in test mode.')
def main(test: bool = False):

    global running

    screen_width, screen_height = INIT_WIDTH, INIT_HEIGHT

    pygame.init()
    font = pygame.font.Font('freesansbold.ttf', 10)
    screen = pygame.display.set_mode((screen_width, screen_height),
                                     pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE,
                                     8)
    pygame.display.set_caption('PET')
    pygame.display.flip()
    if test:
        setup_replay()
    else:
        setup_sigrok()
    img = pygame.Surface((1050, 250),depth=8)

    frame = 1
    while running:
        decoder_fps_txt = font.render(f'decoder {decoder_clock.get_fps():.4} fps', True, (255, 255, 255), (0, 0, 0))
        decoder_fps_txt_rect = decoder_fps_txt.get_rect()
        decoder_fps_txt_rect.topleft = (0, 0)
        render_fps_txt = font.render(f'render {render_clock.get_fps():.4} fps', True, (255, 255, 255), (0, 0, 0))
        render_fps_txt_rect = decoder_fps_txt.get_rect()
        render_fps_txt_rect.topleft = (0, decoder_fps_txt_rect.bottom)
        img.blit(decoded_surface.surface, (0, 0), (400,0,1050,250))
        dst = pygame.transform.scale(img, (screen_width, screen_height))
        screen.blit(dst, (0,0))
        screen.blit(decoder_fps_txt, decoder_fps_txt_rect)
        screen.blit(render_fps_txt, render_fps_txt_rect)
        pygame.display.flip()
        render_clock.tick(30)

        frame += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
                print(f'{screen_width}, {screen_height}')
                screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
    # session.stop()


if __name__ == '__main__':
    main()
