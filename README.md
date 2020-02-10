# petvideo
A simple program to emulate the Commodore PET monitor on your PC.
You can hook it up and have the output of the PET displayed in a window like this:

![](assets/petvideo.gif)

## Why?

PETs are awesome but the fact that they are a "onesie" computer, it is hard to test independently their 
motherboard from their screens. This allows you to just hook up a PET motherboard and fix it without to have a buzzing 10kv device that tries to kill you nearby.

The alternative is to build a composite adapter but it is a one purpose device while a LA can also be used for more advance vintage computer troubleshooting!

## What do I need?

All you need a ~$10 fx2lafw compatible USB LA device, see a list of devices [on the sigrok website](https://sigrok.org/wiki/Fx2lafw).

I used [this one from Amazon](https://www.amazon.com/gp/product/B077LSG5P2/ref=ppx_yo_dt_b_asin_title_o02_s00?ie=UTF8&psc=1) (I have no affiliation whatsoever with it).

And connect it like this:

```
LA       PET Connector J7
CH0      Pin 1     [Video]
CH1      Pin 3     [VER Drive]
CH2      Pin 5     [HOR Drive] 
GND      Pin 7     [Gnd]
```

It should look like this...
![](assets/connections.jpg)

With here, brown for video, red for vertical drive, yellow for horizontal drive and black for GND.

## Software dependencies

You will need to install:
- [Python 3.8+](https://www.python.org/)
- [libsigrok](https://sigrok.org/wiki/Libsigrok)
- [cython](https://pypi.org/project/Cython/) 
- [pygame](https://pypi.org/project/pygame/)
- [numpy](https://pypi.org/project/numpy/)
- [click](https://pypi.org/project/click/)

If you are on Arch Linux you can install all those dependencies with this command, you will need the community repos to be enabled:
```bash
sudo pacman -S python libsigrok cython python-pygame python-numpy python-click
```

## Usage

You can test the rendering part of the software independently first:
```bash
./petvideo --test
```

To run it for real on the first LA found on your system:
```bash
./petvideo
```

You can ask for a fancy CRT-style rendering with:
```bash
./petvideo --phosphore
```

To see if your system is keeping up you can ask for rendering and decoding statistics:
```bash
./petvideo --fps
```


## Creating a capture for the tool
The test sample has been captured like this:
```bash
sigrok-cli -d fx2lafw --continuous -O binary --config samplerate=12m -o test/raw-vid-ver-hor-x-x-x-x-x.raw
```
