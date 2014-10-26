__author__ = 'ethan'

from log_settings import LOGGING
import logging
import logging.config
import urllib
import urllib2
import re
from database import CrawlerDb

#Setting for Logging
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("crawler_logger")

# Number of web pages will be searched
SEARCH_RESULTS = 20

google_adurl_regex = re.compile('adurl=(.*?)"')
google_url_regex = re.compile('url\?q=(.*?)&amp;sa=')
email_regex = re.compile('([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4})', re.IGNORECASE)
url_regex = re.compile('<a\s.*?href=[\'"](.*?)[\'"].*?>')

# Connect to database
db = CrawlerDb()
db.connect()

def crawler(keywords):
    """
    This method will:
    1. Google search the keyword(s) and return SEARCH_RESULTS number of pages
    2. For every searched webpage, crawl the webpage 2 level-deep. That means the webpage
       itself and all its linking pages. If at least one emails was found, then return that
       email and don't crawl the second level.
    3.

    :param keywords:
    :return:
    """

    logger.info("-"*40)
    logger.info("Keywords to Google for: %s" % keywords)
    logger.info("-"*40)

    # Step 1: using Google to search the keywords and return the first SEARCH_RESULTS pages
    # Google search results are paged with 10 urls each. There are also adurls
    for pageIndex in range(0, SEARCH_RESULTS):
        query = {'q': keywords}
        url = 'http://www.google.com/search?' + urllib.urlencode(query) + '&start=' + str(pageIndex)
        data = retrieve_html(url)
        for url in google_url_regex.findall(data):


def retrieve_html(url):
    """
    Crawl a website, and returns the whole html as an ascii string.

    On any error, return.
    """
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Just-Crawling 0.1')
    request = None
    status = 0
    try:
        logger.info("Crawling %s" % url)
        request = urllib2.urlopen(req)
    except urllib2.URLError, e:
        logger.error("Exception at url: %s\n%s" % (url, e))
    except urllib2.HTTPError, e:
        status = e.code
    except Exception, e:
        return
    if status == 0:
        status = 200

    try:
        data = request.read()
    except Exception, e:
        return

    return str(data)