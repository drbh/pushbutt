# pushbutt

> [!WARNING]
> This project is still in active development and may surprises you with unexpected behavior

a simple programmable button for integration with automation systems. 

## Features

device case:

- [ ] 3D printable case
- [ ] fully reproducible design via code

device software:

- [X] send a http request on button press
- [X] handle actions from client or button press

client software:

- [X] setup wifi via a simple terminal client
- [X] setup the http request via a simple terminal client


### Hardware

| Part                   | Description      |
| ---------------------- | ---------------- |
| ESP32 C3               | microcontroller  |
| 5mm LED                | status indicator |
| 12x12mm Tactile Button | pushbutton       |

### Pinout

| ESP32 Pin | Connected To  | Note                              | Purpose          |
| --------- | ------------- | --------------------------------- | ---------------- |
| GND       | LED -         |                                   | status indicator |
| 3         | LED +         | using PWM to add breathing effect | status indicator |
| 10        | Button In     | pull-up resistor to GND           | pushbutton       |
| 4, 8      | Button ground | grounded for reference            | pushbutton       |

### Software

First make sure you have micropython installed on the ESP32 board

```bash
make flash
```

copy the source files to the board

```bash
make copy-src
```

### Terminal Client

now run the terminal client

```bash
uv run tui.py
```
