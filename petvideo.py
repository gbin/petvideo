#!/usr/bin/env python3

from enum import Enum
from threading import Thread

import click
import pygame
import numpy as np
import sigrok.core as sr

import pyximport
pyximport.install(setup_args={"include_dirs":np.get_include()}, reload_support=True)
from vdecode import decode, render_lock, rendered_surface, decoded_surface

INIT_WIDTH, INIT_HEIGHT = 640, 480
LA_SAMPLE_RATE = 12000000

EMULATED_SAMPLE_BUFFER_SIZE = 240000
EMULATED_DATAFEED_RATE = LA_SAMPLE_RATE // EMULATED_SAMPLE_BUFFER_SIZE

running = True
render_clock = pygame.time.Clock()
decoder_clock = pygame.time.Clock()


def _datafeed_cb(device, packet):
    if packet.type != sr.PacketType.LOGIC:
        return
    buffer = packet.payload.data
    # having a vector instead of a weird 2d buffer that sigrok gives us improves drastically the performance.
    decode(buffer.reshape((buffer.shape[0], )), decoder_clock)


def _stopped_cb():
    print('stopped')

def start_sigrok(driver: str = 'fx2lafw'):
    context = sr.Context_create()
    session = context.create_session()
    session.add_datafeed_callback(_datafeed_cb)
    session.set_stopped_callback(_stopped_cb)
    driver = context.drivers[driver]
    dev = driver.scan()[0]
    dev.open()
    dev.config_set(sr.ConfigKey.SAMPLERATE, LA_SAMPLE_RATE)
    session.add_device(dev)
    session.start()
    session.run()


def start_replay():
    replay_clock = pygame.time.Clock()
    class FakePayload:
        def __init__(self):
            self.data = None

    class FakePacket:
        def __init__(self):
            self.type = sr.PacketType.LOGIC
            self.payload = FakePayload()
    f = open('test/raw-vid-ver-hor-x-x-x-x-x.raw', 'rb')
    packet = FakePacket()

    while running:
        b = f.read(EMULATED_SAMPLE_BUFFER_SIZE)
        if len(b) == 0:
            f.seek(0)
            b = f.read(EMULATED_SAMPLE_BUFFER_SIZE)
        buffer = np.frombuffer(b, dtype=np.uint8)
        buffer = buffer.reshape((buffer.shape[0], 1))  # This emulates the shape sigrok is giving us in real life.
        packet.payload.data = buffer
        _datafeed_cb(None, packet)
        replay_clock.tick(EMULATED_DATAFEED_RATE)


@click.command()
@click.option('--test/--no-test', default=False, help='Start petvideo in replay mode.')
@click.option('--phosphore/--no-phosphore', default=False, help='Emulates a fancy phoshore effect.')
@click.option('--fps/--no-fps', default=False, help='Show the current performance of the emulator.')
def main(test: bool = False, phosphore: bool = False, fps: bool = False):

    global running

    screen_width, screen_height = INIT_WIDTH, INIT_HEIGHT

    pygame.init()
    font = pygame.font.Font('freesansbold.ttf', 10)
    screen = pygame.display.set_mode((screen_width, screen_height),
                                     pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE,
                                     8)
    pygame.display.set_caption('PET')
    pal = [(0, i, 0) for i in range(256)]
    img = pygame.Surface((625, 250), depth=8)

    if phosphore:
        img.set_alpha(100)
        prev = pygame.Surface((625, 250), depth=8)
        prev.set_palette(pal)
        prev.set_alpha(100)

    for s in (img, decoded_surface, rendered_surface):
        s.set_palette(pal)

    t = None
    if test:
        t = Thread(target=start_replay)
    else:
        t = Thread(target=start_sigrok)
    t.start()


    frame = 1
    while running:
        if fps:
            decoder_fps_txt = font.render(f'decoder {decoder_clock.get_fps():.4} fps', True, (255, 255, 255), (0, 0, 0))
            decoder_fps_txt_rect = decoder_fps_txt.get_rect()
            decoder_fps_txt_rect.topleft = (0, 0)
            render_fps_txt = font.render(f'render {render_clock.get_fps():.4} fps', True, (255, 255, 255), (0, 0, 0))
            render_fps_txt_rect = decoder_fps_txt.get_rect()
            render_fps_txt_rect.topleft = (0, decoder_fps_txt_rect.bottom)
        with render_lock:
            img.blit(rendered_surface, (0, 0), (200, 0, 625, 250))
            if phosphore:
                img.blit(prev, (0, 0))
        dst = pygame.transform.scale(img, (screen_width, screen_height))
        if phosphore:
            prev.blit(img, (0, 0))
            img.fill((0, 0, 0))
        screen.blit(dst, (0, 0))
        if fps:
            screen.blit(decoder_fps_txt, decoder_fps_txt_rect)
            screen.blit(render_fps_txt, render_fps_txt_rect)
        pygame.display.flip()

        render_clock.tick(120)

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
