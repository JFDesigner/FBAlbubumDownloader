# -*- coding: utf-8 -*-

import __init__ as common
import urllib2
import re


def main():
    cj = common.chrome()
    #cj = common.firefox()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
    for key, value in hdr.iteritems():
        opener.addheaders.append((key, value))
    url = 'https://bitbucket.org/'
    get_title = lambda html: re.findall('<title>(.*?)</title>', html, flags=re.DOTALL)[0].strip()
    login_html = opener.open(url).read()
    print get_title(login_html)

if __name__ == '__main__':
    main()

