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


torrent_file_re = re.compile(r'href="http\:\/\/.*\.torrent"')


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
    pa = re.compile(r'(\d*)\s*(\w[bB])?')
    result = pa.search(size_str)
    if not result:
        raise Exception('Failed to parse size!')
    value = result.group(1)
    unit = result.group(2)
    if not unit:
        # assume those are bytes
        return value
    value = int(value)
    unit = unit.upper()
    powers = {'K': 1, 'M': 2, 'G': 3, 'T': 4}
    for letter in powers:
        if unit.startswith(letter):
            return value * 1024 ** powers[letter]
    return value

def read_url(url):
    torrent_file = urllib2.urlopen(url)
    data = torrent_file.read()
    if torrent_file.headers[CONTENT_ENCODING_HEADER] == 'gzip':
        #data = zlib.decompress(data)
        data = gzip.GzipFile(fileobj=StringIO(data)).read()
    else:
        assert torrent_file.headers[CONTENT_TYPE_HEADER]=='application/x-bittorrent'
    if len(data) <= 0:
        raise Exception('Failed to get torrent file!')    
    return data


def write_file(data, filename):
    print 'Writing file.. %s' % filename
    output = open(filename, 'wb')
    output.write(data)
    output.close()


class Downloader(object):

    @classmethod
    def read_url(cls, url):
        torrent_file = urllib2.urlopen(url)
        data = torrent_file.read()
        if torrent_file.headers[CONTENT_ENCODING_HEADER] == 'gzip':
            #data = zlib.decompress(data)
            data = gzip.GzipFile(fileobj=StringIO(data)).read()
        else:
            assert torrent_file.headers[CONTENT_TYPE_HEADER]=='application/x-bittorrent'
        if len(data) <= 0:
            raise Exception('Failed to get torrent file!')    
        return data

    @classmethod
    def write_file(cls, data, filename):
        print 'Writing file.. %s' % filename
        output = open(filename, 'wb')
        output.write(data)
        output.close()

    def get_torrent_data(self, url):
        return self.read_url(url)


class TorrentCache(Downloader):
    
    def get_torrent_data(self, url=None):
        if not url.startswith('http'):
            # assume url is torrent_id
            url = self.make_url(url)
        return Downloader.get_torrent_data(self, url)


class Torrage(TorrentCache):
    
    name = 'Torrage'

    def make_url(self, torrent_id):
        filename = '%s.torrent' % torrent_id.upper()
        url = 'http://torrage.com/torrent/' + filename
        return url


class CacheAwareDownloader(Downloader):
    
    def __init__(self, cache_sites=[], downloaders={}):
        self.cache_sites = [Torrage()]
        self.cache_sites.extend(cache_sites)
        self.downloaders = {}
        self.downloaders.update(downloaders)

    def find_torrent_url(self, torrent_site):
        # TODO: use specific downloader mathed by name from self.downloaders
        # Fallback to the following otherwise:
        print 'Parsing through: %s(%s)' % \
            (torrent_site['name'], torrent_site['url'])
        page = Torero.get_request(torrent_site['url'])
        found = torrent_file_re.search(page)
        #print page; exit()                
        if found:
            return found.group(0)

    def download(self, torrent, dir_path, torrent_sites={}, use_cache=False):
        torrent_data = None
        if use_cache:
            for cache_site in self.cache_sites:
                try:
                    torrent_data = cache_site.get_torrent_data(torrent['id'])
                except:
                    pass
                if torrent_data:
                    break
                print 'Failed to download from cache: ' + cache_site.name
        if torrent_sites:
            for torrent_site in torrent_sites:
                torrent_url = self.find_torrent_url 
                # We have url - now download..
                try:
                    torrent_data = torrent_site.get_torrent_data(torrent_url)
                except:
                    pass
                if torrent_data:
                    break
                print 'Failed to download from site: ' + torrent_site['name']
            if not torrent_url:
                raise Exception('Failed to find any torrent link')
        if not torrent_data:
            #print 'Failed to download: %s' % torrent
            return
        filename = os.sep.join((dir_path, '%s.torrent' % torrent['title'].replace(' ','')))
        self.write_file(torrent_data, filename)
        return True
             

class TorrentzBlind(CacheAwareDownloader):
    pass
    

class SearchEngine(object):

    def get_search_url(self):
        pass

    def parse_results(self, tree):
        pass


class TorrentzDotCom(SearchEngine):

    exclude_names = ['Download Direct']

    def get_search_url(self):
        return 'http://torrentz.eu/verified'

    def get_details_url(self, torrent_id):
        return 'http://torrentz.eu/%s' % torrent_id

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
            #print torrent
        return torrents

    def parse_details(self, tree):
        '''
        Return torrent sites containing links to torrent file of interest.
        '''
        results_div = tree.xpath('//div[@class=\'download\']')[0]
        def_list_items = results_div.xpath('dl')
        torrent_sites = list()
        for def_list_item in def_list_items:
            torrent_site = dict()
            link, update_time = def_list_item            
            torrent_site['url'] = link.find('a').get('href')
            torrent_site['name'] = link.find('a/span[@class=\'u\']').text
            if torrent_site['name'] in self.exclude_names:
                continue
            torrent_site['torrent_title'] = link.find('a/span[@class=\'n\']').text
            torrent_sites.append(torrent_site)
            #print torrent_file
        return torrent_sites

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

    @classmethod
    def get_request(cls, url, values=None, headers={}):
        if not USER_AGENT_HEADER in headers:
            headers[USER_AGENT_HEADER] = USER_AGENT
        if values:
            url += '?' + urllib.urlencode(values)
        req = urllib2.Request(url, headers=headers)
        response = urllib2.urlopen(req)
        return response.read()

    @classmethod
    def post_request(cls, url, values, headers={}):
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

    def get_torrent_sites(self, torrent):
        torrent_details_url = self._search_engine.get_details_url(torrent['id'])
        torrent_details_page = self.get_request(torrent_details_url)
        tree = self.parse_broken_html(torrent_details_page)
        torrent_sites = self._search_engine.parse_details(tree)
        return torrent_sites
    
    def download(self, torrent, dir_path):
        if not self._downloader.download(torrent, dir_path, use_cache=True):
            # try to use some downloaders instead
            sites = self.get_torrent_sites(torrent)
            self._downloader.download(torrent, dir_path, torrent_sites=sites)


def dest_exists(dir_path):
    if not os.path.exists(dir_path):
        user_input = raw_input('Create path %s (yes/no)?' % dir_path)
        if not user_input.startswith('y'):
            return False
        os.makedirs(dir_path)
    return True

