from machine import Pin, PWM
import time
import json
import math
import network
import urequests


class Routine:
    def __init__(self):
        self.running = True
        time.sleep_ms(100)


class Network:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)

    def connect_wifi(self, ssid, password):
        try:
            if not self.wlan.isconnected():
                self.wlan.connect(ssid, password)
                while not self.wlan.isconnected():
                    pass
            return True
        except Exception as e:
            print("Failed to connect to WiFi:", e)
            return False

    def disconnect_wifi(self):
        self.wlan.disconnect()

    def is_connected(self):
        return self.wlan.isconnected()

    def get_ip(self):
        return self.wlan.ifconfig()[0]


class Button:
    def __init__(self, pin):
        # set pins low so button press can be detected
        low_pins = [4, 8, 10]
        for pin in low_pins:
            Pin(pin, Pin.OUT, value=0)

        self.pin = Pin(pin, Pin.IN)
        self.last_time = 0
        self.pin.irq(trigger=Pin.IRQ_RISING, handler=self.button_pressed)
        self.on_press = None

    def set_on_press(self, on_press):
        self.on_press = on_press

    def button_pressed(self, pin):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_time) > 300:
            self.last_time = current_time
            print("Button released!")
            if self.on_press:
                self.on_press()
            return True
        return False


class HTTPClient:
    def __init__(self):
        self.url = None
        self.method = None
        self.data_template = None
        self.get_data = None

    def set_url(self, url):
        self.url = url

    def set_method(self, method):
        self.method = method

    def set_data_template(self, data_template):
        if "$$" not in data_template:
            return {"error": "Data template must contain $$"}
        self.data_template = data_template

    def set_get_data(self, get_data):
        self.get_data = get_data

    def render_data(self):
        if self.data_template is None or self.get_data is None:
            return {"error": "Data template or get data function not set"}
        current = self.get_data()
        rendered = self.data_template.replace("$$", current)
        return rendered

    def send_request(self):
        if self.url is None or self.method is None:
            return {"error": "URL or method not set"}
        try:
            data = self.render_data()
            headers = {"Content-Type": "application/json"}
            response = urequests.request(
                self.method, self.url, data=data, headers=headers
            )
            return json.loads(response.text)
        except Exception as e:
            return {"error": str(e)}


class MyRoutine(Routine):
    def __init__(self):
        super().__init__()
        self.led = Pin(3, Pin.OUT)
        self.pwm_led = PWM(self.led)
        self.pwm_led.freq(1000)
        self.pwm_led.duty(0)
        self.wifi = Network()
        self.button = Button(10)
        self.button.set_on_press(self.on_button_press)
        self.http_client = HTTPClient()
        print("Routine initialized")

    def on_button_press(self):
        self.pulse()
        res = self.send_request()
        print(res)

    def pulse(self):
        try:
            CYCLE_MS = 3000
            STEPS = 100

            for i in range(STEPS):
                x = i / STEPS
                brightness = math.sin(x * math.pi) ** 3
                duty = int(brightness * brightness * 1023)
                self.pwm_led.duty(duty)
                time.sleep_ms(CYCLE_MS // STEPS)

            # Fade out
            for i in range(STEPS - 1, -1, -1):
                x = i / STEPS
                brightness = math.sin(x * math.pi) ** 3
                duty = int(brightness * brightness * 1023)
                self.pwm_led.duty(duty)
                time.sleep_ms(CYCLE_MS // STEPS)

            self.pwm_led.duty(0)
            return {"val": "ok"}
        except Exception as e:
            self.pwm_led.duty(0)
            return {"error": str(e)}

    def handle_cmd(self, cmd):
        if cmd.get("cmd") == "led":
            self.led.value(not self.led.value())
            return {"val": "LED toggled"}
        elif cmd.get("cmd") == "check_wifi":
            return {"val": self.wifi.is_connected()}
        elif cmd.get("cmd") == "connect_wifi":
            did_connect = self.wifi.connect_wifi(cmd.get("ssid"), cmd.get("password"))
            return {
                "val": "WiFi connected" if did_connect else "Failed to connect to WiFi"
            }
        elif cmd.get("cmd") == "disconnect_wifi":
            self.wifi.disconnect_wifi()
            return {"val": "WiFi disconnected"}
        elif cmd.get("cmd") == "get_ip":
            return {"val": self.wifi.get_ip()}
        elif cmd.get("cmd") == "pulse":
            return self.pulse()
        elif cmd.get("cmd") == "set_url":
            self.http_client.set_url(cmd.get("url"))
            return {"val": "URL set"}
        elif cmd.get("cmd") == "set_method":
            self.http_client.set_method(cmd.get("method"))
            return {"val": "Method set"}
        elif cmd.get("cmd") == "set_data_template":
            self.http_client.set_data_template(cmd.get("data_template"))
            return {"val": "Data template set"}
        elif cmd.get("cmd") == "send_request":
            return self.http_client.send_request()
        elif cmd.get("cmd") == "dump_http":
            return {
                "val": {
                    "url": self.http_client.url,
                    "method": self.http_client.method,
                    "data_template": self.http_client.data_template,
                }
            }
        return {"val": "Invalid command"}

    def run(self):
        while 1:
            try:
                line = input()
                print(line)
                resp = self.handle_cmd(json.loads(line))
                print(json.dumps(resp))
            except Exception as _e:
                pass

            if self.running:
                print(json.dumps({"status": "heartbeat"}))

            time.sleep_ms(10)


MyRoutine().run()
