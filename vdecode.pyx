# cython: language_level=3
from libc.stdint cimport uint8_t, uint64_t
from cpython cimport array
from threading import Lock
cimport numpy as np
import pygame

DEF VIDEO_MASK     = 0b00000001
DEF VER_DRIVE_MASK = 0b00000010
DEF HOR_DRIVE_MASK = 0b00000100

DEF BUFFER_WIDTH = 3200
DEF BUFFER_HEIGHT = 500

cdef enum VState:
    PRE_VBLANK = 0
    VBLANK = 1
    HBLANK = 2
    LEFT_LINE = 3
    RIGHT_LINE = 4

render_lock = Lock()
decoded_surface = pygame.Surface((BUFFER_WIDTH, BUFFER_HEIGHT), depth=8)
rendered_surface = pygame.Surface((BUFFER_WIDTH, BUFFER_HEIGHT), depth=8)

def flip_surfaces():
    global decoded_surface, rendered_surface
    with render_lock:
        decoded_surface, rendered_surface = rendered_surface, rendered_surface


cdef int vstate = VState.PRE_VBLANK
cdef int current_pixel_index = 0
cdef int current_line_index = 0

cdef array.array line_buffer = array.array('B', [0]*BUFFER_WIDTH)

def decode(np.ndarray[np.uint8_t, ndim=1] raw_data, decoder_clock):
    global vstate, current_pixel_index, current_line_index
    cdef int i = 0
    cdef int buffer_len = raw_data.shape[0]
    cdef uint8_t b
    while i < buffer_len:
        if vstate == VState.PRE_VBLANK:
            with nogil:
                while i < buffer_len:
                    b = raw_data[i]
                    i += 1
                    if b & VER_DRIVE_MASK == 0:
                        vstate = VState.VBLANK
                        break

        if vstate == VState.VBLANK:
            with nogil:
                while i < buffer_len:
                    b = raw_data[i]
                    i += 1
                    if b & VER_DRIVE_MASK != 0:
                        current_line_index = 0
                        current_max_pixel_index = 0
                        vstate = VState.HBLANK
                        break
            decoder_clock.tick()
            flip_surfaces()

        if vstate == VState.HBLANK:
            while i < buffer_len:
                b = raw_data[i]
                i += 1
                if b & VER_DRIVE_MASK == 0:
                    vstate = VState.PRE_VBLANK
                    break
                if b & HOR_DRIVE_MASK != 0:
                    vstate = VState.LEFT_LINE
                    current_pixel_index = 0
                    break
        if vstate == VState.LEFT_LINE:
            while i < buffer_len:
                b = raw_data[i]
                i += 1
                line_buffer[current_pixel_index] = (1 - (b & VIDEO_MASK)) * 30
                current_pixel_index += 1
                if b & HOR_DRIVE_MASK == 0:
                    vstate = VState.RIGHT_LINE
                    break

        if vstate == VState.RIGHT_LINE:
            while i < buffer_len:
                b = raw_data[i]
                i += 1
                if b & HOR_DRIVE_MASK != 0:
                    vstate = VState.HBLANK
                    current_buffer = decoded_surface.get_buffer()
                    current_buffer.write(bytes(line_buffer), current_line_index*BUFFER_WIDTH)
                    del current_buffer
                    current_line_index += 1
                    break
                line_buffer[current_pixel_index] = (1 - (b & VIDEO_MASK)) * 30
                current_pixel_index += 1
