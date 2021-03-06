__author__ = 'ethan cheng'
# CSCE515 Term Project
# Simple web crawler

from log_settings import LOGGING
import logging
import logging.config
import urlparse
import urllib
import urllib2
import re
import traceback
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

EMAILS_FILENAME = 'data/emails.csv'
DOMAINS_FILENAME = 'data/domains.csv'

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
            db.enqueue(url)
        for url in google_adurl_regex.findall(data):
            db.enqueue(url)

    # Step 2: Crawl each of the search result for 2-level depth
    while True:
        #get the first uncrawled result from db
        uncrawled = db.dequeue()
        if uncrawled is False:
            break
        email_set = find_emails(uncrawled.url)
        if len(email_set) > 0:
            db.crawled(uncrawled, ",".join(list(email_set)))
        else:
            db.crawled(uncrawled, None)


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
    except urllib2.URLError as e:
        logger.error("Exception at url: %s\n%s" % (url, e))
    except urllib2.HTTPError as e:
        status = e.code
    except:
        return
    if status == 0:
        status = 200

    try:
        data = request.read()
    except:
        return

    return str(data)


def find_emails(url):
	"""
	Find the email at level 1.
	If there is an email, good. Return that email
	Else, find in level 2. Store all results in database directly, and return None
	"""
	html = retrieve_html(url)
	email_set = find_emails_in_html(html)

	if len(email_set) > 0:
		# If there is a email, we stop at level 1.
		return email_set

	else:
		# No email at level 1. Crawl level 2
		logger.info('No email at level 1.. proceeding to crawl level 2')

		link_set = find_links(url, html)
		for link in link_set:
			# Crawl them right away!
			# Enqueue them too
			html = retrieve_html(link)
			if html is None:
				continue
			email_set = find_emails_in_html(html)
			db.enqueue(link, list(email_set))

		# We return an empty set
		return set()


def find_emails_in_html(html):
	if html is None:
		return set()
	email_set = set()
	for email in email_regex.findall(html):
		email_set.add(email)
	return email_set


def find_links(url, html):
	"""
	Find all the links with same hostname as url
	"""
	if html is None:
		return set()
	url = urlparse.urlparse(url)
	links = url_regex.findall(html)
	link_set = set()
	for link in links:
		if link is None:
			continue
		try:
			link = str(link)
			if link.startswith("/"):
				link_set.add('http://' + url.netloc + link)
			elif link.startswith("http") or link.startswith("https"):
				if link.find(url.netloc):
					link_set.add(link)
			elif link.startswith("#"):
				continue
			else:
				link_set.add(urlparse.urljoin(url.geturl(), link))
		except:
			pass

	return link_set

if __name__ == "__main__":
	import sys
	try:
		arg = sys.argv[1].lower()
		if (arg == '--emails') or (arg == '-e'):
			# Get all the emails and save in a CSV
			logger.info("="*40)
			logger.info("Processing...")
			emails = db.get_all_emails()
			logger.info("There are %d emails" % len(emails))
			file = open(EMAILS_FILENAME, "w+")
			file.writelines("\n".join(emails))
			file.close()
			logger.info("All emails saved to ./data/emails.csv")
			logger.info("="*40)
		elif (arg == '--domains') or (arg == '-d'):
			# Get all the domains and save in a CSV
			logger.info("="*40)
			logger.info("Processing...")
			domains = db.get_all_domains()
			logger.info("There are %d domains" % len(domains))
			file = open(DOMAINS_FILENAME, "w+")
			file.writelines("\n".join(domains))
			file.close()
			logger.info("All domains saved to ./data/domains.csv")
			logger.info("="*40)
		else:
			# Crawl the supplied keywords!
			crawler(arg)

	except KeyboardInterrupt:
		logger.error("Stopping (KeyboardInterrupt)")
		sys.exit()
	except Exception as e:
		logger.error("EXCEPTION: %s " % e)
		traceback.print_exc()