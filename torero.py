import re
import urllib
import urllib2
from lxml import etree
from StringIO import StringIO
import gzip
import sys
import os


USER_AGENT_HEADER = 'User-Agent'
USER_AGENT = 'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT)'
CONTENT_TYPE_HEADER = 'Content-Type'
CONTENT_ENCODING_HEADER = 'Content-Encoding'


def subtree_tostring(tree):
    text = ''.join(
        [etree.tostring(value) for value in tree]
    )
    if tree.text:
        text = tree.text + text
    return text


def remove_html_tags(html_str):
    if type(html_str) != str:
        html_str = subtree_tostring(html_str)
    pa = re.compile(r'<.*?>')
    return pa.sub('', html_str)

def compute_bytes(size_str):
    pa = re.compile(r'(\d*)\s*?(\w*?b)')
    result = pa.findall(size_str)
    if not result:
        return 0
    result = result[0]
    if len(result) != 2:
        print '!'
        if len(result) == 1:
            # We assume these digits are bytes
            return result[0]
        return 0
    value, unit = result
    value = int(value)
    unit = unit.upper()
    powers = {'K': 1, 'M': 2, 'G': 3, 'T': 4}
    for letter in powers:
        if unit.startswith(letter):
            return value * 1024 ** powers[letter]
    return value


class Downloader(object):

    def download(self, torrent_id, dir_path):
        pass


class Torrage(Downloader):

    def download(self, torrent_id, dir_path):
        filename = '%s.torrent' % torrent_id.upper()
        url = 'http://torrage.com/torrent/' + filename
        torrent_file = urllib2.urlopen(url)
        #assert(torrent_file.headers[CONTENT_TYPE_HEADER], 'application/x-bittorrent')
        data = torrent_file.read()
        if torrent_file.headers[CONTENT_ENCODING_HEADER] == 'gzip':
            #data = zlib.decompress(data)
            data = gzip.GzipFile(fileobj=StringIO(data)).read()
        output = open(dir_path + filename, 'wb')
        output.write(data)
        output.close()


class SearchEngine(object):

    def get_search_url(self):
        pass

    def parse_results(self, tree):
        pass


class TorrentzDotCom(SearchEngine):

    def get_search_url(self):
        return 'http://torrentz.com/verified'

    def parse_results(self, tree):
        results_div = tree.xpath('//div[@class=\'results\']')[0]
        def_list_items = results_div.xpath('dl')
        torrents = list()
        for def_list_item in def_list_items:
            torrent = dict()
            title, description = def_list_item
            torrent['id'] = title.find('a').get('href')[1:]
            torrent['title'] = remove_html_tags(title.find('a'))
            torrent['date'] = description.find('span[@class=\'a\']/span')\
                .get('title')
            torrent['size'] = description.find('span[@class=\'s\']').text
            torrents.append(torrent)
        return torrents
        

class Torero(object):

    def __init__(self, search_engine, downloader=None):
        self._search_engine = search_engine
        self._downloader = downloader
        self.predicates = list()

    def add_filter_predicate(self, predicate):
        self.predicates.append(predicate)
        return self

    def filter_results(self, results):
        for item in results:
            result = True
            for predicate in self.predicates:
                if not predicate(item):
                    result = False
                    break
            if result:
                yield item
            else:
                continue

    def get_request(self, url, values, headers={}):
        if not USER_AGENT_HEADER in headers:
            headers[USER_AGENT_HEADER] = USER_AGENT
        url += '?' + urllib.urlencode(values)
        req = urllib2.Request(url, headers=headers)
        response = urllib2.urlopen(req)
        return response.read()

    def post_request(self, url, values, headers={}):
        if not USER_AGENT_HEADER in headers:
            headers[USER_AGENT_HEADER] = USER_AGENT
        data = urllib.urlencode(values)
        req = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(req)
        return response.read()

    def parse_broken_html(self, broken_html):
        parser = etree.HTMLParser()
        return etree.parse(StringIO(broken_html), parser)

    def search_for(self, keywords):
        if not type(keywords) is str:
            keywords = ' '.join(keywords)
        params = {'f': keywords}
        url = self._search_engine.get_search_url()
        xhtml_page = self.get_request(url, params)
        tree = self.parse_broken_html(xhtml_page)
        results = self._search_engine.parse_results(tree)
        if self.predicates:
            results = list(self.filter_results(results))
        return results

    def download(self, torrent, dir_path):
        self._downloader.download(torrent['id'], dir_path)

def dest_exists(dir_path):
    if not os.path.exists(dir_path):
        user_input = raw_input('Create path %s (yes/no)?' % dir_path)
        if not user_input.startswith('y'):
            return False
        os.makedirs(dir_path)
    return True

   

