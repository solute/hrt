# coding: utf-8

import time, zlib, urllib2, urlparse, string, threading, base64
import BaseHTTPServer
import logging

import config
import visualizer
import injector
import sys

def base_href(url):
    p = urlparse.urlparse(url)
    return p.scheme + "://" + p.netloc + "/"


class HTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    protocol_version = "HTTP/1.0"

    def do_GET(self):
        """ Handle a GET-Request which was redirected here by injecting this servers URL """

        origin_url, url = injector.parse_path(self.path) # reconstruct the originial url

        if self.path.startswith("/stop/"):
            return

        logging.info("reading url " + repr(url))

        # append missing parts of the original-url
        if url.startswith("//"):
            url = "http:" + url
        elif not url.startswith("http"):
            url = base_href(origin_url) + url

        parsed_url = urlparse.urlparse(url)

        if url.endswith(".jpg") or url.endswith(".gif") or url.endswith(".png"):
            # images? - we do not need no stinkin images!
            content = u""
            info = {"Content-Type": "image/gif"}

        else:
            # create the request to the original URL and read it's content...
            headers = {"User-agent": "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11",
                       "Accept": "*/*",
                       "Accept-encoding": "identity",
                       "Referer": origin_url,
                       "Host": parsed_url.netloc}

            # ... using the original cookies ...
            for copy_header in ["Cookie", "X-Requested-With"]:
                if copy_header in self.headers:
                    headers[copy_header] = self.headers[copy_header]

            # ... fire ...
            req = urllib2.Request(url = url,
                                  headers = headers)

            # ... slurp ...
            try:
                opener = urllib2.build_opener()#urllib2.HTTPRedirectHandler, urllib2.HTTPCookieProcessor, urllib2.ProxyHandler)
                f = opener.open(req)
                info = f.info()
                content = ""
                while True:
                    time.sleep(0.1) # dirty but effective
                    chunk = f.read()
                    if not chunk:
                        break
                    content += chunk
                f.close()
            except urllib2.HTTPError:
                content = ""
                info = {"Content-Type": "none"}

            # ... if its compressed decompress it.
            if info.get("Content-Encoding") == "gzip":
                content = zlib.decompress(content, 16 + zlib.MAX_WBITS)

            # ... decode encoding ...
            if "charset=" in info["Content-Type"]:
                encoding = info["Content-Type"].split("charset=")[-1]
                if encoding[0] in "'\"":
                    encoding = encoding[1:-1]
                content = unicode(content, encoding)
            else:
                # ...or guess it!
                try:
                    content = unicode(content, "utf-8")
                except:
                    try:
                        content = unicode(content, "latin-1")
                    except:
                        print "Fucked up encoding in:", url

            # the current url is now the origin_url for injection
            # this will cause the downloads initiated by this document to have it self as origin_url
            origin_string = config.get("hrt_url") % base64.b64encode(url)
            content = injector.inject(content, info["Content-Type"], origin_string)


        self.send_response(200)

        # create the response for the original request...
        response_headers = {"Content-Length": str(len(content)),
                            "Cache-Control": "nocache", # disable caching
                            "Content-Type": info["Content-Type"]}

        # copy the headers
        for key, value in response_headers.items():
            self.send_header(key, value)
        self.end_headers()

        # send the response
        if type(content) is unicode:
            content = content.encode("utf-8")
        self.wfile.write(content)

##        self.write_to_disk(url, content)

        self.server.visualizer.add_relation(url = url, origin_url = origin_url)

    def log_message(self, *args):
        pass

    def write_to_disk(self, url, content):
        if not content:
            return

        url = url.replace("/", "_")
        url = url.replace("\\", "_")
        url = url.replace(":", "")
        url = url[:64]
        f = open("C_" + url, "wb")
        f.write(content)
        f.close()


class HTTPServer(BaseHTTPServer.HTTPServer):

    def __init__(self, *args):
        BaseHTTPServer.HTTPServer.__init__(self, *args)

        self.running = True
        self.visualizer = visualizer.Visualizer()


    def serve_forever(self):
        while self.running:
            self.handle_request()

    def stop(self):

        self.visualizer.visualize()

        def ping():
            url = config.get("hrt_url") % "stop"
            try:
                f = urllib2.urlopen(url, timeout = 1)
                f.read()
                f.close()
            except:
                pass

        logging.info("stop requested...")
        self.running = False

        # tickle the server a little bit...
        for i in range(3):
            t = threading.Thread(target = ping)
            t.start()


class ServerThread(threading.Thread):

    def run(self):

        server_address = ('127.0.0.1', config.get("server_port"))
        self.httpd = HTTPServer(server_address, HTTPRequestHandler)

        sa = self.httpd.socket.getsockname()
        logging.info("Serving HTTP on " + str(sa[0]) + " port " + str(sa[1]) + "...")
        self.httpd.serve_forever()
        logging.info("Server stopped.")


def start():
    """ Starts the server in a new thread and returns the server-thread-object """

    st = ServerThread()
    st.start()

    def stop():
        st.httpd.stop()

    st.stop = stop

    return st



