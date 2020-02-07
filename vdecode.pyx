# cython: language_level=3
cimport numpy as np
from libc.stdint cimport uint8_t, uint64_t
from cpython cimport array
cdef enum VState:
    PRE_VBLANK = 0
    VBLANK = 1
    HBLANK = 2
    LEFT_LINE = 3
    RIGHT_LINE = 4


DEF VIDEO_MASK     = 0b00000001
DEF VER_DRIVE_MASK = 0b00000010
DEF HOR_DRIVE_MASK = 0b00000100
cdef int vstate = VState.PRE_VBLANK

cdef int current_pixel_index = 0
cdef int current_line_index = 0

cdef array.array line_buffer = array.array('B', [0]*3200)

def decode(np.ndarray[np.uint8_t, ndim=1] raw_data, decoded_surface, decoder_clock):
    global vstate, current_pixel_index, current_line_index
    cdef int i = 0
    cdef int decoded_frames = 0
    cdef int buffer_len = raw_data.shape[0]
    current_buffer = decoded_surface.surface.get_buffer()
    cdef uint8_t b
    while i < buffer_len:
        if vstate == VState.PRE_VBLANK:
            with nogil:
                while i < buffer_len:
                    b = raw_data[i]
                    if b & VER_DRIVE_MASK == 0:
                        vstate = VState.VBLANK
                        break
                    i += 1

        if vstate == VState.VBLANK:
            with nogil:
                while i < buffer_len:
                    b = raw_data[i]
                    if b & VER_DRIVE_MASK != 0:
                        decoded_frames +=1
                        current_line_index = 0
                        current_max_pixel_index = 0
                        vstate = VState.HBLANK
                        break
                    i += 1
            decoder_clock.tick()

        if vstate == VState.HBLANK:
            while i < buffer_len:
                b = raw_data[i]
                if b & VER_DRIVE_MASK == 0:
                    vstate = VState.PRE_VBLANK
                    break
                if b & HOR_DRIVE_MASK != 0:
                    vstate = VState.LEFT_LINE
                    current_pixel_index = 0
                    break
                i += 1
        if vstate == VState.LEFT_LINE:
            while i < buffer_len:
                b = raw_data[i]
                line_buffer[current_pixel_index] = (1 - (b & VIDEO_MASK)) * 30
                current_pixel_index += 1
                if b & HOR_DRIVE_MASK == 0:
                    vstate = VState.RIGHT_LINE
                    break
                i += 1

        if vstate == VState.RIGHT_LINE:
            while i < buffer_len:
                b = raw_data[i]
                if b & HOR_DRIVE_MASK != 0:
                    vstate = VState.HBLANK
                    current_buffer = decoded_surface.surface.get_buffer()
                    current_buffer.write(bytes(line_buffer), current_line_index*3200)
                    del current_buffer
                    current_line_index += 1
                    break
                line_buffer[current_pixel_index] = (1 - (b & VIDEO_MASK)) * 30
                current_pixel_index += 1
                if current_pixel_index>decoded_surface.max_width:
                    decoded_surface.max_width = current_pixel_index
                i += 1
    return decoded_frames
