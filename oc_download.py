#!/usr/bin/python3

import json
import getpass
import os
import argparse

# import requests, installing the module locally if necessary
try:
    import requests
except ModuleNotFoundError:
    print('Installing the \'requests\' library...')
    import sys
    # in a virtual environment, --user is neither necessary nor permitted
    venv = False
    if hasattr(sys,'real_prefix'):
        if sys.prefix != sys.real_prefix:
            venv = True
    else:
        if sys.prefix != sys.base_prefix:
            venv = True
    import pip._internal
    pipargs = ['install']
    if not venv:
        pipargs += ['--user']
    pipargs += ['requests']
    if hasattr(pip._internal,'main'):
        pip._internal.main(pipargs)
    else:
        try:
            import pip._internal.main as pipmain
            pipmain.main(pipargs)
        except:
            print('The library could not be installed automatically.')
            print('Please install the \'requests\' library and re-run the ' +
                'tool.')
            exit(1)
    print()
    # in older versions I tried to import the requests library after
    # installing it - this approach worked on Linux, but resulted in a
    # ModuleNotFoundError on Windows. (the program would work on the next run,
    # though.) oddly enough, removing the import fixed the problem: apparently
    # pip loads the module when installing it. I will need to fix the code
    # should this default behaviour ever change.

version = '1.4'

# constructing the argument parser (and the help menu)
parser = argparse.ArgumentParser(
    description='Downloads videos from an OpenCast sever.',
    prog='OpenCast Downloader',add_help=False)
parser.add_argument('-h','--help',action='help',
    help='Display this help message and exit.')
parser.add_argument('-v','--version',action='version',
    version='%(prog)s '+version,
    help='Display version info and exit.')
parser.add_argument('-U','--url',action='store',
    help='URL of the OpenCast server.')
parser.add_argument('-u','--username',action='store',
    help='Username for the OpenCast server.')
parser.add_argument('-p','--password',action='store',
    help='Password for the OpenCast server.')
parser.add_argument('-o','--output-directory',action='store',
    help='Download directory for videos.')
parser.add_argument('-r','--resolution',action='store',
    help='Resolution string to match. ' +
        '(The value "max" automatically selects the maximum resolution.)')
parser.add_argument('-s','--series',action='store',
    help='String to match for series titles.')
parser.add_argument('-ls','--list-series',action='store_true',
    help='List available series and exit.')
parser.add_argument('-le','--list-episodes',action='store_true',
    help='List available episodes. (Can be used with --series.)')
parser.add_argument('-e','--episodes',action='store',
    help='String to match for episode titles, use "all" to download all.')
parser.add_argument('-pr','--presenter',action='store_true',
    help='Download presenter videos.')
parser.add_argument('-pn','--presentation',action='store_true',
    help='Download presentation videos.')
args = vars(parser.parse_args())

# if a directory is specified with -d, check for validity
dir_str = args.get('output_directory',None)
if dir_str:
    dir_str = os.path.expanduser(dir_str) # rewrite ~/dir to /home/username/dir
    if not os.path.isdir(dir_str if dir_str != '' else '.'):
        print('The specified output directory is invalid.')
        exit(1)

# ask for URL if -U is not specified
url = args.get('url',None)
if not url:
    print('Please input the URL of your university\'s OpenCast server.\n')
    url = input('URL: ')

# results in a valid URL even if the user specifies a subpage instead of the
# root and / or omits the protocol
t = url.split('//')
oc_base = 'https://'+t[1 if len(t)>1 else 0].split('/')[0]

# check if the specified URL can be reached at all
try:
    rq = requests.get(oc_base)
except Exception as e:
    if hasattr(e,'__doc__'):
        print('An error has occured:')
        print(e.__doc__)
    else:
        print('An unknown error has occured.')
        print('('+str(type(e))+')')
    exit(1)
if rq.status_code != 200:
    print('Error: the HTTP request returned status code ' +
        str(rq.status_code)+'.')

# ask for username / password if -u / -p are not specified
un = args.get('username',None)
if not un:
    un = input('Username: ')
pw = args.get('password',None)
if not pw:
    pw = getpass.getpass('Password (will not be echoed): ')

# log into OpenCast via a POST request - if we do not log in, the GET request
# to episodes.json will only return the videos that are visible to the public
login_payload={'j_username':un,'j_password':pw,
    '_spring_security_remember_me':True}
try:
    ses = requests.session()
    ses.post(oc_base+'/j_spring_security_check',data=login_payload)
    el = ses.get(oc_base+'/search/episode.json')
except Exception as e:
    print('Something went wrong...')
    print('('+str(type(e))+')')
    exit(1)

# check if the response is valid JSON
try:
    el.json()
except json.decoder.JSONDecodeError:
    print('Error: the file does not seem to be a valid JSON file.')

# helper function for format error messages
def format_error(d,exc=None):
    print('Error: the webserver\'s response does not have the expected format.')
    import tempfile
    out = tempfile.NamedTemporaryFile(mode="w+",delete=False)
    if exc:
        import traceback
        traceback.print_exc(file=out)
        out.write("\n")
    out.write(json.dumps(d))
    print('The output has been saved to '+out.name+'.')
    print('Please file a bug report and include this file.')
    out.close()
    exit(1)

# categorize search results by series
try:
    series = {}
    res = el.json()['search-results']['result']
    for i in range(len(res)):
        d = res[i]
        if type(d) == dict and type(d.get('mediapackage',None)) == dict:
            k = d['mediapackage'].get('series','other')
            if k not in series.keys():
                series[k] = {
                    'title': d['mediapackage'].get('seriestitle',k),
                    'videos': [{
                        'downloader_id': i,
                        'creator': d.get('dcCreator','None'),
                        'title': d['dcTitle']
                    }]
                }
            else:
                series[k]['videos'] += [{
                    'downloader_id': i,
                    'creator': d.get('dcCreator','None'),
                    'title': d['dcTitle']
                }]
except Exception as e:
    format_error(el.json(),exc=e)

sk = list(series.keys())

# list series if -ls is specified
if args.get('list_series',False):
    for t in [series[k]['title'] for k in sk]:
        print(t)
    exit(0)
# if no series are specified, but -e or -le are specified, use all series
if not args.get('series',None):
    if args.get('episodes',None) or args.get('list_episodes',False):
        sc = {'videos':[]}
        for k in sk:
            sc['videos'] += series[k]['videos']
# otherwise, ask user to choose from a list of series
    else:
        fmt = '[%'+str(len(str(len(series))))+'d] %s'
        if len(sk) == 0:
            print('Error: no videos found!')
            exit(1)
        for i in range(len(sk)):
            print(fmt % (i+1,series[sk[i]]['title']))
        while True:
            sn_str = input('\nPlease input the number of the series you want ' +
                'to download videos from, or\ninput "0" to choose videos ' +
                'from all available series: ')
            try:
                sn = int(sn_str)
                if sn not in range(len(sk)+1):
                    raise Exception()
                print('')
                break
            except:
                print('\nPlease enter a valid number between 1 and %d!' % 
                    len(sk))
        if sn == 0:
            sc = {'videos':[]}
            for k in sk:
                sc['videos'] += series[k]['videos']
        else:
            sc = series[sk[sn-1]]
# if series are specified, select all matching series
else:
    sc = {'videos':[]}
    for k in sk:
        if args['series'] in series[k]['title']:
          sc['videos'] += series[k]['videos']
    if len(sc['videos']) == 0:
        print("Could not find a matching series!")
        exit(1)

# helper function for parsing numerical ranges, taken from
# https://stackoverflow.com/a/6405228
def ranges(x):
    result = []
    for part in x.split(','):
        if '-' in part:
            a, b = part.split('-')
            a, b = int(a), int(b)
            result.extend(range(a, b + 1))
        else:
            a = int(part)
            result.append(a)
    return result

# list episodes if -le is specified
if args.get('list_episodes',False):
    for v in sc['videos']:
        print(v['title'])
    exit(0)
# if -e is not specified, ask user to choose from a list of episodes
if not args.get('episodes',None):
    fmt = '[%'+str(len(str(len(sc))))+'d] %s'
    for i in range(len(sc['videos'])):
        print(fmt % (i+1,sc['videos'][i]['title']))
    while True:
        vn = input('\nPlease input the numbers of videos you want to ' +
            'download (e.g. "2,4-7"): ')
        try:
            rg = ranges(vn)
            for i in rg:
                if i not in range(1,len(sc['videos'])+1):
                    pn = i
                    raise Exception()
            print('')
            break
        except:
            print(('\n%d is not a valid choice - please enter numbers ' +
                '/ ranges between 1 and %d!') % (pn,len(sc['videos'])))
# if "-e all" is specified, select all episodes
elif args['episodes'] == 'all':
    rg = list(range(len(sc['videos'])))
# else if -e is specified, select matching episodes
else:
    rg = []
    for i in range(len(sc['videos'])):
        if args['episodes'] in sc['videos'][i]['title']:
            rg += [i+1]
    if len(rg) == 0:
        print("Could not find matching episodes!")
        exit(1)

# filter media packages for HLS playlists and obtain links for each available
# choice of resolution, also keeping track of the maximum resolution available
# for each video; - if -r is not specified, display choice of resolutions for
# each video to user, also keep track of whether any selected episode provides
# both presenter and presentation videos
ex_presenter = False
ex_presentation = False
rs = args.get('resolution',None)
hls_dict = {}
for i in rg:
    vj = res[sc['videos'][i-1]['downloader_id']]['mediapackage']
    if not rs:
        print(vj['title'])
    hls_streams = {}
    for mi in vj['media']['track']:
        if mi['transport'] == 'HLS':
            md = {}
            us = mi['url'].split('/')
            md['hls_base'] = '/'.join(us[:len(us)-1])
            playlist = requests.get(mi['url']).text.split('\n')
            max_res = 0
            rl = []
            for j in range(len(playlist)):
                if 'RESOLUTION' in playlist[j]:
                    reso = playlist[j].split('RESOLUTION=')[1]
                    md[reso] = playlist[j+1]
                    rl += [reso]
                    height = int(reso.split('x')[1])
                    if height > max_res:
                        max_res = height
                        md['max'] = md[reso]
            md['resolutions'] = rl
            hls_streams[mi['type']] = md
            hls_dict[i] = hls_streams
    if 'presenter/delivery' in hls_streams.keys():
        if not rs:
            print('    Available resolutions for presenter video: ' +
                ', '.join(hls_streams['presenter/delivery']['resolutions']))
        ex_presenter = True
    if 'presentation/delivery' in hls_streams.keys():
        if not rs:
            print('    Available resolutions for presentation video: ' +
                ', '.join(hls_streams['presentation/delivery']['resolutions']))
        ex_presentation = True

# if any episode provides both presenter and presentation videos and no command
# line options -pr or -pn are given, ask user to choose; caution: this choice
# applies to all episodes, no matter if all episodes provide both types of video
if ex_presenter and ex_presentation:
    if args.get('presenter',False) or args.get('presentation',False):
       dl_presenter = args.get('presenter',False)
       dl_presentation = args.get('presentation',False)
    else:
        print('\nDownload [1] presenter videos, [2] presentation videos or ' +
            '[3] both?')
        while True:
            ch_str = input('\nPlease input 1, 2 or 3: ')
            try:
                ch = int(ch_str)
                if ch not in [1,2,3]:
                    raise Exception()
                print('')
                break
            except:
                print('\nPlease enter a valid number between 1 and 3!')
        dl_presenter = ch%2 == 1
        dl_presentation = ch//2 == 1

# if -r is not specified, ask user to choose the resolution
if not rs:
    print('Please enter the resolution to download for each video.')
    print('Note: this will only download videos available in the specified ' +
        'resolution.')
    print('To download the highest resolution for each video, enter "max".\n')
    rs = input('Download resolution: ')

# if -d is not specified, ask user where to save the video files
if not dir_str:
    print('\nPlease specify where to save the downloaded files.')
    while True:
        dir_str = input('\nInput a valid directory or leave blank to save to ' +
            'the working directory: ')
        dir_str = os.path.expanduser(dir_str) # ~/dir -> /home/username/dir
        try:
            if not os.path.isdir(dir_str if dir_str != '' else '.'):
                raise Exception()
            break
        except:
            pass

# helper function for generating valid file names, taken from
# https://github.com/django/django/blob/master/django/utils/text.py
def get_valid_filename(s):
    import re
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)

# helper function for downloading either type of video; explanation: for a given
# resolution, the file name in the HLS playlist leads to a list of MPEG-TS chunk
# file names - those are downloaded and concatenated into one MPEG-TS file
def download(i,is_presenter,dl_presenter,dl_presentation,reso):
    vj = res[sc['videos'][i-1]['downloader_id']]['mediapackage']
    pstr = 'presenter' if is_presenter else 'presentation'
    vh = hls_dict[i].get(pstr+'/delivery',None)
    if not vh:
        return
    cl_file = vh.get(reso,None)
    if not cl_file:
        return
    cl_url = vh['hls_base']+'/'+cl_file
    dlstr = '\nDownloading "%s"' % vj['title']
    fname = os.path.join(dir_str,get_valid_filename(vj['title']))
    if dl_presenter and dl_presentation:
        if 'presenter/delivery' in hls_dict[i].keys() and \
            'presentation/delivery' in hls_dict[i].keys():
            dlstr += ' ('+pstr+')'
            fname += '_'+pstr
    print(dlstr)
    fname += '.ts'
    cl = [l for l in requests.get(cl_url).text.split('\n') if l.endswith('.ts')]
    dlfile = open(fname,'wb')
    # progress bar (this does not monitor network activity, but rather the ratio
    # of the count of downloaded chunks and the length of the chunk list)
    width = 80
    fmt = '\r[%-'+str(width-7)+'s] %3d%%'
    for i in range(len(cl)):
        dlfile.write(requests.get(vh['hls_base']+'/'+cl[i],stream=True
            ).raw.read())
        print(fmt % ((((width-7)*(i+1))//len(cl))*'=',(100*(i+1))//len(cl)), \
            end='')
    dlfile.close()
    print()

# download the videos as specified
if not ex_presentation:
    dl_presenter,dl_presentation = True,False
if not ex_presenter:
    dl_presenter,dl_presentation = False,True
for i in rg:
    if dl_presenter:
        download(i,True,dl_presenter,dl_presentation,rs)
    if dl_presentation:
        download(i,False,dl_presenter,dl_presentation,rs)
