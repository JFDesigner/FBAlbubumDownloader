import urllib
import mechanize
import cookielib
from urlparse import urlparse

import browser_cookie

import os
import sys
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

class FacebookAlbumParser(HTMLParser):

    def __init__(self, destDir, browser):
        HTMLParser.__init__(self)
        self.browser = browser
        self.count = 0
        self.i = 0
        self.destDir = destDir
        self.isFbStarGrid = False
        self.starGridPhrase = "fbStarGrid fbStarGridAppendTo" # Found in <div> class=
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
                        self.count +=1
                        self.imagePage = attr[1]
                        self.openSaveImage()
                        self.isPhotoControlWrapper = False
                        break

    def openSaveImage(self):
        parser = FacebookImagePageParser(self.destDir, self.count)
        browser.open(self.imagePage)
        parser.feed(browser.response().read().decode("utf-8", "replace"))


class FacebookImagePageParser(HTMLParser):

    def __init__(self, destDir, count):
        HTMLParser.__init__(self)
        self.destDir = destDir
        self.count = count

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            if ("class", "fbPhotosPhotoActionsItem") in attrs and ("target", "_blank") in attrs:
                for attr in attrs:
                    if attr[0] == "href":
                        self.saveImage(attr[1])

    def saveImage(self, _url):
        data = openAsChrome(_url)
        o = urlparse(_url)
        filename = o.path.split('/')[-1]

        finalPath = os.path.join(self.destDir, filename)

        print self.count, ": Saving Image=> ", filename

        if os.path.exists(finalPath):
            print "Image already exists at that directory, skipping..."
        else:
            with open(os.path.join(self.destDir, filename), 'wb') as f:
                f.write(data)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("No arguments suppiled! pass: url [destDir]")
        #sys.exit(0)
        print "for testing we will use default page"
        url = r"https://www.facebook.com/ericdam27/media_set?set=a.10204998465376861.1073741845.1098742557&type=3"
    else:
        url = sys.argv[1]

    browser = mechanize.Browser()
    cj = browser_cookie.chrome()
    browser.set_cookiejar(cj)

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

    browser.addheaders.append(('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'))
    browser.addheaders.append(('Accept-Language', 'en-GB,en-US;q=0.8,en;q=0.6'))
    browser.addheaders.append(('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'))

    browser.open(url)

    browser.find_link(url="/facebook")

    if len(sys.argv) <= 2:
        print("No specified dest dir, default to Downloads\images folder.")
        destDir = r'H:\Users\Jon\Downloads\images'
    else:
        destDir = sys.argv[2]

    destDir = os.path.abspath(destDir)

    if not(os.path.isdir(destDir)):
        print("Directory doesn't exist. Making...")
        os.makedirs(destDir)

    destDir = os.path.abspath(destDir)


    data = browser.response().read()

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

    fbAlbumP = FacebookAlbumParser(destDir, browser)
    fbAlbumP.feed(data.decode("utf-8", "replace"))

    with open("result.html", "wb") as f:
        f.write(browser.response().read())

    with open("result2.html", "wb") as f:
        f.write(data)

    print fbAlbumP.count, "Images saved"