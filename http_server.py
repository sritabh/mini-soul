import network
import uasyncio as asyncio
import ujson as json
from config_utils import get_config, save_config


def _noop(*args, **kwargs):
    pass


class HttpServer:
    def __init__(self, on_started=None, on_connected=None, on_saved=None):
        self._on_started   = on_started   or _noop
        self._on_connected = on_connected or _noop
        self._on_saved     = on_saved     or _noop
        self._server = None
        self._ap     = None

    # ── Hotspot ───────────────────────────────────────────────────────────────

    SSID     = "MiniSoul"
    PASSWORD = "myminisoul"

    def _start_hotspot(self):
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=self.SSID, password=self.PASSWORD, authmode=3)
        while not ap.active():
            pass
        print("Hotspot started:", ap.ifconfig())
        return ap

    # ── Request / response helpers ────────────────────────────────────────────

    @staticmethod
    def _parse_request(data):
        sep = b'\r\n\r\n'
        sep_idx = data.find(sep)
        if sep_idx == -1:
            headers_raw, body = data, b''
        else:
            headers_raw, body = data[:sep_idx], data[sep_idx + 4:]
        first_line = headers_raw.decode('utf-8').split('\r\n')[0].split(' ')
        method = first_line[0] if first_line else 'GET'
        path = first_line[1] if len(first_line) > 1 else '/'
        return method, path, body

    @staticmethod
    def _make_response(status, content_type, body):
        return (
            "HTTP/1.1 {}\r\n"
            "Content-Type: {}\r\n"
            "Content-Length: {}\r\n"
            "\r\n{}"
        ).format(status, content_type, len(body), body)

    @classmethod
    def _json_response(cls, obj, status="200 OK"):
        return cls._make_response(status, "application/json", json.dumps(obj))

    @classmethod
    def _html_response(cls, html):
        return cls._make_response("200 OK", "text/html", html)

    @classmethod
    def _not_found(cls, msg="Not found"):
        return cls._make_response("404 Not Found", "text/plain", msg)

    # ── Config helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _load_config():
        return get_config()

    @staticmethod
    def _save_config(config):
        save_config(config)

    # ── Route handlers ────────────────────────────────────────────────────────

    def _handle_get_root(self, _body):
        try:
            with open('setup_ui/index.html', 'r') as f:
                html = f.read()
            return self._html_response(html)
        except OSError:
            return self._not_found("File not found.")

    def _handle_get_config(self, _body):
        return self._json_response(self._load_config())

    @staticmethod
    def _parse_iso_datetime(s):
        date_part, time_part = s.split('T')
        yy, mo, dd = (int(x) for x in date_part.split('-'))
        parts = time_part.split(':')
        hh, mm = int(parts[0]), int(parts[1])
        ss = int(parts[2]) if len(parts) > 2 else 0
        return yy, mo, dd, hh, mm, ss

    def _handle_post_save(self, body):
        try:
            data = json.loads(body)
            print("Received data:", data)
            config = self._load_config()
            _IGNORE = {'updated_at'}
            original = {k: v for k, v in config.items() if k not in _IGNORE}

            if 'name' in data:
                config['name'] = data['name']

            if 'clock_face' in data:
                available = config.get('available_clock_faces', [])
                if data['clock_face'] in available:
                    config['clock_face'] = data['clock_face']

            time_str = data.get('time', '')
            if time_str:
                config['updated_at'] = time_str
                from rtc_utils import init_rtc
                init_rtc(force_set=True, new_time=self._parse_iso_datetime(time_str))

            updated = {k: v for k, v in config.items() if k not in _IGNORE}
            if updated != original:
                self._save_config(config)
                print("Config saved.")
            else:
                print("Config unchanged, skipping write.")

            self._on_saved(config)
            return self._json_response({"status": "ok"})
        except Exception as e:
            print("Error handling /save:", e)
            return self._json_response({"status": "error", "msg": str(e)}, "500 Internal Server Error")

    # ── Router ────────────────────────────────────────────────────────────────

    def _dispatch(self, method, path, body):
        routes = {
            ('GET',  '/'):       self._handle_get_root,
            ('GET',  '/config'): self._handle_get_config,
            ('POST', '/save'):   self._handle_post_save,
        }
        handler = routes.get((method, path))
        if handler:
            return handler(body)
        return self._not_found()

    # ── Async connection handler ──────────────────────────────────────────────

    async def _handle_connection(self, reader, writer):
        addr = writer.get_extra_info('peername')
        print("Connection from:", addr)
        try:
            request = await reader.read(4096)
            method, path, body = self._parse_request(request)
            print("Request:", method, path)
            response = self._dispatch(method, path, body)
            writer.write(response.encode('utf-8'))
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def _watch_stations(self):
        """Fire on_connected when the first device joins the AP network."""
        connected = False
        while True:
            try:
                stations = self._ap.status('stations') if self._ap else []
            except Exception:
                stations = []
            if stations and not connected:
                connected = True
                self._on_connected(stations[0])
            elif not stations and connected:
                connected = False   # device left — reset so re-joining fires again
            await asyncio.sleep_ms(500)

    # ── Public entry point ────────────────────────────────────────────────────

    async def run_server(self):
        self._ap = self._start_hotspot()
        ip = self._ap.ifconfig()[0]
        self._on_started(ip, self.SSID, self.PASSWORD)
        self._server = await asyncio.start_server(self._handle_connection, "0.0.0.0", 80)
        print("Listening on port 80...")
        from mdns import run_mdns
        asyncio.create_task(run_mdns('minisoul', ip))
        asyncio.create_task(self._watch_stations())
        # keep alive loop
        while True:
            await asyncio.sleep(3600)

    def stop(self):
        """Shut down the TCP server and tear down the Wi-Fi hotspot."""
        if self._server is not None:
            self._server.close()
            self._server = None
        if self._ap is not None:
            self._ap.active(False)
            self._ap = None
        print("HttpServer stopped.")


# ── Standalone execution ──────────────────────────────────────────────────────

if __name__ == '__main__':
    from qr_display import show_qr

    def on_started(ip, ssid, password):
        from machine import Pin
        from rtc_utils import i2c
        from ssd1306 import SSD1306_I2C
        Pin(7, Pin.OUT, value=1)   # power OLED VCC rail
        oled = SSD1306_I2C(128, 64, i2c)
        show_qr(oled, "http://{}/".format(ip), scale=2)
        print("Showing QR for", ip)

    def on_connected(addr):
        print("Client connected:", addr)

    def on_saved(config):
        print("Settings saved:", config.get('name'))

    server = HttpServer(on_started=on_started, on_connected=on_connected, on_saved=on_saved)
    try:
        asyncio.run(server.run_server())
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.stop()
