import urllib
import mechanize
from urlparse import urlparse

import browser_cookie

import os
import sys
import re
from HTMLParser import HTMLParser
from HTMLParser import starttagopen
from HTMLParser import charref
from HTMLParser import entityref
from HTMLParser import incomplete

def openAsChrome(url):
    u = urllib.FancyURLopener()
    u.addheaders = []
    u.addheader('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36')
    u.addheader('Accept-Language', 'en-GB,en-US;q=0.8,en;q=0.6')
    u.addheader('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
    f = u.open(url)
    content = f.read()
    f.close()
    return content

def findAlbumTitle(data):
    #findTitle = re.compile('class="fbPhotoAlbumTitle">(.*)</h1>')
    #title = findTitle.match(data)
    phrase = 'class="fbPhotoAlbumTitle">'
    startPos = data.find(phrase) + len(phrase)
    endPos = data.find('<', startPos)
    title = data[startPos:endPos]
    h = HTMLParser()
    finalTitle = h.unescape(title)
    try:
        return finalTitle
    except:
        return "Unnamed"

def cleanHiddenElements(data):
    # Some of the code is hidden in scripts so we remove the code tags and get just the html
    phrase ='<code class="hidden_elem" '
    idPhrase = 'id="u_0_2d"><!-- ' # length is important, the id doesn't actually matter
    end = '</code>'
    findEnd = False

    while True:
        if findEnd:
            find = end
        else:
            find = phrase
        i = data.find(find)
        if i == -1:
            break
        data = data[:i+1] + data[i+len(find)+len(idPhrase)-1:]
        findEnd = not findEnd

    return data

class FacebookAlbumParser(HTMLParser):

    def __init__(self, browser):
        HTMLParser.__init__(self)
        self.browser = browser
        self.count = 0
        self.i = 0
        self.isTitle = False
        self.title = ""
        # ignore next div
        self.isPhotoControlWrapper = False # Found in next <div> with class=" _53s fbPhotoCurationControlWrapper"
        # use link from next <a> class
        self.isFinalLink = False # take the href of this one

        # go to the page
        self.imagePage = ""

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            for attr in attrs:
                if attr[0] == 'class' and "_53s fbPhotoCurationControlWrapper" in attr[1]:
                    self.isPhotoControlWrapper = True
                    break
        elif tag == "a":
            if self.isPhotoControlWrapper:
                for attr in attrs:
                    if attr[0] == 'href':
                        self.count += 1
                        self.imagePage = attr[1]
                        self.isPhotoControlWrapper = False
                        break

    def handle_data(self, data):
        pass

    def goahead(self, end):
        rawdata = self.rawdata
        i = 0
        n = len(rawdata)
        while i < n:
            if self.count >= 1:
                break
            match = self.interesting.search(rawdata, i) # < or &
            if match:
                j = match.start()
            else:
                if self.cdata_elem:
                    break
                j = n
            if i < j: self.handle_data(rawdata[i:j])
            i = self.updatepos(i, j)
            if i == n: break
            startswith = rawdata.startswith
            if startswith('<', i):
                if starttagopen.match(rawdata, i): # < + letter
                    k = self.parse_starttag(i)
                elif startswith("</", i):
                    k = self.parse_endtag(i)
                elif startswith("<!--", i):
                    k = self.parse_comment(i)
                elif startswith("<?", i):
                    k = self.parse_pi(i)
                elif startswith("<!", i):
                    k = self.parse_html_declaration(i)
                elif (i + 1) < n:
                    self.handle_data("<")
                    k = i + 1
                else:
                    break
                if k < 0:
                    if not end:
                        break
                    k = rawdata.find('>', i + 1)
                    if k < 0:
                        k = rawdata.find('<', i + 1)
                        if k < 0:
                            k = i + 1
                    else:
                        k += 1
                    self.handle_data(rawdata[i:k])
                i = self.updatepos(i, k)
            elif startswith("&#", i):
                match = charref.match(rawdata, i)
                if match:
                    name = match.group()[2:-1]
                    self.handle_charref(name)
                    k = match.end()
                    if not startswith(';', k-1):
                        k = k - 1
                    i = self.updatepos(i, k)
                    continue
                else:
                    if ";" in rawdata[i:]: #bail by consuming &#
                        self.handle_data(rawdata[0:2])
                        i = self.updatepos(i, 2)
                    break
            elif startswith('&', i):
                match = entityref.match(rawdata, i)
                if match:
                    name = match.group(1)
                    self.handle_entityref(name)
                    k = match.end()
                    if not startswith(';', k-1):
                        k = k - 1
                    i = self.updatepos(i, k)
                    continue
                match = incomplete.match(rawdata, i)
                if match:
                    # match.group() will contain at least 2 chars
                    if end and match.group() == rawdata[i:]:
                        self.error("EOF in middle of entity or char ref")
                    # incomplete
                    break
                elif (i + 1) < n:
                    # not the end of the buffer, and can't be confused
                    # with some other construct
                    self.handle_data("&")
                    i = self.updatepos(i, i + 1)
                else:
                    break
            else:
                assert 0, "interesting.search() lied"
        # end while
        if end and i < n and not self.cdata_elem:
            self.handle_data(rawdata[i:n])
            i = self.updatepos(i, n)
        self.rawdata = rawdata[i:]

class FacebookImagePageParser(HTMLParser):

    def __init__(self, destDir):
        HTMLParser.__init__(self)
        self.destDir = destDir
        self.nextPage = ""
        self.count = 0
        self.imgNum = 0
        self.isRepeat = False
        self.complete = False

    def goahead(self, end):
        self.complete = False
        self.isRepeat = False
        rawdata = self.rawdata
        i = 0
        n = len(rawdata)
        while i < n:
            if self.complete or self.isRepeat:
                break
            match = self.interesting.search(rawdata, i) # < or &
            if match:
                j = match.start()
            else:
                if self.cdata_elem:
                    break
                j = n
            if i < j: self.handle_data(rawdata[i:j])
            i = self.updatepos(i, j)
            if i == n: break
            startswith = rawdata.startswith
            if startswith('<', i):
                if starttagopen.match(rawdata, i): # < + letter
                    k = self.parse_starttag(i)
                elif startswith("</", i):
                    k = self.parse_endtag(i)
                elif startswith("<!--", i):
                    k = self.parse_comment(i)
                elif startswith("<?", i):
                    k = self.parse_pi(i)
                elif startswith("<!", i):
                    k = self.parse_html_declaration(i)
                elif (i + 1) < n:
                    self.handle_data("<")
                    k = i + 1
                else:
                    break
                if k < 0:
                    if not end:
                        break
                    k = rawdata.find('>', i + 1)
                    if k < 0:
                        k = rawdata.find('<', i + 1)
                        if k < 0:
                            k = i + 1
                    else:
                        k += 1
                    self.handle_data(rawdata[i:k])
                i = self.updatepos(i, k)
            elif startswith("&#", i):
                match = charref.match(rawdata, i)
                if match:
                    name = match.group()[2:-1]
                    self.handle_charref(name)
                    k = match.end()
                    if not startswith(';', k-1):
                        k = k - 1
                    i = self.updatepos(i, k)
                    continue
                else:
                    if ";" in rawdata[i:]: #bail by consuming &#
                        self.handle_data(rawdata[0:2])
                        i = self.updatepos(i, 2)
                    break
            elif startswith('&', i):
                match = entityref.match(rawdata, i)
                if match:
                    name = match.group(1)
                    self.handle_entityref(name)
                    k = match.end()
                    if not startswith(';', k-1):
                        k = k - 1
                    i = self.updatepos(i, k)
                    continue
                match = incomplete.match(rawdata, i)
                if match:
                    # match.group() will contain at least 2 chars
                    if end and match.group() == rawdata[i:]:
                        self.error("EOF in middle of entity or char ref")
                    # incomplete
                    break
                elif (i + 1) < n:
                    # not the end of the buffer, and can't be confused
                    # with some other construct
                    self.handle_data("&")
                    i = self.updatepos(i, i + 1)
                else:
                    break
            else:
                assert 0, "interesting.search() lied"
        # end while
        if end and i < n and not self.cdata_elem and not self.isRepeat:
            self.handle_data(rawdata[i:n])
            i = self.updatepos(i, n)

        if self.isRepeat:
            self.rawdata=""
        else:
            self.rawdata = rawdata[i:]

        return self.complete

    def feed(self, data):
        r"""Feed data to the parser.

        Call this as often as you want, with as little or as much text
        as you want (may include '\n').
        """
        self.rawdata = self.rawdata + data
        return self.goahead(0)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            if ("class", "fbPhotosPhotoActionsItem") in attrs and ("target", "_blank") in attrs:
                for attr in attrs:
                    if attr[0] == "href":
                        self.saveImage(attr[1])
                        break

    def saveImage(self, _url):
        data = openAsChrome(_url)
        o = urlparse(_url)
        filename = o.path.split('/')[-1]

        finalPath = os.path.join(self.destDir, filename)

        print self.count, ": Saving Image=> ", filename

        if os.path.exists(finalPath):
            print "Image already exists at that directory, ending image downloads..."
            self.isRepeat = True
        else:
            with open(os.path.join(self.destDir, filename), 'wb') as f:
                f.write(data)
                self.count += 1
                self.complete = True


def main(argv):
    # handle url info
    if len(argv) <= 1:
        print "No arguments suppiled! pass: url [destDir]"
        url = r"https://www.facebook.com/ericdam27/media_set?set=a.10204998465376861.1073741845.1098742557"
        # return 1
    else:
        url = argv[1]

    o = urlparse(url)
    path = o.path.split('/')

    browser = mechanize.Browser()
    cj = browser_cookie.chrome()
    browser.set_cookiejar(cj)

    # set broswer settings
    browser.set_handle_equiv(True)
    #browser.set_handle_gzip(True)
    browser.set_handle_redirect(True)
    browser.set_handle_referer(True)
    browser.set_handle_robots(False)

    # Follows refresh 0 but not hangs on refresh > 0
    browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

     # Want debugging messages?
    # browser.set_debug_http(True)
    # browser.set_debug_redirects(True)
    # browser.set_debug_responses(True)

    # append some headings to make the browser act like modern browsers
    browser.addheaders.append(('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'))
    browser.addheaders.append(('Accept-Language', 'en-GB,en-US;q=0.8,en;q=0.6'))
    browser.addheaders.append(('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'))

    # open the album page url
    browser.open(url)

    data = cleanHiddenElements(browser.response().read())

    title = findAlbumTitle(browser.response().read())

    # handle destination directory
    if len(argv) <= 2:
        destDir = os.path.join(os.path.expanduser(r'~\Downloads'), path[1], title)
        print "No specified dest dir, default to {} folder.".format(destDir)
    else:
        destDir = os.path.join(argv[2], path[1], title)

    destDir = os.path.abspath(destDir)

    if not(os.path.isdir(destDir)):
        print "Directory \"{}\" doesn't exist. Making folders...".format(destDir)
        os.makedirs(destDir)

    with open("test.html", "wb") as f:
        f.write(data)

    # the album parser
    fbAlbumP = FacebookAlbumParser(browser)
    fbAlbumP.feed(data.decode("utf-8", "replace"))

    # open the first image page of the album
    browser.open(fbAlbumP.imagePage)
    # create the html image parser
    imgParser = FacebookImagePageParser(destDir)
    complete = False

    # go through all images and parse to download the images
    while True:
        complete = imgParser.feed(browser.response().read().decode("utf-8", "replace"))
        if not complete:
            break
        browser.follow_link(text="Next")

    print imgParser.count, "Images saved"
    return 0

if __name__ == "__main__":
    main(sys.argv)
