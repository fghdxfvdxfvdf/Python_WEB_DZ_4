# http://127.0.0.1:3000
# http://localhost:3000
from datetime import datetime as dt, timedelta
import json
import logging
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
from threading import Thread
from urllib import parse 
import mimetypes


BASE_DIR = pathlib.Path()
STORAGE_DIR = BASE_DIR.joinpath('storage')
FILE_STORAGE = STORAGE_DIR / 'data.json'

SERVER_IP = '127.0.0.1'
SERVER_PORT = 5000 # 8000

BUFFER = 1024

SERVER_IP_HTTP = '0.0.0.0'
SERVER_PORT_HTTP = 3000


def send_data_to_socket(body):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(body, (SERVER_IP, SERVER_PORT)) # 
    client_socket.close()


class MyHTTPHandler(BaseHTTPRequestHandler):
    def do_POST(self):

        body = self.rfile.read(int(self.headers['Content-Length']))

        send_data_to_socket(body)

        self.send_response(302) # команда браузеру куди перейти        
        self.send_header('Location', '/')
        self.end_headers()

    def do_GET(self):
        route = parse.urlparse(self.path)
        logging.info('route: {route}')
        match route.path:
            case '/':
                self.send_html('index.html')
            case '/message':
                self.send_html('message.html')
            case _:
                file = BASE_DIR / route.path[1::]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self, filename):
        self.send_response(200)

        mime_type, *rest = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')

        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())


def save_data(body):    
    try:
        if not FILE_STORAGE.exists():
            with open(FILE_STORAGE, 'w', encoding='utf-8') as fd:
                json.dump({}, fd, ensure_ascii=False)

        payload = {key: value for key, value in [el.split('=') for el in body.split('&')]} 
        
        current_time = dt.now().strftime("%Y-%m-%d %H:%M:%S.%f") [:-3]
        new_entry = {current_time: payload}

        existing_data = {}
        if FILE_STORAGE.is_file():
            with open(FILE_STORAGE, 'r', encoding='utf-8') as fd:
                existing_data = json.load(fd)

        existing_data.update(new_entry)

        with open(FILE_STORAGE, 'w', encoding='utf-8') as fd:
            json.dump(existing_data, fd, ensure_ascii=False, indent=0)

    except ValueError as err:
        logging.error(f'Field parse data {body} with error: {err}')
    except OSError as err:
        logging.error(f'Field write data {body} with error: {err}')


def run_http_server(ip: str, port: int):
    address = (ip, port)
    http_server = HTTPServer(address, MyHTTPHandler)
    logging.info(f'server_http is run')
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        logging.info('server_http stopped')
        http_server.server_close()
    finally:
        http_server.server_close()


def run_socket_server(ip: str, port: int):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket_address = (ip, port)
    server_socket.bind(server_socket_address)
    logging.info(f'server is run')

    try:
        while True:
            data, address = server_socket.recvfrom(BUFFER)  
            # logging.info(f'data == {data}') 
            data = parse.unquote_plus(data.decode())
            # logging.info(f'data_2 == {data}') 
            save_data(data)

    except KeyboardInterrupt:
        logging.info('Socket server stopped')
    except Exception as e:
        logging.error(f'Error in socket server: {e}')
    finally:
        server_socket.close()


if __name__=='__main__':
    logging.basicConfig(level=logging.INFO, format='%(threadName)s %(message)s')

    thread_server = Thread(target=run_http_server, args=(SERVER_IP_HTTP, SERVER_PORT_HTTP))
    thread_server.start()           

    thread_socket = Thread(target=run_socket_server, args=(SERVER_IP, SERVER_PORT))
    thread_socket.start()