# cython: language_level=3
import numpy as np
cimport numpy as np

cdef enum VState:
    PRE_VBLANK = 0
    VBLANK = 1
    HBLANK = 2
    LINE = 3


DEF VIDEO_MASK     = 0b00000001
DEF VER_DRIVE_MASK = 0b00000010
DEF HOR_DRIVE_MASK = 0b00000100
cdef int vstate = VState.PRE_VBLANK


def decode(np.ndarray[np.uint8_t] raw_data, np.ndarray[np.uint8_t, ndim=2] framebuffer, int gindex):
    global vstate
    cdef int left = 0
    cdef int i = 0

    cdef int max = raw_data.shape[0]
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
                    #print(f'Start of scan {left+gindex}')
                    vstate = VState.PRE_VBLANK
                    break
                left += 1
                i += 1
    decoded_signal = np.packbits(np.bitwise_and(raw_data, VIDEO_MASK))
    # print(decoded_signal)
    # incoming_length =
    # right = len(decoded_signal) + current_index if current_index +
    # raster[current_index:len(decoded_signal)] = decoded_signal
    # print(packet.payload.data)


print('Hello world')
