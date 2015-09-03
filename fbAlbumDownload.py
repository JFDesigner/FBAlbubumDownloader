import urllib
import mechanize
from urlparse import urlparse
import argparse

import browser_cookie

import os
from HTMLParser import HTMLParser, starttagopen, charref, entityref, incomplete

__version__ = "0.0.1"
__file__ = "fbAlbumDownload.py"


def open_as_browser(url):
    """
    Used to open a basic url as a modern browser
    :param url: The url to open
    :return: the html data as a byte string
    """
    u = urllib.FancyURLopener()
    u.addheaders = []
    u.addheader('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36')
    u.addheader('Accept-Language', 'en-GB,en-US;q=0.8,en;q=0.6')
    u.addheader('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
    f = u.open(url)
    content = f.read()
    f.close()
    return content


def save_image(url, destination_dir):
    """
    Saves an image or a url passed
    :param url: the image/page to be saved
    :param destination_dir: the destination directory for the image
    :return: True/False if the the image was saved or not based on if the file already exists
    """
    o = urlparse(url)
    filename = o.path.split('/')[-1]
    final_path = os.path.join(destination_dir, filename)

    print filename

    if os.path.exists(final_path):
        print "Image already exists at that directory. Stop Download."
        return False
    else:
        with open(final_path, 'wb') as f:
            data = open_as_browser(url)
            f.write(data)
            return True


def create_chrome_browser():
    """
    Creates a mechanize Chrome browser including the correct settings, headers and cookies
    :return: Mechanize Browser object
    """
    browser = mechanize.Browser()
    cj = browser_cookie.chrome()
    browser.set_cookiejar(cj)

    # set browser settings
    browser.set_handle_equiv(True)
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
    browser.addheaders.append(('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64)'
                               'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'))
    browser.addheaders.append(('Accept-Language', 'en-GB,en-US;q=0.8,en;q=0.6'))
    browser.addheaders.append(('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'))

    return browser


def find_album_title(data):
    """
    Find the title of the album in the web-page using basic string find
    :param data: the html of the page
    :return: a string with the name of the album
    """
    phrase = 'class="fbPhotoAlbumTitle">'
    start_pos = data.find(phrase) + len(phrase)
    end_pos = data.find('<', start_pos)
    title = data[start_pos:end_pos]
    # used to replace the html symbols with unicode symbols
    h = HTMLParser()
    final_title = h.unescape(title)
    if final_title != "":
        return final_title
    else:
        return "Unnamed"


def clean_hidden_code_elements(data):
    """
    Remove some of the hidden code in the page that is inside <code> tags and get all the html in a normal format
    :param data: the html of the page
    :return: the code stripped html
    """
    phrase = '<code class="hidden_elem" '
    id_phrase = 'id="u_0_2d"><!-- '  # length is important, the id string doesn't actually matter
    end = '</code>'
    try_find_end = False

    while True:
        if try_find_end:
            find = end
        else:
            find = phrase
        i = data.find(find)
        if i == -1:
            break
        data = data[:i+1] + data[i+len(find)+len(id_phrase)-1:]
        try_find_end = not try_find_end

    return data


class FacebookAlbumParser(HTMLParser):

    def __init__(self, browser):
        """
        Used to parse the Facebook Album html. Used to get the first image link in the page from the album and is
        stored in self.imagePage
        :param browser: the browser
        :return:
        """
        HTMLParser.__init__(self)
        self.browser = browser
        self.isTitle = False
        self.title = ""

        self.isPhotoControlWrapper = False  # Found in next <div> with class=" _53s fbPhotoCurationControlWrapper"

        self.isImagePageFound = False

        # go to the page
        self.imagePage = ""

    def handle_starttag(self, tag, attrs):
        # used to find first image control wrapper and take the link after it
        if tag == "div":
            for attr in attrs:
                if attr[0] == 'class' and "_53s fbPhotoCurationControlWrapper" in attr[1]:
                    self.isPhotoControlWrapper = True
                    break
        # if the div before is the photo wrapper and we have a link then take the url since this is the image page
        elif tag == "a" and self.isPhotoControlWrapper:
            for attr in attrs:
                if attr[0] == 'href':
                    self.imagePage = attr[1]
                    self.isImagePageFound = True
                    break

    def goahead(self, end):
        # same as inherit except break statement in start of while loop
        rawdata = self.rawdata
        i = 0
        n = len(rawdata)
        while i < n:
            if self.isImagePageFound:  # added to stop searching through html after the image page is found
                break
            match = self.interesting.search(rawdata, i)  # < or &
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
                if starttagopen.match(rawdata, i):  # < + letter
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
                    if ";" in rawdata[i:]:  # bail by consuming &#
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


def image_process(browser, count, destination_dir):
    """
    Processes the image page, saves the image and continues to the next page
    :param browser: the Mechanize chrome browser containing all our Cookies
    :param count: The image download count
    :param destination_dir: The destination directory for the image
    :return: True/False if the image was saved, the image count
    """
    # find the download link
    img_url = browser.find_link(text="Download")
    print "{:0=3}".format(count+1), ": Saving Image=> ",
    # save the image
    is_not_repeat = save_image(img_url.url, destination_dir)
    # if successful save, increment count
    if is_not_repeat:
        count += 1
    # go to the next page
    browser.follow_link(text="Next")
    return is_not_repeat, count


def main(url, destination, num_imgs):
    """
    Main function that runs on start
    :param url: the facebook album page url
    :param destination: the destination directory for the images
    :param num_imgs: the number of images in the directory, if specified
    :return: 0 or 1, Success or Failure
    """
    # handle url info
    o = urlparse(url)
    if o.netloc != "www.facebook.com":
        print "Website is not apart of Facebook. The netloc is \"{}\". Try again".format(o.netloc)
        return 1

    # create the browser with imported cookies and correct headers and options
    browser = create_chrome_browser()

    # open the album page url
    browser.open(url)

    # check if we have permission to access the page
    if 'Sorry, this content isn\'t available at the moment' in browser.response().read():
        print "You don't have permission to access the Facebook page. Try another page."
        return 1

    # clean code segments of the page and store the html
    data = clean_hidden_code_elements(browser.response().read())
    # get the title of the album
    title = find_album_title(browser.response().read())

    # handle destination directory
    destination_dir = os.path.abspath(os.path.join(destination, title))
    print "Saving files to {} folder.".format(destination_dir)

    if not(os.path.isdir(destination_dir)):
        print "Directory \"{}\" doesn't exist. Making folders...".format(destination_dir)
        os.makedirs(destination_dir)

    # the album parser
    fb_album_parser = FacebookAlbumParser(browser)
    fb_album_parser.feed(data.decode("utf-8", "replace"))

    # open the first image page of the album
    browser.open(fb_album_parser.imagePage)

    count = 0
    is_not_repeat = True
    # go through all images and parse to download the images
    if not num_imgs:
        while is_not_repeat:
            is_not_repeat, count = image_process(browser, count, destination_dir)
    else:
        for i in xrange(num_imgs):
            is_not_repeat, count = image_process(browser, count, destination_dir)

    # final image count
    print count, "Images saved"
    return 0

if __name__ == "__main__":
    # create the default download directory to the users download folder
    download_dir = os.path.expanduser(r'~\Downloads')

    # passes all the arguments so the code can be used as a command line program
    parser = argparse.ArgumentParser(prog='fbAlbumDownload', description="Download a Facebook Album from a url.")
    parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
    parser.add_argument('url', metavar='url', type=str, help="a url to a Facebook Album", nargs='?')
    parser.add_argument('-dest', type=str, nargs='?', default=download_dir,
                        help="a destination directory for the album (default: {})".format(download_dir))
    parser.add_argument('-nImgs', type=int, nargs='?',
                        help="the number of images in the library. If unset, will iterate until a duplicate is found")
    # parse the arguments
    args = parser.parse_args()

    print ""
    if args.url is not None:
        main(args.url, args.dest, args.nImgs)
