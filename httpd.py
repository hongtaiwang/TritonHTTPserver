import sys
import os
import socket
import time
import threading


class MyServer:
    def __init__(self, port, doc_root):
        self.port = port
        self.doc_root = doc_root
        self.host = '127.0.0.1'
        self.res_200 = "HTTP/1.1 200 OK\r\nServer: Myserver 1.0\r\n"

        self.res_404 = "HTTP/1.1 404 NOT FOUND\r\nServer: Myserver 1.0\r\n\r\n"

        self.res_400 = "HTTP/1.1 400 Client Error\r\nServer: Myserver 1.0\r\n\r\n"

        self.res_close = "HTTP/1.1 Connection:close\r\nServer: Myserver 1.0\r\n\r\n"

    # map request into dict
    def req_info(self, request):
        # 400 malform
        if request[-4:] != '\r\n\r\n':
            info = {'url': '400malform'}
            return info
        headers = request.splitlines()
        firstline = headers.pop(0)
        try:
            (act, url, version) = firstline.split()
        except ValueError:
            info = {'url': '400malform'}
            return info
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
        while i < len(x):
            if '' in x:
                x.remove('')
            if i < 0 or x[0] == '..' or len(x) == 0:  # path escape from file root
                info['url'] = '404escape'
                return info
            if i < len(x) and x[i] == '..':
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
        return info

    # generate response
    def res_gen(self, reqinfo):
        path = reqinfo['url']
        # 404 escape
        if path == '404escape':
            return self.res_404
        # 400 malform req
        if path == "400malform":
            return self.res_400
        try:
            reqinfo['Host'] and reqinfo['User-Agent']
        except KeyError:
            return self.res_400
        # 404 not found
        if not os.path.isfile(path):
            return self.res_404
        # a valid 200 req
        else:
            res = self.res_200
            res += "Last-Modified: {}\r\n".format(time.ctime(os.stat(path).st_mtime))
            with open(path, "rb") as f:
                data = f.read()
                res += "Content-Length: {}\r\n".format(len(data))
                if path.split('.')[-1] == 'html':
                    res += 'Content-Type: text/html\r\n\r\n'
                    res = res + str(data, 'utf-8')
                else:  # for jpg and png
                    if path.split('.')[-1] == 'png':
                        res += 'Content-Type: image/png\r\n\r\n'
                    else:
                        res += 'Content-Type: image/jpeg\r\n\r\n'
                    res = res + str(data)
        return res


def createsocket(conn, addr):
    with conn:
        try:
            conn.settimeout(5)
        except socket.timeout:
            conn.close()
            # print('closed')
        # print('Connected by', addr)
        while True:
            req = conn.recv(1024).decode()
            if not req:
                break
            info = server.req_info(req)
            msg = server.res_gen(info).encode()
            conn.sendall(msg)
            # print("msg send finished")
            # msg = server.res_close.encode()
            # conn.sendall(msg)
            break


if __name__ == '__main__':
    input_port = int(sys.argv[1])
    input_doc_root = sys.argv[2]
    server = MyServer(input_port, input_doc_root)
    # Add code to start your server here
    threads = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((server.host, server.port))
        s.listen()
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=createsocket(conn, addr), args=(conn, addr))
            t.start()
            threads.append(t)
            for t in threads:
                t.join()



