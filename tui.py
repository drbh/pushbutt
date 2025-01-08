from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Button, Static, Log, Input
from textual.reactive import reactive
from rich import box
from rich.panel import Panel
import serial
import json
import time
from typing import Optional


class ESP32Client:
    def __init__(self, port, baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = serial.Serial(port, baudrate, timeout=timeout)

        # Reset sequence
        self.serial.setDTR(False)
        self.serial.setRTS(False)
        time.sleep(0.1)
        self.serial.setDTR(True)
        self.serial.setRTS(True)

        # Clear buffer
        while self.serial.read(100) != b"":
            pass

    def send_command(self, cmd):
        try:
            msg = json.dumps(cmd).encode("utf-8") + b"\r\n"
            self.serial.write(msg)

            try_count = 0
            while True:
                if try_count > 10:
                    return None
                try_count += 1
                response = self.serial.readline().decode("utf-8").strip()
                if response.startswith('{"val'):
                    break
                time.sleep(0.001)

            return json.loads(response) if response else None
        except Exception as e:
            return {"error": str(e)}

    def close(self):
        self.serial.close()


class StatusWidget(Static):
    """Shows device connection status"""

    status = reactive("Disconnected")
    wifi_status = reactive("Unknown")
    ip_address = reactive("None")

    def compose(self) -> ComposeResult:
        yield Static(id="status_content")

    def watch_status(self) -> None:
        self.update_status()

    def watch_wifi_status(self) -> None:
        self.update_status()

    def watch_ip_address(self) -> None:
        self.update_status()

    def update_status(self) -> None:
        content = (
            f"Device: {self.status}\nWiFi: {self.wifi_status}\nIP: {self.ip_address}"
        )
        self.query_one("#status_content").update(
            Panel(content, title="Status", box=box.ROUNDED)
        )


class ESP32TUI(App):
    CSS = """
    StatusWidget {
        height: auto;
        margin: 1;
    }

    #controls {
        height: auto;
        margin: 1;
    }

    #command-log {
        height: 1fr;
        margin: 1;
        border: solid green;
    }

    Input {
        margin: 1;
    }

    Button {
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "connect", "Connect"),
        ("d", "disconnect", "Disconnect"),
        ("l", "toggle_led", "Toggle LED"),
        ("p", "pulse_led", "Pulse LED"),
        ("w", "wifi_setup", "WiFi Setup"),
        ("i", "get_ip", "Get IP"),
        ("h", "dump_http", "Dump HTTP"),
    ]

    def __init__(self):
        super().__init__()
        self.client: Optional[ESP32Client] = None
        self._status_widget: Optional[StatusWidget] = None
        self._command_log: Optional[Log] = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield StatusWidget()
        yield Container(
            Horizontal(
                Button("Connect", id="connect", variant="success"),
                Button("WiFi Setup", id="wifi_setup", variant="primary"),
                Button("Toggle LED", id="toggle_led", variant="warning"),
                Button("Pulse LED", id="pulse_led", variant="warning"),
                Button("Get IP", id="get_ip", variant="primary"),
                Button("Disconnect", id="disconnect", variant="warning"),
                Button("Dump HTTP", id="dump_http", variant="primary"),
                Button("HTTP Request", id="http_setup", variant="primary"),
                id="controls",
            )
        )
        yield Input(placeholder="WiFi SSID", id="ssid")
        yield Input(placeholder="WiFi Password", password=True, id="password")
        yield Input(placeholder="URL", id="url")
        yield Input(placeholder="Method", id="method")
        yield Input(placeholder="Data Template", id="data_template")
        yield Log(id="command-log", highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted to the screen."""
        self._status_widget = self.query_one(StatusWidget)
        self._command_log = self.query_one("#command-log")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        self.log_message(f"Button pressed: {button_id}")
        if button_id == "connect":
            self.action_connect()
        elif button_id == "wifi_setup":
            self.setup_wifi()
        elif button_id == "toggle_led":
            self.action_toggle_led()
        elif button_id == "pulse_led":
            self.action_pulse_led()
        elif button_id == "disconnect":
            self.action_disconnect()
        elif button_id == "get_ip":
            self.action_get_ip()
        elif button_id == "dump_http":
            self.action_dump_http()
        elif button_id == "http_setup":
            self.action_setup_http()

    def log_message(self, message: str) -> None:
        """Write a message to the log."""
        if self._command_log:
            self._command_log.write_line(
                f"[grey]{time.strftime('%H:%M:%S')}[/] {message}"
            )

    def action_setup_http(self) -> None:
        """Setup HTTP request."""
        if self.client:
            url = self.query_one("#url").value
            method = self.query_one("#method").value
            data_template = self.query_one("#data_template").value

            if not url or not method:
                self.log_message("[yellow]Please enter URL and method[/]")
                return

            response = self.client.send_command(
                {
                    "cmd": "set_url",
                    "url": url,
                }
            )
            self.log_message(f"URL setup response: {response}")

            response = self.client.send_command(
                {
                    "cmd": "set_method",
                    "method": method,
                }
            )
            self.log_message(f"Method setup response: {response}")

            response = self.client.send_command(
                {
                    "cmd": "set_data_template",
                    "data_template": data_template,
                }
            )
            self.log_message(f"Data template setup response: {response}")

            response = self.client.send_command({"cmd": "send_request"})
            self.log_message(f"HTTP request response: {response}")
        else:
            self.log_message("[red]Connect to device first[/]")

    def action_dump_http(self) -> None:
        """Dump HTTP settings."""
        if self.client:
            response = self.client.send_command({"cmd": "dump_http"})
            self.log_message(f"HTTP settings: {response}")
        else:
            self.log_message("[red]Connect to device first[/]")

    def action_get_ip(self) -> None:
        """Get IP address."""
        if self.client:
            response = self.client.send_command({"cmd": "get_ip"})
            self.log_message(f"IP address: {response.get('val', 'Unknown')}")
        else:
            self.log_message("[red]Connect to device first[/]")

    def action_connect(self) -> None:
        """Connect to the ESP32."""
        try:
            if not self.client:
                self.client = ESP32Client("/dev/tty.usbmodem1101")
                self._status_widget.status = "Connected"
                self.log_message("[green]Connected to ESP32[/]")
                self.check_wifi_status()
        except Exception as e:
            self.log_message(f"[red]Connection error: {e}[/]")

    def action_disconnect(self) -> None:
        """Disconnect from the ESP32."""
        if self.client:
            self.client.close()
            self.client = None
            self._status_widget.status = "Disconnected"
            self._status_widget.wifi_status = "Unknown"
            self._status_widget.ip_address = "None"
            self.log_message("[yellow]Disconnected from ESP32[/]")

    def action_toggle_led(self) -> None:
        """Toggle the LED."""
        if self.client:
            response = self.client.send_command({"cmd": "led"})
            self.log_message(f"LED toggle response: {response}")

    def action_pulse_led(self) -> None:
        """Pulse the LED."""
        if self.client:
            response = self.client.send_command({"cmd": "pulse"})
            self.log_message(f"LED pulse response: {response}")

    def setup_wifi(self) -> None:
        """Setup WiFi connection."""
        if not self.client:
            self.log_message("[red]Connect to device first[/]")
            return

        ssid = self.query_one("#ssid").value
        password = self.query_one("#password").value

        if not ssid or not password:
            self.log_message("[yellow]Please enter WiFi credentials[/]")
            return

        response = self.client.send_command(
            {"cmd": "connect_wifi", "ssid": ssid, "password": password}
        )
        self.log_message(f"WiFi setup response: {response}")
        self.check_wifi_status()

    def check_wifi_status(self) -> None:
        """Check WiFi connection status."""
        if self.client:
            response = self.client.send_command({"cmd": "check_wifi"})
            if response and response.get("val"):
                self._status_widget.wifi_status = "Connected"
                ip_response = self.client.send_command({"cmd": "get_ip"})
                self._status_widget.ip_address = (
                    ip_response.get("val", "Unknown") if ip_response else "Unknown"
                )
            else:
                self._status_widget.wifi_status = "Disconnected"
                self._status_widget.ip_address = "None"


if __name__ == "__main__":
    app = ESP32TUI()
    app.run()
