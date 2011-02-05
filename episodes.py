import os
import argparse
import re

from torero import ( Torero, Torrage, TorrentzDotCom, dest_exists,
        compute_bytes)


def get_episode(keywords, episode, destination, silent=True):
    '''
    Find an episode's torrent, matching keywords pattern,
    and download it into destination path.
    '''
    print('Looking for %s %s' % (keywords, episode))
    torero = Torero(TorrentzDotCom(), Torrage())
    re_keywords = re.compile(keywords, re.I)
    re_episode = re.compile(episode, re.I)
    size_limit = compute_bytes('400 Mb')
    torrents = torero.add_filter_predicate(
            lambda torrent: compute_bytes(torrent['size']) < size_limit
        ).add_filter_predicate(
            lambda torrent: re_keywords.search(torrent['title'])
        ).add_filter_predicate(
            lambda torrent: re_episode.search(torrent['title'])
        ).search_for(keywords + ' ' + episode)
    # download torrent
    if not torrents:
        print('Episode %s was not found.' % episode)
        return
    torrent = torrents[0]
    print 'Found: ' + torrent['title'] + ' ' + torrent['size']
    if not silent:
        user_input = raw_input("Download (yes/no)?")
        if not user_input.startswith('y'):
            print 'Skipping'
            return
    torero.download(torrents[0], destination)

def prepare_arg_parser():
    parser = argparse.ArgumentParser(
            description='Torrentz episode discovery',
            epilog='Example: episodes.py 7 10 defenders --prefix=S01E')
    parser.add_argument('--prefix', default='S01E')
    parser.add_argument('range', type=int, nargs=2)
    parser.add_argument('keywords', nargs='*')
    default_download_dest = os.path.join(os.getcwd(), 'downloads', '')
    parser.add_argument('--downloads', default=default_download_dest)
    return parser


if __name__ == '__main__':
    # Parse command line arguments.
    parser = prepare_arg_parser()
    args = parser.parse_args()
    season_prefix = args.prefix
    kwds_match = ' '.join(args.keywords)
    episodes = xrange(args.range[0], args.range[1] + 1)
    downloads = args.downloads
    # Check if downloads path is ready.
    if not dest_exists(downloads):
        parser.exit('Failed to download to %s' % downloads)
    # Find and download episodes.
    for episode_num in episodes:
        episode = season_prefix + str(episode_num).zfill(2)
        get_episode(kwds_match, episode, downloads)
 
