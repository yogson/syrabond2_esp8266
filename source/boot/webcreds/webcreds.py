__version__ = "0.1"

from time import sleep
import sys
import usocket as socket
import ujson as json
import machine
import network
import uasyncio


class Http:

    def __init__(self, ip='0.0.0.0', port=80):
        print('Starting web server')
        self.server = socket.socket()
        self.server.setblocking(0)
        self.server.bind((ip, port))
        self.server.listen(3)
        self.sys_version = "Micropython/" + sys.version.split()[0]
        self.server_version = "HTTP/" + __version__
        self.default_request_version = "HTTP/0.9"
        self.protocol_version = "HTTP/1.0"
        self.raw_requestline = b''
        self.mainloop_disactive = False

    def get_request(self):
        try:
            self.s, self.addr = self.server.accept()
            self.s.settimeout(2)
            print('Request from ' + str(self.addr[0]))
            while True:
                try:
                    data = self.s.recv(120)
                    self.raw_requestline += data
                except OSError:
                    break
        except:
            sleep(1)

    def parse_request(self):
        if len(self.raw_requestline) > 2048:
            self.requestline = ''
            self.request_version = ''
            self.command = ''
            self.send_response(414, message='Request too long')
            return
        if not self.raw_requestline:
            self.close_connection = 1
            return
        self.command = None  # set in case of error on the first line
        self.request_version = version = self.default_request_version
        self.close_connection = 1
        requestline = self.raw_requestline.decode()
        requestline = requestline.split('\n')[0]
        self.requestline = requestline
        words = requestline.split()
        print(words)
        if len(words) == 3:
            command, path, version = words
            if version[:5] != 'HTTP/':
                self.send_response(400, "Bad request version (%r)" % version)
                return False
            try:
                base_version_number = version.split('/', 1)[1]
                version_number = base_version_number.split(".")
                if len(version_number) != 2:
                    self.send_response(400, "Bad request version (%r)" % version)
                version_number = int(version_number[0]), int(version_number[1])
            except:
                self.send_response(400, "Bad request version (%r)" % version)
                return False
            if version_number >= (1, 1) and self.protocol_version >= "HTTP/1.1":
                self.close_connection = 0
            if version_number >= (2, 0):
                self.send_response(505,
                                "Invalid HTTP Version (%s)" % base_version_number)
                return False
        elif len(words) == 2:
            command, path = words
            self.close_connection = 1
            if command != 'GET':
                self.send_response(400,
                                "Bad HTTP/0.9 request type (%r)" % command)
                return False
        elif not words:
            return False
        else:
            self.send_response(400, "Bad request syntax (%r)" % requestline)
            return False
        self.command, self.path, self.request_version = command, path, version
        return True

    def handle_request(self):
        try:
            if not self.parse_request():
                # An error code has been sent, just exit
                return
            mname = 'do_' + self.command
            print(mname)
            if not hasattr(self, mname):
                self.send_response(501, "Unsupported method (%r)" % self.command)
                return
            method = getattr(self, mname)
            method()
            self.s.flush()  # actually send the response if not already done.
        except:
            # a read or a write timed out.  Discard this connection
            self.close_connection = 1
            return

    def send_response(self, code, message=None):
        """Send the response header.
        """
        if self.request_version != 'HTTP/0.9':
            data = "%s %d %s\r\n" % (self.protocol_version, code, message)
            self.s.send(data.encode())
            print(self.protocol_version, code, message)
        self.send_header('Server', self.version_string())

    def send_header(self, keyword, value):
        """Send a MIME header."""
        if self.request_version != 'HTTP/0.9':
            data = "%s: %s\r\n" % (keyword, value)
            self.s.send(data.encode())

    def end_headers(self):
        """Send the blank line ending the MIME headers."""
        if self.request_version != 'HTTP/0.9':
            self.s.send(b"\r\n")

    def version_string(self):
        """Return the server software version string."""
        return self.server_version + ' ' + self.sys_version

    def show_page(self, page):
        print('show page '+page)
        self.send_response(200, 'OK')
        self.send_header('content-type', 'text/html')
        self.end_headers()
        f = open(page, 'r')
        data = f.read()
        f.close()
        self.s.send(data.encode())

    def do_GET(self):
        if self.path == '/':
            self.show_page('index.html')
        else:
            self.send_response(404, 'Not found')
        if self.close_connection:
            self.s.close()
        self.raw_requestline = b''

    def do_POST(self):
        self.mainloop_disactive = True
        lines = self.raw_requestline.decode().split('\n')
        data = lines[len(lines)-1]
        try:
            ssid, pwd = data.split('&')
            ssid = percent_decode(ssid[ssid.find('=')+1:])
            pwd = percent_decode(pwd[pwd.find('=')+1:])
            print(ssid, pwd)
            res = try_to_connect(ssid, pwd)
            if res:
                save_creds(ssid, pwd)
                self.show_page('ok.html')
                data = '<p>Устройство успешно подключено к %s</p>' \
                       '<p>Параметры подключения сохранены, устройство перезагружено.</p></body></html>' % ssid
                self.s.send(data.encode())
                sleep(1)
                self.s.close()
                sleep(1)
                machine.reset()
            else:
                self.show_page('noconn.html')
        except ValueError:
            self.show_page('error.html')
        if self.close_connection:
            self.s.close()
        self.raw_requestline = b''


def percent_decode(text):
    dictionary = {'%21':'!', '%23':'#', '%24':'$', '%26':'&', '%27':"'", '%28':'(',
                  '%29':')', '%2A':'*', '%2B':'+', '%2C':',', '%2F':'/', '%3A':':',
                  '%3B':';', '%3D':'=', '%3F':'?', '%40':'@', '%5B':'[', '%5D':']'}
    for key in dictionary:
        text = text.replace(key, dictionary[key])
    return text


def save_creds(ssid, pwd):
    dict = {}
    dict['ssid'] = ssid
    dict['pass'] = pwd
    encoded = json.dumps(dict)
    try:
        f = open('network.json', 'w')
        f.write('')
        f.close()
        f = open('network.json', 'w')
        f.write(encoded)
        f.close()
    except:
        print('Could not write config file')


def try_to_connect(ssid, pwd):
    led = machine.Pin(13, machine.Pin.OUT)
    print('Trying to connect to '+ssid + ' with '+pwd)
    led.value(0)
    sta_if = network.WLAN(network.STA_IF)
    if sta_if.isconnected():
        sta_if.disconnect()
        sleep(2)
    sta_if.active(True)
    sta_if.connect(ssid, pwd)
    t = 0
    while not sta_if.isconnected():
            if t < 15:
                led.value(0)
                sleep(0.5)
                led.value(1)
                sleep(0.5)
                t += 1
                pass
            else:
                print('Wrong credentials')
                led.value(0)
                return (False)
    print('Connected: ', sta_if.ifconfig())
    led.value(1)
    return True


async def run_webcreds_server():
    try:
        import webcreds
    except ImportError:
        return
    sta = network.WLAN(network.STA_IF)
    serv = Http()
    while not sta.isconnected():
        serv.get_request()
        if serv.raw_requestline:
            serv.parse_request()
            serv.handle_request()
        await uasyncio.sleep(0.1)
