
flash:
	.venv/bin/esptool.py \
		--chip esp32c3 \
		--port /dev/tty.usbmodem1101 \
		--baud 460800 \
		write_flash \
		-z 0x0 /Users/drbh/Projects/esp-gossip/ESP32_GENERIC_C3-20240602-v1.23.0.bin

shell:
	picocom -b 9600 /dev/tty.usbmodem1101 

copy-src:
	.venv/bin/rshell --port /dev/cu.usbmodem1101 cp routine.py /pyboard/main.py && \
	echo "Copied files to pyboard"


clean-all-files:
	.venv/bin/rshell --port /dev/cu.usbmodem1101 rm /pyboard/main.py && \
	echo "Removed all files from pyboard"