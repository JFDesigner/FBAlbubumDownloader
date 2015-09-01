# FBAlbumDownloader

![FBAlbumDownloader](https://jflynndesigner.files.wordpress.com/2015/09/fbalbumdownloader_banner.png "FBAlbumDownloader")

FBAlbumDownloader is a command line Facebook Album Downloader that uses Python2.7. It does this by:

  - You supplying a Facebook album url that you have access to
  - The page is opened in the program using browser cookies from your Chrome browser
  - All the images are found and downloaded from that album to a folder

### Version
1.0.0

### Tech

Tested on Python 2.7.9, haven't seen how backwards compatible it is with older versions of 2.7.

FBAlbumDownloader uses a few additional modules to work properly:

* **[PyWin32]**         - Used to decrypt the cookies stored by Chrome (Windows Only) 
* **[sqlite3]**         - 3.8.0 or higher library for sqlite3 is needed to open the cookies from the database (Windows DLLs Included)
    * *Technical Jargen:* The database schema for Chrome cookies has been changed to utilize partial indexes, which are supported on SQLite 3.8.0 and higher. Python comes with 3.6.21 and needs an update to read the Cookies properly
* **[browser_cookie]**  - Loads cookies from your browser into a cookiejar object (included)
* **[mechanize]**       - Stateful programmatic web browsing in Python (included) 
* **[keyring]** - Used to decrypt the cookies stored by Chrome (Unix Only)

### Installation

*Only tested on Windows 7 (32-bit Python install) and 8.1 (64-bit Python install)*

1. Install PyWin32 at http://sourceforge.net/projects/pywin32/. Just use one of the executables to install on Windows.
2. Backup your Python sqlite3.dll at your Python27 DLL installation directory (mine is at C:\Python27\DLLs\sqlite3.dll)
    * I simply did this by renaming the file to sqlite3.dll.backup
3. Get/Compile an updated sqlite3 DLL for your OS and place it in your Python27 DLL installation directory
    * 32bit and 64bit versions are included in the download folder sqlite3. Copying the correct one to the directory should work.
    * If you want to download the latest version check https://www.sqlite.org/download.html
    * If you want to compile the dll yourself check https://www.sqlite.org/howtocompile.html

After that, you should be good to go! To check if everything has worked, run Python and enter these commands:

```python
>>> import win32crypt       # This is what is installed from PyWin32. If this fails to import, check your install
>>> import sqlite3          # This is for opening the cookies in Chrome. If this fails to import, check your install
>>> sqlite3.sqlite_version  # As long as the version is 3.8.0+ it should work fine
'3.8.11'
```

### How to Use

To use the code, simply use it from the command line doing the following:

```bat
D:\FBAlbumDownloader> python fbAlbumDownloader.py -h
usage: fbAlbumDownload [-h] [--version] [-dest [DEST]] [-nImgs [NIMGS]] [url]

Download a Facebook Album from a url.

positional arguments:
  url             a url to a Facebook Album

optional arguments:
  -h, --help      show this help message and exit
  --version       show program's version number and exit
  -dest [DEST]    a destination directory for the album (default:
                  C:\Users\Jon\Downloads)
  -nImgs [NIMGS]  the number of images in the library. If unset, will iterate
                  until a duplicate is found

```

Also, to note, the default destination directory will be your User folder followed by \Downloads

### Todos

 - Check workings with Mac and Linux
 - Implement so that Cookies arn't used from only Chrome browser 
 - Use login and store Cookies (tried with Mechanize, didn't work)
 - Implement multi-threading which finds all urls (work from start and from back) and then downloads them all
 - Basic interface and create executable

### Contact

If you have problems or questions then please contact me by emailing me at jonflynn@jfdesigner.co.uk.

### Website

Visit my portfolio to see more of my work and interesting programs at jfdesigner.co.uk.

License
----

GPL V2

