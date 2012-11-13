import os
import argparse
import re

from torero import ( Torero, TorrentzBlind, TorrentzDotCom, dest_exists,
        compute_bytes)


def get_episode(keywords, episode, destination, min_size='120Mb', max_size='400Mb', silent=True):
    '''
    Find an episode's torrent, matching keywords pattern,
    and download it into destination path.
    '''
    print('Looking for %s %s with size in %s' % (keywords, episode, (min_size, max_size)))
    #torero = Torero(TorrentzDotCom(), Torrage())
    torero = Torero(TorrentzDotCom(), TorrentzBlind())
    re_keywords = '(%s)' % '|'.join(keywords)
    re_keywords = re.compile(re_keywords, re.I)
    re_episode = re.compile(episode, re.I)
    min_size = compute_bytes(min_size)
    max_size = compute_bytes(max_size)
    # TODO: add max peers criteria
    torrents = torero.add_filter_predicate(
            lambda torrent: compute_bytes(torrent['size']) < max_size \
                and compute_bytes(torrent['size']) > min_size
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
    torero.download(torrent, destination)

def prepare_arg_parser():
    parser = argparse.ArgumentParser(
            description='Torrentz episode discovery',
            epilog='Example: episodes.py 7 10 defenders --prefix=S01E\n'
                    'episodes.py 2 3 "The Big Bang Theory" HDTV --prefix=S06E')
    parser.add_argument('--prefix', default='S01E')
    parser.add_argument('--minsize', default='120Mb')
    parser.add_argument('--maxsize', default='400Mb')
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
        get_episode(kwds_match, episode, downloads, args.minsize, args.maxsize)
 
