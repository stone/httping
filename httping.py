# -*- coding:utf-8 -*-
#!/usr/bin/python2.5
"""
httping - Ping like tool for http, display return-code, latency etc

Copyright (C) 2009 Fredrik Steen. Free use of this software is granted
under the terms of the GNU General Public License (GPL).
"""
from optparse import OptionParser
import httplib
import time
import socket
from datetime import datetime
from urlparse import urlparse


# Icky Globals
__VERSION__ = 0.1
USER_AGENT = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.10) Gecko/2009042523 Ubuntu/9.04 (jaunty) Firefox/3.0.10"

class HTTPing:
    def __init__(self, url, count, debug=False, quiet=False, flood=False, server_report=False):
        self.url = url
        self.count = count
        self.debug = debug
        self.quiet = quiet
        self.flood = flood
        self.server_report = server_report
        self.totals = []
        self.failed = 0
        self.server_header = None
        self.fail_codes = [500]
        self.urlparse()

    def urlparse(self):
        self.url_parsed = urlparse(self.url)

    def ping(self):
        try:
            self.ip = socket.gethostbyname(self.url_parsed.hostname)
        except socket.gaierror, e:
            print "Host %s not found" % self.url_parsed.hostname
            raise SystemExit
        if not self.quiet:
            print "HTTPING %s (%s)" % (self.url_parsed.hostname, self.ip)

        cnt = 0
        for x in range(0, int(self.count)):
            cnt += 1
            if self.url_parsed.scheme == 'http':
                (tt,code,reason) = self.http_connect()
            elif self.url_parsed.scheme == 'https':
                (tt,code,reason) = self.https_connect()
            else:
                print "url needs to start with 'http:// or https://'"
                raise SystemExit
            if tt is None:
                self.fail += 1
                continue
            elif code in self.fail_codes:
                self.fail += 1
                continue

            self.totals.append(tt)
            if not self.quiet:
                print "connected to %s (%s) seq=%s code=%s(%s) time=%s ms" % (self.url_parsed.netloc, self.ip, cnt, code, reason, tt)

            if not self.flood:
                time.sleep(1)

        self.report()
        if self.server_report:
            self.print_server_report()

    def print_server_report(self):

        for x in self.server_header:
            print "%s: %s" % x

    def http_connect(self):
        try:
            conn = httplib.HTTPConnection(self.url_parsed.netloc,
                    port=self.url_parsed.port,
                    timeout=30)
        except TypeError:
            conn = httplib.HTTPConnection(self.url_parsed.netloc,
                    port=self.url_parsed.port)
        try:
            conn.set_debuglevel(self.debug)
            stime = datetime.now()
            conn.request('HEAD', "/", None, {'User-Agent': USER_AGENT})
            resp = conn.getresponse()
            etime = datetime.now()
            resp_code = resp.status
            resp_reason = resp.reason
            if self.server_header is None:
                self.server_header = resp.getheaders()
        except Exception, e:
            return (None, None, None)
            #raise Exception("Connection Error: %s" % e)
        finally:
            conn.close()

        ttime = etime - stime
        milis = ttime.microseconds/1000
        return (milis, resp_code, resp_reason)
    
    def https_connect(self):
        try:
            conn = httplib.HTTPSConnection(self.url_parsed.netloc,
                    port=self.url_parsed.port,
                    timeout=30)
        except TypeError:
            conn = httplib.HTTPSConnection(self.url_parsed.netloc,
                    port=self.url_parsed.port)
        try:
            conn.set_debuglevel(self.debug)
            stime = datetime.now()
            conn.request('HEAD', "/", None, {'User-Agent':USER_AGENT})
            resp = conn.getresponse()
            etime = datetime.now()
            resp_code = resp.status
            resp_reason = resp.reason
            if self.server_header is None:
                self.server_header = resp.getheaders()
        except Exception, e:
            return (None,None,None)
        finally:
            conn.close()
        ttime = etime - stime
        milis = ttime.microseconds/1000
        return (milis, resp_code, resp_reason)

    def report(self):
        _num = len(self.totals)
        _min = min(self.totals)
        _max = max(self.totals)
        _average = float(sum(self.totals)) / len(self.totals)
        print "--- %s ---" % self.url
        print "%s connects, %s ok, %s%% failed" % (_num, _num-self.failed, self.failed/_num )
        print "round-trip min/avg/max = %s/%s/%s ms" % (_min, _average, _max)



def main():
    usage = "usage: %prog [options] url"
    version = "%%prog %s" % __VERSION__
    parser = OptionParser(usage=usage, version=version)
    parser.add_option("-d", "--debug",
                  action="store_true", dest="debug", default=False,
                  help="make lots of noise")
    parser.add_option("-q", "--quiet",
                  action="store_true", dest="quiet", default=False,
                  help="be vewwy quiet (I'm hunting wabbits)")
    parser.add_option("-f", "--flood",
                  action="store_true", dest="flood", default=False,
                  help="no delay between pings")
    parser.add_option("-s", "--server",
                  action="store_true", dest="server_report", default=False,
                  help="display verbose report")
    parser.add_option("-c", "--count", default=5,
                  dest="count", help="number of requests"),

    (options, args) = parser.parse_args()

    if len(args) < 1:
        print parser.error("need a url to ping, -h/--help for help")
        raise SystemExit

    if args[0][:7] != "http://" and args[0][:8] != "https://":
        print "url needs to start with 'http://' or 'https://'"
        raise SystemExit

    hping = HTTPing(args[0], options.count, options.debug,
        options.quiet, options.flood, options.server_report)
    try:
        hping.ping()
    except KeyboardInterrupt:
        hping.report()




if __name__ == '__main__':
        main()

