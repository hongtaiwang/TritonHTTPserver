import sys
import os
import socket
import time
import threading


class MyServer:
    def __init__(self, port, doc_root):
        self.port = port
        self.doc_root = doc_root
        self.host = "localhost"
        self.res_200 = "HTTP/1.1 HTTP/1.1 200 OK\r\nServer: Myserver 1.0\r\n"

        self.res_404 = "HTTP/1.1 404 NOT FOUND\r\nServer: Myserver 1.0\r\n\r\n"

        self.res_400 = "HTTP/1.1 400 MALFORMED REQ\r\nServer: Myserver 1.0\r\n\r\n"

        self.res_close = "HTTP/1.1 Connection:close\r\nServer: Myserver 1.0\r\n\r\n"

    """
    Add your server and handlers here.

    """
    # map request into dict
    def req_info(self, request):
        headers = request.splitlines()
        firstline = headers.pop(0)
        try:
            (act, url, version) = firstline.split()
        except ValueError:
            return "400malform"
        info = {'act': act, 'url': url, 'version': version}
        for h in headers:
            h = h.split(': ')
            if len(h) < 2:
                continue
            field = h[0]
            value = h[1]
            info[field] = value
        # mapping url, return 404 escape or absolute filename
        # judge whether escape
        path = ''
        x = url.split('/')
        i = 0
        while (i < len(x)):
            if '' in x:
                x.remove('')
            if i < 0 or x[0] == '..':  # path escape from file root
                return '404escape'
            if x[i] == '..':
                x.remove(x[i])
                x.remove(x[i - 1])
                i -= 1
            else:
                i += 1
        # map index.html
        if len(x[-1].split('.')) < 2:
            x.append('index.html')
        for d in range(len(x)):
            path = path + '/' + x[d]
        info['url'] = os.path.realpath(self.doc_root + path)
        print(info)
        return info

    # generate response
    def res_gen(self, reqinfo):
        if reqinfo == "400malform":
            return self.res_400
        path = reqinfo['url']
        try:
            reqinfo['Host'] and reqinfo['User-Agent']
        except KeyError:
            return self.res_400

        if path == '404escape' or not os.path.isfile(path):
            return self.res_404
        # a valid 200 req
        else:
            res = self.res_200
            res += "Last-Modified: {}\r\n".format(time.ctime(os.stat(path).st_mtime))
            with open(path, "rb") as f:
                data = f.read()
                res += "Content-Length: {}\r\n".format(len(data))
                if path.split('.')[-1] == 'html':
                    res = res + str(data, 'utf-8')
                else:  # for jpg and png
                    res = res + str(data)
        return res


def createsocket(conn, addr):
    with conn:
        print('Connected by', addr)
        while True:
            req = conn.recv(1024).decode()
            if not req:
                break
            info = server.req_info(req)
            msg = server.res_gen(info).encode()
            conn.sendall(msg)
            print("msg send finished")
            # msg = server.res_close.encode()
            # conn.sengall(msg)
            break


if __name__ == '__main__':
    input_port = int(sys.argv[1])
    input_doc_root = sys.argv[2]
    server = MyServer(input_port, input_doc_root)
    # Add code to start your server here
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((server.host, server.port))
            s.listen()
            conn, addr = s.accept()
            s.settimeout(5)
            t = threading.Thread(target=createsocket(conn, addr), args=(conn, addr)).start()

