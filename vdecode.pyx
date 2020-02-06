# cython: language_level=3
import numpy as np
cimport numpy as np
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

# here we assume a x10 oversampling
cdef array.array current_line_buffer = array.array('B', [0,] * 3200)
#cdef np.ndarray[np.uint8_t] current_line_buffer = np.zeros((320 * 10,), dtype=int)
cdef int current_pixel_index = 0
cdef int current_line_index = 0

def decode(np.ndarray[np.uint8_t] raw_data, np.ndarray[np.uint8_t, ndim=2] framebuffer, int gindex):
    global vstate, current_pixel_index, current_line_index
    cdef int left = 0
    cdef int i = 0

    cdef int max = raw_data.shape[0]
    cdef int width = 0

    while i < max:
        if vstate == VState.PRE_VBLANK:
            while i < max:
                b = raw_data[i]
                if b & VER_DRIVE_MASK == 0:
                    vstate = VState.VBLANK
                    break
                left += 1
                i += 1
        if vstate == VState.VBLANK:
            while i < max:
                b = raw_data[i]
                if b & VER_DRIVE_MASK != 0:
                    print(f'Number of lines {current_line_index}')
                    print(f'Start of scan {left+gindex}')
                    current_line_index = 0
                    vstate = VState.HBLANK
                    break
                left += 1
                i += 1
        if vstate == VState.HBLANK:
            while i < max:
                b = raw_data[i]
                if b & VER_DRIVE_MASK == 0:
                    print(f'End of scan {left+gindex}')
                    vstate = VState.PRE_VBLANK
                    break
                if b & HOR_DRIVE_MASK != 0:
                    #print(f'Start of line {left+gindex}')
                    vstate = VState.LEFT_LINE
                    current_pixel_index = 0
                    current_line_index += 1
                    break
                left += 1
                i += 1

        if vstate == VState.LEFT_LINE:
            while i < max:
                b = raw_data[i]
                current_line_buffer[current_pixel_index] = b
                current_pixel_index += 1
                if b & HOR_DRIVE_MASK == 0:
                    vstate = VState.RIGHT_LINE
                    break
                left += 1
                i += 1

        if vstate == VState.RIGHT_LINE:
            while i < max:
                b = raw_data[i]
                if b & HOR_DRIVE_MASK != 0:
                    vstate = VState.HBLANK
                    # print(f'Line lengh {current_pixel_index}')
                    width = framebuffer.shape[0]
                    for p in range(width):
                        framebuffer[p][current_line_index]=0 if current_line_buffer[(p * current_pixel_index)//width] & VIDEO_MASK else 30
                    break
                current_line_buffer[current_pixel_index] = b
                current_pixel_index += 1
                left += 1
                i += 1

    # decoded_signal = np.packbits(np.bitwise_and(raw_data, VIDEO_MASK))
    # print(decoded_signal)
    # incoming_length =
    # right = len(decoded_signal) + current_index if current_index +
    # raster[current_index:len(decoded_signal)] = decoded_signal
    # print(packet.payload.data)


print('Hello world')
