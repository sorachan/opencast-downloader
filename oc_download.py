#!/usr/bin/python3

import requests
import json
import getpass
import os
import argparse

version = '1.0'

parser = argparse.ArgumentParser(description='Downloads videos from an OpenCast sever.',prog='OpenCast Downloader',add_help=False)
parser.add_argument('-h','--help',action='help',help='Display this help message and exit.')
parser.add_argument('-v','--version',action='version',version='%(prog)s '+version,help='Display version info and exit.')
parser.add_argument('-U','--url',action='store',help='URL of the OpenCast server.')
parser.add_argument('-u','--username',action='store',help='Username for the OpenCast server.')
parser.add_argument('-p','--password',action='store',help='Password for the OpenCast server.')
parser.add_argument('-o','--output-directory',action='store',help='Download directory for videos.')
parser.add_argument('-r','--resolution',action='store',help='Resolution string to match. (The value "max" automatically selects the maximum resolution.)')
parser.add_argument('-s','--series',action='store',help='String to match for series titles.')
parser.add_argument('-ls','--list-series',action='store_true',help='List available series and exit.')
parser.add_argument('-le','--list-episodes',action='store_true',help='List available episodes. (Can be used with --series.)')
parser.add_argument('-e','--episodes',action='store',help='String to match for episode titles, use "*" to download all.')
parser.add_argument('-pr','--presenter',action='store_true',help='Download presenter videos.')
parser.add_argument('-pn','--presentation',action='store_true',help='Download presentation videos.')
args = vars(parser.parse_args())

dir_str = args.get('output_directory',None)
if dir_str:
    dir_str = os.path.expanduser(dir_str) # needed so ~/dir can be written for /home/username/dir
    if not os.path.isdir(dir_str if dir_str != '' else '.'):
        print("The specified output directory is invalid.")
        exit(1)

url = args.get('url',None)
if not url:
    print('Please input the URL of your university\'s OpenCast server.\n')

    url = input('URL: ')

t = url.split('//')
oc_base = 'https://'+t[1 if len(t)>1 else 0].split('/')[0]

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
    print('Error: the HTTP request returned status code '+str(r.status_code)+'.')

un = args.get('username',None)
if not un:
    un = input('Username: ')
pw = args.get('password',None)
if not pw:
    pw = getpass.getpass('Password (will not be echoed): ')

login_payload={'j_username':un,'j_password':pw,'_spring_security_remember_me':True}

try:
    ses = requests.session()
    ses.post(oc_base+'/j_spring_security_check',data=login_payload)
    el = ses.get(oc_base+'/search/episode.json')
except Exception as e:
    print('Something went wrong...')
    print('('+str(type(e))+')')
    exit(1)

try:
    el.json()
except json.decoder.JSONDecodeError:
    print('Error: the file does not seem to be a valid JSON file.')

def format_error(d):
    print('Error: the webserver\'s response does not have the expected format.')
    import tempfile
    out = tempfile.NamedTemporaryFile(delete=False)
    out.write(json.dumps(d))
    print('The output has been saved to '+out.name+'.')
    print('Please file a bug report and include this file.')
    out.close()

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
                        'creator': d['dcCreator'],
                        'title': d['dcTitle']
                    }]
                }
            else:
                series[k]['videos'] += [{
                    'downloader_id': i,
                    'creator': d['dcCreator'],
                    'title': d['dcTitle']
                }]
except:
    format_error(el.json())

def dig(n):
    d = 0
    t = n
    while t>0:
        d += 1
        t = t//10
    return d

sk = list(series.keys())
if args.get('list_series',False):
    for t in [series[k]['title'] for k in sk]:
        print(t)
    exit(0)
if args.get('list_episodes',False) and not args.get('series',None):
    for d in res:
        print(d['mediapackage']['title'])
    exit(0)
if not args.get('series',None):
    fmt = '[%'+str(dig(len(series)))+'d] %s'
    if len(sk) == 0:
        print('Error: no videos found!')
        exit(1)
    for i in range(len(sk)):
        print(fmt % (i+1,series[sk[i]]['title']))
    while True:
        sn_str = input('\nPlease input the number of the series you want to download videos from: ')
        try:
            sn = int(sn_str)
            if sn not in range(1,len(sk)+1):
                raise Exception()
            print('')
            break
        except:
            print('\nPlease enter a valid number between 1 and %d!' % len(sk))
    sc = series[sk[sn-1]]
else:
    sc = None
    for k in sk:
        if args['series'] in series[k]['title']:
            sc = series[k]
            break
    if not sc:
        print("Could not find a matching series!")
        exit(1)

fmt = '[%'+str(dig(len(sc)))+'d] %s'

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

if args.get('list_episodes',False):
    for v in sc['videos']:
        print(v['title'])
    exit(0)
if not args.get('episodes',None):
    for i in range(len(sc['videos'])):
        print(fmt % (i+1,sc['videos'][i]['title']))
    while True:
        vn = input('\nPlease input the numbers of videos you want to download (e.g. "2,4-7"): ')
        try:
            rg = ranges(vn)
            for i in rg:
                if i not in range(1,len(sc['videos'])+1):
                    pn = i
                    raise Exception()
            print('')
            break
        except:
            print('\n%d is not a valid choice - please enter numbers / ranges between 1 and %d!' % (pn,len(sc['videos'])))    
else:
    rg = []
    for i in range(len(sc['videos'])):
        if args['episodes'] in sc['videos'][i]['title']:
            rg += [i+1]
    if len(rg) == 0:
        print("Could not find matching episodes!")
        exit(1)

ex_presenter = False
ex_presentation = False

hls_dict = {}

rs = args.get('resolution',None)

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
            print('    Available resolutions for presenter video: '+', '.join(hls_streams['presenter/delivery']['resolutions']))
        ex_presenter = True
    if 'presentation/delivery' in hls_streams.keys():
        if not rs:
            print('    Available resolutions for presentation video: '+', '.join(hls_streams['presentation/delivery']['resolutions']))
        ex_presentation = True
        
if ex_presenter and ex_presentation:
    if args.get('presenter',False) or args.get('presentation',False):
       dl_presenter = args.get('presenter',False)
       dl_presentation = args.get('presentation',False)
    else:
        print('\nDownload [1] presenter videos, [2] presentation videos or [3] both?')
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

if not rs:
    print('Please enter the resolution to download for each video.')
    print('Note: this will only download videos available in the specified resolution.')
    print('To download the highest resolution for each video, enter "max".\n')
    rs = input('Download resolution: ')

if not dir_str:
    print('\nPlease specify where to save the downloaded files.')
    while True:
        dir_str = input('\nInput a valid directory or leave blank to save to the working directory: ')
        dir_str = os.path.expanduser(dir_str) # needed so ~/dir can be written for /home/username/dir
        try:
            if not os.path.isdir(dir_str if dir_str != '' else '.'):
                raise Exception()
            break
        except:
            pass

# https://github.com/django/django/blob/master/django/utils/text.py
def get_valid_filename(s):
    import re
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)

def download(i,is_presenter,dl_presenter,dl_presentation,reso):
    vj = res[sc['videos'][i-1]['downloader_id']]['mediapackage']
    pstr = 'presenter' if is_presenter else 'presentation'
    vh = hls_dict[i][pstr+'/delivery']
    cl_file = vh.get(reso,None)
    if not cl_file:
        return
    cl_url = vh['hls_base']+'/'+cl_file
    dlstr = '\nDownloading "%s"' % vj['title']
    fname = os.path.join(dir_str,get_valid_filename(vj['title']))
    if dl_presenter and dl_presentation:
        if 'presenter/delivery' in hls_dict[i].keys() and 'presentation/delivery' in hls_dict[i].keys():
            dlstr += ' ('+pstr+')'
            fname += '_'+pstr
    print(dlstr)
    fname += '.ts'
    cl = [l for l in requests.get(cl_url).text.split('\n') if l.endswith('.ts')]
    dlfile = open(fname,'wb')
    width = 80
    fmt = '\r[%-'+str(width-7)+'s] %3d%%'
    for i in range(len(cl)):
        dlfile.write(requests.get(vh['hls_base']+'/'+cl[i],stream=True).raw.read())
        print(fmt % ((((width-7)*(i+1))//len(cl))*'=',(100*(i+1))//len(cl)),end='')
    dlfile.close()
    print()

for i in rg:
    if dl_presenter:
        download(i,True,dl_presenter,dl_presentation,rs)
    if dl_presentation:
        download(i,False,dl_presenter,dl_presentation,rs)
