# petvideo
A simple video acquisition program to display the Commodore PET video output with a logic analyzer.

You will need a $10 fx2la compatible USB LA device.

Connect like this:

```
LA       PET Connector J7
CH0      Pin 1     [Video]
CH1      Pin 3     [VER Drive]
CH2      Pin 5     [HOR Drive] 
GND      Pin 7     [Gnd]
```

Usage:
```
./petvideo
```


To run it on a prerecorded test capture:
```
./petvideo --test
```

The test sample has been captured like this:

```
sigrok-cli -d fx2lafw --continuous -O binary --config samplerate=12m -o test/raw-vid-ver-hor-x-x-x-x-x.raw
```
