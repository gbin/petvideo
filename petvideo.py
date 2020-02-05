from threading import Thread

import pygame
import numpy as np
import sigrok.core as sr

pygame.init()
width, height = 320, 200
screen = pygame.display.set_mode((width, height),
                                 pygame.DOUBLEBUF | pygame.HWSURFACE,
                                 8)
pygame.display.set_caption('PET')

VIDEO_MASK = 1
HOR_DRIVE_MASK = 2
VER_DRIVE_MASK = 4

raster = np.ndarray(shape=(320*200, ), dtype=np.uint8)
current_index = 0

def _datafeed_cb(device, packet):
    if packet.type != sr.PacketType.LOGIC:
        return
    decoded_signal = np.packbits(np.bitwise_and(packet.payload.data, VIDEO_MASK))
    # incoming_length =
    #right = len(decoded_signal) + current_index if current_index +
    raster[current_index:len(decoded_signal)] = decoded_signal
    # print(packet.payload.data)


def _stopped_cb(**kwargs):
    print('Stopped')


context = sr.Context_create()
session = context.create_session()
session.add_datafeed_callback(_datafeed_cb)
session.set_stopped_callback(_stopped_cb)
driver = context.drivers['demo']  #fx2lafw
dev = driver.scan()[0]
dev.open()
print(dev.config_keys())
dev.config_set(sr.ConfigKey.SAMPLERATE, 10000)
session.add_device(dev)
session.start()
t = Thread(target=session.run)
t.start()


def grab_frame():
    x = np.arange(0, 200)
    y = np.arange(0, 320)
    X, Y = np.meshgrid(x, y)
    Z = X + Y
    Z = 255 * Z / Z.max()
    return pygame.surfarray.make_surface(Z)


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
session.stop()
