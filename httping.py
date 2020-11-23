#!/usr/bin/env python
"""
httping - Ping like tool for http, display return-code, latency etc

Copyright (C) 2009 Fredrik Steen. Free use of this software is granted
under the terms of the GNU General Public License (GPL).

Originally from: https://github.com/stone/httping
"""
from __future__ import print_function
try:
    import httplib
except ImportError:
    from http import client as httplib
import time
import socket
from datetime import datetime
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
from argparse import ArgumentTypeError, ArgumentParser
import math
import sys

# Icky Globals
__VERSION__ = 0.1
USER_AGENT = "httping v:{0} @ {1} ".format(__VERSION__, socket.gethostname())


class HTTPing:
    def __init__(self, url, count, timeout, sinterval, debug=False, errorfail=False, quiet=False, flood=False, server_report=False):
        self.url = url
        self.count = count
        self.debug = debug
        self.respsize = 0
        self.quiet = quiet
        self.flood = flood
        self.server_report = server_report
        self.totals = []
        self.failed = 0
        self.server_header = None
        self.fail_codes = [500]
        self.urlparse()
        self.timeout = float(timeout)
        self.report_interval = 60
        self.errorfail = errorfail
        self.sinterval = float(sinterval)

    def urlparse(self):
        self.url_parsed = urlparse(self.url)

    def connection(self):
        if self.url_parsed.scheme == 'https':
            class_ = httplib.HTTPSConnection
        else:
            class_ = httplib.HTTPConnection
        return class_(self.url_parsed.hostname,
                      port=self.url_parsed.port,
                      timeout=self.timeout)

    def ping(self):
        try:
            self.ip = socket.gethostbyname(self.url_parsed.hostname)
        except socket.gaierror as e:
            print("Error connecting to %s - %s" % (self.url_parsed.hostname, e))
            raise SystemExit
        if not self.quiet:
            print("HTTPING %s (%s)" % (self.url_parsed.hostname, self.ip))

        cnt = 0

        try:
            conn = self.connection()

        except Exception as e:
            raise Exception(e)

        while True:
            cnt += 1
            try:
                (tt, code, reason) = self.http_connect(conn)
                self.totals.append(tt)
                # This is not implemented yet
                # if code in self.fail_codes:
                #     self.fail += 1
                #     #continue
                if not self.quiet:
                    print("%d bytes from %s (%s) seq=%s code=%s (%s) time=%s ms" % (sys.getsizeof(self.respsize), self.url_parsed.netloc, self.ip, cnt, code, reason, tt))

            except Exception as e:
                if self.errorfail:
                    raise Exception(e)
                else:
                    self.failed += 1
                    conn = self.connection()
                    (tt, code, reason) = (None, None, e)
                    print("ERROR from %s (%s) seq=%s code=%s (%s) time=%s ms" % (self.url_parsed.netloc, self.ip, cnt, code, reason, tt))

            if cnt % self.report_interval == 0:
                hping.report()
                print('-------')
            if not self.flood:
                time.sleep(self.sinterval)

            if int(self.count) != 0:
                if cnt == int(self.count):
                    break

        conn.close()
        self.report()
        if self.server_report:
            self.print_server_report()

    def print_server_report(self):

        for x in self.server_header:
            print("%s: %s" % x)

    def http_connect(self, conn):
        conn.set_debuglevel(self.debug)
        stime = datetime.now()
        conn.request('GET', self.url_parsed.path, None, {'User-Agent': USER_AGENT})
        resp = conn.getresponse()
        # We don't use it but need read() here to do another http request
        self.respsize = resp.read()
        etime = datetime.now()
        resp_code = resp.status
        resp_reason = resp.reason
        if self.server_header is None:
            self.server_header = resp.getheaders()
        resp = None
        ttime = etime - stime
        milis = ttime.microseconds/1000
        return (milis, resp_code, resp_reason)

    def average(self, s):
        s = list(s)
        return sum(s) * 1.0 / len(s)

    def report(self):
        _num = len(self.totals)+self.failed if len(self.totals) !=0 else 0
        _min = min(self.totals) if len(self.totals) !=0 else 0
        _max = max(self.totals) if len(self.totals) !=0 else 0
        _avg = self.average(self.totals) if len(self.totals) !=0 else 0
        _variance = map(lambda x: (x - _avg)**2, self.totals) if len(self.totals) !=0 else 0
        _stdev = math.sqrt(self.average(_variance)) if len(self.totals) !=0 else 0
        _ok = _num - self.failed if len(self.totals) !=0 else 0
        print("--- %s ping statistics ---" % self.url)
        print("%s total, %s ok, %s failed" % (_num, _ok, self.failed))
        print("round-trip min/avg/max/stdev = %.3f/%.3f/%.3f/%.3f ms" % (_min, _avg, _max, _stdev))


if __name__ == '__main__':
    def check_url(url):
        if not str(url).startswith(('http://', 'https://')):
            raise ArgumentTypeError("{} is not a url".format(url))
        return url

    parser = ArgumentParser()
    parser.add_argument("-d", "--debug",
                        action="store_true", dest="debug", default=False,
                        help="make lots of noise")
    parser.add_argument("-e", "--errorfail",
                        action="store_true", dest="errorfail", default=False,
                        help="fail on connection error, default reconnect")
    parser.add_argument("-q", "--quiet",
                        action="store_true", dest="quiet", default=False,
                        help="be vewwy quiet (I'm hunting wabbits)")
    parser.add_argument("-f", "--flood",
                        action="store_true", dest="flood", default=False,
                        help="no delay between pings")
    parser.add_argument("-s", "--server",
                        action="store_true", dest="server_report", default=False,
                        help="display verbose report")
    parser.add_argument("-c", "--count", default=5,
                        dest="count", help="number of requests, 0 = infinity"),
    parser.add_argument("-i", "--interval", default=1,
                        dest="sinterval", help="sleep interval between packets"),
    parser.add_argument("-t", "--timeout", default=2,
                        dest="timeout", help="timeout"),
    parser.add_argument("url", help="URL to ping",
                        type=check_url)

    args = parser.parse_args()
    hping = HTTPing(args.url, args.count, args.timeout, args.sinterval, args.debug, args.errorfail,
                    args.quiet, args.flood, args.server_report)
    try:
        hping.ping()
    except KeyboardInterrupt:
        hping.report()
