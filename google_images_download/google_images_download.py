#!/usr/bin/env python
# vim: sw=4:ts=4:sts=4

import argparse
import codecs
import datetime
import json
import os
import ssl
import sys
import time

import urllib.request
from urllib.request import Request, urlopen
from urllib.request import URLError, HTTPError
from urllib.parse import quote

import http.client
from http.client import IncompleteRead, BadStatusLine
http.client._MAXHEADERS = 1000


USER_AGENT = ('Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36')
EXTENSIONS = ('jpg', 'gif', 'png', 'bmp', 'svg', 'webp', 'ico')

SILENT_MODE = False


def sprint(*args, **kwargs):
    if not SILENT_MODE:
        print(*args, **kwargs)


class ArgumentParser(argparse.ArgumentParser):

    def error(self, message):
        raise Exception(message)


def get_parser():
    """Parse command-line inputs"""

    parser = ArgumentParser(exit_on_error=False)

    parser.add_argument('--suffix_keywords', default='',
                        help='comma separated additional words added after '
                        'the main keyword')

    parser.add_argument('--prefix_keywords', default='',
                        help='comma separated additional words added before '
                        'main keyword')

    parser.add_argument('--limit', type=int, defaut=100)

    parser.add_argument('--single_image', type=str,
                        help='downloading a single image from URL')

    parser.add_argument('--output_directory', type=str,
                        help='download images in a specific main directory')

    parser.add_argument('--delay', type=int,
                        help='delay in seconds to wait between downloading '
                        'two images')

    parser.add_argument('--color', type=str,
                        help='filter on color',
                        choices=['red', 'orange', 'yellow', 'green', 'teal',
                                 'blue', 'purple', 'pink', 'white', 'gray',
                                 'black', 'brown'])

    parser.add_argument('--color_type', type=str,
                        help='filter on color',
                        choices=['full-color', 'black-and-white',
                                 'transparent'])

    parser.add_argument('--usage_rights', type=str,
                        help='usage rights',
                        choices=[
                            'labeled-for-reuse-with-modifications',
                            'labeled-for-reuse',
                            'labeled-for-noncommercial-reuse-with-'
                            'modification',
                            'labeled-for-nocommercial-reuse'])

    parser.add_argument('--type', type=str,
                        help='image type',
                        choices=['face', 'photo', 'clipart', 'line-drawing',
                                 'animated'])

    parser.add_argument('--aspect_ratio', type=str,
                        help='comma separated additional words added to '
                        'keywords',
                        choices=['tall', 'square', 'wide', 'panoramic'])

    parser.add_argument('--similar_images', type=str,
                        help='downloads images very similar to the image URL '
                        'you provide')

    parser.add_argument('--specific_site', type=str,
                        help='downloads images that are indexed from a '
                        'specific website')

    parser.add_argument('--print_urls', action='store_true',
                        help='Print the URLs of the images')

    parser.add_argument('--print_size', action='store_true',
                        help='Print the size of the images on disk')

    parser.add_argument('--print_paths', action='store_true',
                        help='Prints the list of absolute paths of the images')

    parser.add_argument('--metadata', action='store_true',
                        help='Print the metadata of the image')

    parser.add_argument('--extract_metadata', action='store_true',
                        help='Dumps all the logs into a text file')

    parser.add_argument('--socket_timeout', type=float,
                        help='Connection timeout waiting for the image to '
                        'download')

    parser.add_argument('--thumbnail', action='store_true',
                        help='Downloads image thumbnail along with the actual '
                        'image')

    parser.add_argument('--thumbnail_only', action='store_true',
                        help='Downloads only thumbnail without downloading '
                        'actual images')

    parser.add_argument('--language', type=str,
                        help='Defines the language filter. The search results '
                        'are authomatically returned in that language',
                        choices=['Arabic', 'Chinese', 'Czech', 'Danish',
                                 'Dutch', 'English', 'Estonian', 'Finnish',
                                 'French', 'German', 'Greek', 'Hebrew',
                                 'Hungarian', 'Icelandic', 'Italian',
                                 'Japanese', 'Korean', 'Latvian',
                                 'Lithuanian', 'Norwegian', 'Portuguese',
                                 'Polish', 'Romanian', 'Russian', 'Spanish',
                                 'Swedish', 'Turkish'])

    parser.add_argument('--prefix', type=str,
                        help='A word that you would want to prefix in front '
                        'of each image name')

    parser.add_argument('--proxy', type=str,
                        help='specify a proxy address and port')

    parser.add_argument('--chromedriver', type=str,
                        help='specify the path to chromedriver executable in '
                        'your local machine')

    parser.add_argument('--related_images', action='store_true',
                        help='Downloads images that are similar to the '
                        'keyword provided')

    parser.add_argument('--safe_search', action='store_true',
                        help='Turns on the safe search filter while searching '
                        'for images')

    parser.add_argument('--no_numbering', action='store_true',
                        help='Allows you to exclude the default numbering of '
                        'images')

    parser.add_argument('--offset', type=int,
                        help='Where to start in the fetched links')

    parser.add_argument('--no_download', action='store_true',
                        help='Prints the URLs of the images and/or thumbnails '
                        'without downloading them')

    parser.add_argument('--ignore_urls', type=tuple,
                        help='delimited list input of image urls/keywords to '
                        'ignore')

    parser.add_argument('--silent_mode', action='store_true',
                        help='Remains silent. Does not print notification '
                        'messages on the terminal')

    parser.add_argument('--save_source', action='store_true',
                        help='creates a text file containing a list of '
                        'downloaded images along with source page url')

    required = parser.add_mutually_exclusive_group(required=True)
    required.add_argument('--keywords', type=str,
                          help='delimited list input')

    required.add_argument('--keywords_from_file', type=str,
                          help='extract list of keywords from a text file')

    required.add_argument('--format', type=str,
                          help='download images with specific format',
                          choices=EXTENSIONS)

    required.add_argument('--url', type=str, help='search with google image URL')
    required.add_argument('--config_file', type=str,
                          help='config file name')

    timegroup = parser.add_mutually_exclusive_group()
    timegroup.add_argument('--time', type=str,
                           help='image age',
                           choices=['past-24-hours', 'past-7-days',
                                    'past-month', 'past-year'])

    timegroup.add_argument('--time_range', type=str,
                           help='time range for the age of the image. should be '
                           'in the format '
                           '{"time_min":"MM/DD/YYYY","time_max":"MM/DD/YYYY"}')

    sizegroup = parser.add_mutually_exclusive_group()
    sizegroup.add_argument('--size',  type=str,
                           help='image size',
                           choices=['large', 'medium', 'icon', '>400*300',
                                    '>640*480', '>800*600', '>1024*768', '>2MP',
                                    '>4MP', '>6MP', '>8MP', '>10MP', '>12MP',
                                    '>15MP', '>20MP', '>40MP', '>70MP'])

    sizegroup.add_argument('--exact_size', type=str,
                           help='exact image resolution "WIDTH,HEIGHT"')

    dirgroup = parser.add_mutually_exclusive_group()
    dirgroup.add_argument('--image_directory', type=str,
                          help='download images in a specific sub-directory')

    dirgroup.add_argument('--no_directory', action='store_true',
                          help='download images in the main directory but no '
                          'sub-directory')

    return parser


def user_input():
    def add_search(new):
        if new.keywords:
            search_keyword = new.keywords.split(',')

        if new.keywords_from_file:
            search_keyword = 'keywords_from_file(new.keywords_from_file)'  # TODO

        if new.url or new.similar_images:
            current_time = str(datetime.datetime.now()).split('.')[0]
            search_keyword = [current_time.replace(":", "_")]

        new.search_keyword = search_keyword
        return new

    parser = get_parser()
    args = parser.parse_args()

    if not args.config_file:
        return [add_search(args)]

    records = []
    with open(args.config_file) as fh:
        json_file = json.load(fh)

    for i, record in enumerate(json_file['Records']):
        parser = get_parser()
        args = [f'--{k}={v}' for k, v in record.items()]
        try:
            new = parser.parse_args(args)
        except Exception as e:
            print('Config %d invalid: %s' % (i, e))
            exit()

        records.append(add_search(new))

    return records


class GoogleImagesDownloader:
    def download_page(self, url):
        """Downloading entire Web Document (Raw Page Content)"""
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        resp = urlopen(req)

        return str(resp.read())

    def get_next_tab(self, raw_page):
        """Finding 'Next Image' from the given raw page"""
        start_line = start_line_2 = raw_page.find('class="dtviD"')
        if start_line == -1:
            return 'no_tabs', '', 0

        start_content = raw_page.find('href="', start_line + 1)
        end_content = raw_page.find('">', start_content + 1)
        url_item = 'https://www.google.com'
        url_item = url_item + raw_page[start_content + 6:end_content]
        url_item = url_item.replace('&amp;', '&')

        raw_page = raw_page.replace('&amp;', '&')
        start_content_2 = raw_page.find(':', start_line_2 + 1)
        end_content_2 = raw_page.find('&usg=', start_content_2 + 1)
        url_item_name = raw_page[start_content_2 + 1:end_content_2]

        chars = url_item_name.find(',g_1:')
        chars_end = url_item_name.find(':', chars + 6)
        if chars_end == -1:
            updated_item_name = url_item_name[chars + 5:].replace('+', ' ')
        else:
            updated_item_name = url_item_name[chars + 5:chars_end]
            updated_item_name = updated_item_name.replace('+', ' ')

        return url_item, updated_item_name, end_content

    def get_all_tabs(self, page):
        """Getting all links with the help of 'get_next_tab'"""
        tabs = {}
        while True:
            item, item_name, end_content = self.get_next_tab(page)
            if item == 'no_tabs':
                break
            else:
                if len(item_name) > 100 or item_name == 'background-color':
                    break
                else:
                    # Append all the links in the list named 'Links'
                    tabs[item_name] = item
                    # TODO: Timer could be used to slow down the request for
                    # image downloads
                    time.sleep(0.1)
                    page = page[end_content:]

        return tabs

    def format_object(self, obj):
        """Format the object in readable format"""
        return {
                'image_description': obj['pt'],
                'image_format': obj['ity'],
                'image_height': obj['oh'],
                'image_host': obj['rh'],
                'image_link': obj['ou'],
                'image_source': obj['ru'],
                'image_thumbnail_url': obj['tu'],
                'image_width': obj['ow']
        }

    def single_image(self, image_url):
        """function to download single image"""
        main_directory = 'downloads'
        url = image_url
        try:
            os.makedirs(main_directory)
        except OSError as e:
            if e.errno != 17:
                raise
            pass
        req = Request(url, headers={'User-Agent': USER_AGENT})

        response = urlopen(req, None, 10)
        data = response.read()
        response.close()

        image_name = str(url[(url.rfind('/')) + 1:])
        if '?' in image_name:
            image_name = image_name[:image_name.find('?')]
        if image_name[-3:] in EXTENSIONS:
            file_name = main_directory + '/' + image_name
        else:
            file_name = main_directory + '/' + image_name + '.jpg'
            image_name = image_name + '.jpg'

        try:
            output_file = open(file_name, 'wb')
            output_file.write(data)
            output_file.close()
        except IOError as e:
            raise e
        except OSError as e:
            raise e
        print('completed ====>',
              image_name.encode('raw_unicode_escape').decode('utf-8'))

    def similar_images(self, similar_images):
        try:
            searchUrl = ''.join(('https://www.google.com/searchbyimage',
                                 '?site=search&sa=X&image_url=',
                                 similar_images))
            headers = {}
            headers['User-Agent'] = USER_AGENT

            req1 = urllib.request.Request(searchUrl, headers=headers)
            resp1 = urlopen(req1)
            content = str(resp1.read())
            l1 = content.find('AMhZZ')
            l2 = content.find('&', l1)
            urll = content[l1:l2]

            newurl = ''.join(('https://www.google.com/search?tbs=sbi:',
                              urll, '&site=search&sa=X'))
            req2 = urllib.request.Request(newurl, headers=headers)
            resp2 = urlopen(req2)
            content = str(resp2.read())
            l3 = content.find('/search?sa=X&amp;q=')
            l4 = content.find(';', l3 + 19)
            urll2 = content[l3 + 19:l4]

            return urll2

        except Exception as e:
            print('--- exception', e)

            return 'Cloud not connect to Google Images endpoint'

    def build_url_parameters(self, arguments):
        """Building URL parameters"""
        if arguments['language']:
            lang = '&lr='
            lang_param = {'Arabic': 'lang_ar',
                          'Chinese (Simplified)': 'lang_zh-CN',
                          'Chinese (Traditional)': 'lang_zh-TW',
                          'Czech': 'lang_cs',
                          'Danish': 'lang_da',
                          'Dutch': 'lang_nl',
                          'English': 'lang_en',
                          'Estonian': 'lang_et',
                          'Finnish': 'lang_fi',
                          'French': 'lang_fr',
                          'German': 'lang_de',
                          'Greek': 'lang_el',
                          'Hebrew': 'lang_iw ',
                          'Hungarian': 'lang_hu',
                          'Icelandic': 'lang_is',
                          'Italian': 'lang_it',
                          'Japanese': 'lang_ja',
                          'Korean': 'lang_ko',
                          'Latvian': 'lang_lv',
                          'Lithuanian': 'lang_lt',
                          'Norwegian': 'lang_no',
                          'Portuguese': 'lang_pt',
                          'Polish': 'lang_pl',
                          'Romanian': 'lang_ro',
                          'Russian': 'lang_ru',
                          'Spanish': 'lang_es',
                          'Swedish': 'lang_sv',
                          'Turkish': 'lang_tr'}
            lang_url = lang+lang_param[arguments['language']]
        else:
            lang_url = ''

        if arguments['time_range']:
            json_acceptable_string = arguments['time_range'].replace('\'', '"')
            d = json.loads(json_acceptable_string)
            time_range = ''.join((',cdr:1,cd_min:', d['time_min'], ',cd_max:',
                                 d['time_max']))
        else:
            time_range = ''

        if arguments['exact_size']:
            exact_size = arguments['exact_size'].split(',')
            size_array = [x.strip() for x in exact_size]
            exact_size = ',isz:ex,iszw:' + str(size_array[0]) + ',iszh:'
            exact_size = exact_size + str(size_array[1])
        else:
            exact_size = ''

        built_url = '&tbs='
        counter = 0
        params = {
                'color': [
                    arguments['color'],
                    {
                        'red': 'ic: specific,isc: red',
                        'orange': 'ic: specific,isc: orange',
                        'yellow': 'ic: specific,isc: yellow',
                        'green': 'ic: specific,isc: green',
                        'teal': 'ic: specific,isc: teel',
                        'blue': 'ic: specific,isc: blue',
                        'purple': 'ic: specific,isc: purple',
                        'pink': 'ic: specific,isc: pink',
                        'white': 'ic: specific,isc: white',
                        'gray': 'ic: specific,isc: gray',
                        'black': 'ic: specific,isc: black',
                        'brown': 'ic: specific,isc: brown'
                    }
                ],
                'color_type': [
                    arguments['color_type'],
                    {
                        'full-color': 'ic:color',
                        'black-and-white': 'ic:gray',
                        'transparent': 'ic:trans'
                    }
                ],
                'usage_rights': [
                    arguments['usage_rights'],
                    {
                        'labeled-for-reuse-with-modifications': 'sur:fmc',
                        'labeled-for-reuse': 'sur:fc',
                        'labeled-for-noncommercial-reuse-with-modification':
                        'sur:fm',
                        'labeled-for-nocommercial-reuse': 'sur:f'
                    }
                ],
                'size': [
                    arguments['size'],
                    {
                        'large': 'isz:l',
                        'medium': 'isz:m',
                        'icon': 'isz:i',
                        '>400*300': 'isz:lt,islt:qsvga',
                        '>640*480': 'isz:lt,islt:vga',
                        '>800*600': 'isz:lt,islt:svga',
                        '>1024*768': 'visz:lt,islt:xga',
                        '>2MP': 'isz:lt,islt:2mp',
                        '>4MP': 'isz:lt,islt:4mp',
                        '>6MP': 'isz:lt,islt:6mp',
                        '>8MP': 'isz:lt,islt:8mp',
                        '>10MP': 'isz:lt,islt:10mp',
                        '>12MP': 'isz:lt,islt:12mp',
                        '>15MP': 'isz:lt,islt:15mp',
                        '>20MP': 'isz:lt,islt:20mp',
                        '>40MP': 'isz:lt,islt:40mp',
                        '>70MP': 'isz:lt,islt:70mp'
                    }
                ],
                'type': [
                        arguments['type'],
                        {
                            'face': 'itp:face',
                            'photo': 'itp:photo',
                            'clipart': 'itp:clipart',
                            'line-drawing': 'itp:lineart',
                            'animated': 'itp:animated'
                        }
                ],
                'time': [
                        arguments['time'],
                        {
                            'past-24-hours': 'qdr:d',
                            'past-7-days': 'qdr:w',
                            'past-month': 'qdr:m',
                            'past-year': 'qdr:y'
                        }
                ],
                'aspect_ratio': [
                        arguments['aspect_ratio'],
                        {
                            'tall': 'iar:t',
                            'square': 'iar:s',
                            'wide': 'iar:w',
                            'panoramic': 'iar:xw'
                        }
                ],
                'format': [
                        arguments['format'],
                        {
                            'jpg': 'ift:jpg',
                            'gif': 'ift:gif',
                            'png': 'ift:png',
                            'bmp': 'ift:bmp',
                            'svg': 'ift:svg',
                            'webp': 'webp',
                            'ico': 'ift:ico',
                            'raw': 'ift:craw'
                        }
                ]
        }
        for key, value in params.items():
            if value[0]:
                # TODO: nonsense
                ext_param = value[1][value[0]]
                # counter will tell if it is first param added or not
                if counter == 0:
                    # add it to the built url
                    built_url = built_url + ext_param
                    counter += 1
                else:
                    built_url = built_url + ',' + ext_param
                    counter += 1
        built_url = lang_url + built_url + exact_size + time_range

        return built_url

    def build_search_url(self, search_term, params, url, similar_images,
                         specific_site, safe_search):
        """building main search URL"""
        # check safe_search
        safe_search_string = '&safe=active'
        # check the args and choose the URL
        if url:
            pass
        elif similar_images:
            print(similar_images)
            url = ''.join(('https://www.google.com/search?q=',
                           self.similar_images(similar_images),
                           '&espv=2&biw=1366&bih=667&site=webhp&source=lnms&',
                           'tbm=isch',
                           '&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'))
        elif specific_site:
            url = ''.join(('https://www.google.com/search?q=',
                           quote(search_term.encode('utf-8')),
                           '&as_sitesearch=',
                           specific_site,
                           '&espv=2&biw=1366&bih=667&site=webhp&source=lnms&',
                           'tbm=isch',
                           params,
                           '&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'))
        else:
            url = ''.join(('https://www.google.com/search?q=',
                           quote(search_term.encode('utf-8')),
                           '&espv=2&biw=1366&bih=667&site=webhp&source=lnms&',
                           'tbm=isch',
                           params,
                           '&sa=X&ei=XosDVaCXD8TasATItgE&ved=0CAcQ_AUoAg'))

        # safe search check
        if safe_search:
            url = url + safe_search_string

        return url

    def file_size(self, file_path):
        """measures the file size"""
        if os.path.isfile(file_path):
            file_info = os.stat(file_path)
            size = file_info.st_size
            for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024.0:
                    return '%3.1f %s' % (size, x)
                size /= 1024.0

            return size

    def keywords_from_file(self, file_name):
        """keywords from file"""
        search_keyword = []
        with codecs.open(file_name, 'r', encoding='utf-8-sig') as f:
            if '.csv' in file_name or '.txt' in file_name:
                for line in f:
                    if line in ['\n', '\r\n']:
                        pass
                    else:
                        ln = line.replace('\n', '').replace('\r', '')
                        search_keyword.append(ln)
            else:
                print('Invalid file type: Valid file types are either .txt '
                      'or .csv \nexiting...')
                sys.exit()

        return search_keyword

    def create_directories(self, main_directory, dir_name, thumbnail,
                           thumbnail_only):
        """make directories"""
        dir_name_thumbnail = dir_name + ' - thumbnail'
        # make a search keyword  directory
        try:
            if not os.path.exists(main_directory):
                os.makedirs(main_directory)
                time.sleep(0.2)
                path = dir_name
                sub_directory = os.path.join(main_directory, path)
                if not os.path.exists(sub_directory):
                    os.makedirs(sub_directory)
                if thumbnail or thumbnail_only:
                    sub_directory_thumbnail = os.path.join(main_directory,
                                                           dir_name_thumbnail)
                    if not os.path.exists(sub_directory_thumbnail):
                        os.makedirs(sub_directory_thumbnail)
            else:
                path = dir_name
                sub_directory = os.path.join(main_directory, path)
                if not os.path.exists(sub_directory):
                    os.makedirs(sub_directory)
                if thumbnail or thumbnail_only:
                    sub_directory_thumbnail = os.path.join(main_directory,
                                                           dir_name_thumbnail)
                    if not os.path.exists(sub_directory_thumbnail):
                        os.makedirs(sub_directory_thumbnail)
        except OSError as e:
            if e.errno != 17:
                raise
            pass

        return

    def download_image_thumbnail(self, image_url, main_directory, dir_name,
                                 return_image_name, print_urls, socket_timeout,
                                 print_size, no_download, save_source, img_src,
                                 ignore_urls):
        """Download Image thumbnails"""
        if print_urls or no_download:
            print('Image URL: ' + image_url)
        if no_download:
            return 'success', 'Printed url without downloading'

        download_message = '{} on an image...trying next one... Error: {}'

        try:
            req = Request(image_url, headers={'User-Agent': USER_AGENT})

            # TODO: more insanity
            try:
                # timeout time to download an image
                if socket_timeout:
                    timeout = float(socket_timeout)
                else:
                    timeout = 10

                response = urlopen(req, None, timeout)
                data = response.read()
                response.close()

                path = ''.join((main_directory, '/', dir_name, ' - thumbnail/',
                                return_image_name))

                try:
                    output_file = open(path, 'wb')
                    output_file.write(data)
                    output_file.close()
                    if save_source:
                        list_path = ''.join((main_directory, '/', save_source,
                                             '.txt'))
                        list_file = open(list_path, 'a')
                        list_file.write(path + '\t' + img_src + '\n')
                        list_file.close()
                except OSError as e:
                    download_status = 'fail'
                    download_message = download_message.format('OSError', e)
                except IOError as e:
                    download_status = 'fail'
                    download_message = download_message.format('IOError', e)

                download_status = 'success'
                download_message = ''.join(('Completed Image Thumbnail ====> ',
                                            return_image_name))

                # image size parameter
                if print_size:
                    print('Image Size: ' + str(self.file_size(path)))

            except UnicodeEncodeError as e:
                download_status = 'fail'
                download_message = download_message.format(
                    'UnicodeEncodeError', e)

        except HTTPError as e:  # If there is any HTTPError
            download_status = 'fail'
            download_message = download_message.format('HTTPError', e)

        except URLError as e:
            download_status = 'fail'
            download_message = download_message.format('URLError', e)

        except ssl.CertificateError as e:
            download_status = 'fail'
            download_message = download_message.format('CertificateError', e)

        except IOError as e:  # If there is any IOError
            download_status = 'fail'
            download_message = download_message.format('IOError', e)

        return download_status, download_message

    def download_image(self, image_url, image_format, main_directory, dir_name,
                       count, print_urls, socket_timeout, prefix, print_size,
                       no_numbering, no_download, save_source, img_src,
                       silent_mode, thumbnail_only, _format, ignore_urls):
        """Download Images"""
        print('download_image(...)')
        if print_urls or no_download:
            sprint('Image URL: ' + image_url)

        if ignore_urls:
            if any(url in image_url for url in ignore_urls.split(',')):
                msg = 'Image ignored due to \'ignore_url\' parameter'
                return 'fail', msg, None, image_url

        if thumbnail_only:
            part = str(image_url[(image_url.rfind('/')) + 1:])
            return 'success', 'Skipping image download...', part, image_url

        if no_download:
            return ('success', 'Printed url without downloading', None,
                    image_url)

        download_message = '{} on an image...trying next one... Error: {}'
        try:
            req = Request(image_url, headers={'User-Agent': USER_AGENT})

            # TODO: more insanity
            try:
                # timeout time to download an image
                if socket_timeout:
                    timeout = float(socket_timeout)
                else:
                    timeout = 10

                response = urlopen(req, None, timeout)
                data = response.read()
                response.close()

                # keep everything after the last '/'
                image_name = image_url.split('/')[-1]
                if _format and image_format != _format:
                    download_message = ('Wrong image format returned. '
                                        'Skipping...')
                    return 'fail', download_message, '', ''

                extensions = ['jpg', 'jpeg', 'gif', 'png', 'bmp', 'svg',
                              'webp', 'ico']
                if not image_format or '.' + image_format not in extensions:
                    download_message = ('Invalid or missing image format. '
                                        'Skipping...')
                    return 'fail', download_message, '', ''

                elif image_name.lower().find('.' + image_format) < 0:
                    image_name = image_name + '.' + image_format
                else:
                    idx = image_name.lower().find('.' + image_format)
                    idx = idx + len(image_format) + 1
                    image_name = image_name[:idx]

                # prefix name in image
                if prefix:
                    prefix = prefix + ' '
                else:
                    prefix = ''

                if no_numbering:
                    path = '{}/{}/{}'.format(main_directory, dir_name,
                                             prefix + image_name)
                else:
                    path = '{}/{}/{}{}.{}'.format(main_directory, dir_name,
                                                  prefix, str(count),
                                                  image_name)

                try:
                    output_file = open(path, 'wb')
                    output_file.write(data)
                    output_file.close()
                    if save_source:
                        list_path = '{}/{}.txt'.format(main_directory,
                                                       save_source)
                        list_file = open(list_path, 'a')
                        list_file.write(path + '\t' + img_src + '\n')
                        list_file.close()
                    absolute_path = os.path.abspath(path)
                except OSError as e:
                    download_status = 'fail'
                    download_message = download_message.format('OSError', e)
                    return_image_name = ''
                    absolute_path = ''

                # return image name back to calling method to use it for
                # thumbnail downloads
                download_status = 'success'
                download_message = 'Completed Image ====> {}{}.{}'.format(
                    prefix, str(count), image_name)
                return_image_name = prefix + str(count) + '.' + image_name

                # image size parameter
                if print_size:
                    sprint('Image Size: ' + str(self.file_size(path)))

            except UnicodeEncodeError as e:
                download_status = 'fail'
                download_message = download_message.format(
                        'UnicodeEncodeError', e)
                return_image_name = ''
                absolute_path = ''

            except URLError as e:
                download_status = 'fail'
                download_message = download_message.format('URLError', e)
                return_image_name = ''
                absolute_path = ''

            except BadStatusLine as e:
                download_status = 'fail'
                download_message = download_message.format('BadStatusLine', e)
                return_image_name = ''
                absolute_path = ''

        except HTTPError as e:  # If there is any HTTPError
            download_status = 'fail'
            download_message = download_message.format('HTTPError', e)
            return_image_name = ''
            absolute_path = ''

        except URLError as e:
            download_status = 'fail'
            download_message = download_message.format('URLError', e)
            return_image_name = ''
            absolute_path = ''

        except ssl.CertificateError as e:
            download_status = 'fail'
            download_message = download_message.format('CertificateError', e)
            return_image_name = ''
            absolute_path = ''

        except IOError as e:  # If there is any IOError
            download_status = 'fail'
            download_message = download_message.format('IOError', e)
            return_image_name = ''
            absolute_path = ''

        except IncompleteRead as e:
            download_status = 'fail'
            download_message = download_message.format('IncompleteRead', e)
            return_image_name = ''
            absolute_path = ''

        return (download_status, download_message, return_image_name,
                absolute_path)

    def _get_next_item(self, s):
        """Finding 'Next Image' from the given raw page"""
        start_line = s.find('rg_meta notranslate')
        # breakpoint()
        if start_line == -1:  # If no links are found then give an error!
            return 'no_links', 0
        else:
            start_line = s.find('class="rg_meta notranslate">')
            start_object = s.find('{', start_line + 1)
            end_object = s.find('</div>', start_object + 1)
            object_raw = str(s[start_object:end_object])

            # remove escape characters based on python version
            try:
                object_decode = bytes(object_raw, 'utf-8').decode(
                        'unicode_escape')
                final_object = json.loads(object_decode)
            except Exception as e:
                print('--exception--', e)
                final_object = ''

            return final_object, end_object

    def _get_all_items(self, page, main_directory, dir_name, limit, arguments):
        """Getting all links with the help of '_get_next_item'"""
        items = []
        abs_path = []
        errorCount = 0
        i = 0
        count = 1
        while count < limit + 1:
            obj, end_content = self._get_next_item(page)
            if obj == 'no_links':
                print('no links!')
                break
            elif obj == '':
                page = page[end_content:]
            elif arguments['offset'] and count < arguments['offset']:
                count += 1
                page = page[end_content:]
            else:
                # format the item for readability
                obj = self.format_object(obj)
                if arguments['metadata']:
                    sprint('\nImage Metadata: ' + str(obj))

                # download the images
                # TODO: can we pass kwargs
                (download_status, download_message, return_image_name,
                 absolute_path) = self.download_image(
                         obj['image_link'],
                         obj['image_format'],
                         main_directory,
                         dir_name,
                         count,
                         arguments['print_urls'],
                         arguments['socket_timeout'],
                         arguments['prefix'],
                         arguments['print_size'],
                         arguments['no_numbering'],
                         arguments['no_download'],
                         arguments['save_source'],
                         obj['image_source'],
                         arguments['silent_mode'],
                         arguments['thumbnail_only'],
                         arguments['format'],
                         arguments['ignore_urls'])

                sprint(download_message)

                if download_status == 'success':
                    # download image_thumbnails
                    if arguments['thumbnail'] or arguments['thumbnail_only']:
                        res = self.download_image_thumbnail(
                                obj['image_thumbnail_url'],
                                main_directory,
                                dir_name,
                                return_image_name,
                                arguments['print_urls'],
                                arguments['socket_timeout'],
                                arguments['print_size'],
                                arguments['no_download'],
                                arguments['save_source'],
                                obj['image_source'],
                                arguments['ignore_urls'])
                        download_status, download_message_thumbnail = res

                        sprint(download_message_thumbnail)

                    count += 1
                    obj['image_filename'] = return_image_name
                    # Append all the links in the list named 'Links'
                    items.append(obj)
                    abs_path.append(absolute_path)
                else:
                    errorCount += 1

                # delay param
                if arguments['delay']:
                    time.sleep(arguments['delay'])

                page = page[end_content:]

            i += 1

        if count < limit:
            msg = ('\n\nUnfortunately all {} could not be downloaded because '
                   'some images were not downloadable. {} is all we got for '
                   'this search filter!')
            print(msg.format(limit, count-1))

        return items, errorCount, abs_path

    def download(self, arguments):
        paths = {}
        errorCount = None

        total_errors = 0
        for pky in arguments.prefix_keywords.split(','):
            for sky in arguments.suffix_keywords.split(','):
                for i, ky in enumerate(arguments.search_keyword):
                    search_term = ' '.join([pky, ky, sky])
                    sprint(f'\nItem no.: {i+1} --> Item name = {search_term}\n'
                           'Evaluating...')

                    if self.image_directory:
                        dir_name = self.image_directory
                    elif self.no_directory:
                        dir_name = ''
                    else:
                        dir_name = search_term
                        if self.color:
                            # sub-directory
                            dir_name = '{}-{}'.format(dir_name,
                                                      self.color)

                    if not self.no_download:
                        # create directories in OS
                        self.create_directories(arguments.main_directory,
                                                dir_name,
                                                self.thumbnail,
                                                self.thumbnail_only)

                    # building URL with params
                    params = self.build_url_parameters(arguments)

                    # building main search url
                    url = self.build_search_url(search_term, params,
                                                self.url,
                                                self.similar_images,
                                                self.specific_site,
                                                self.safe_search)

                    raw_html = self.download_page(url)  # download page

                    if self.no_download:
                        sprint('Getting URLs without downloading images...')
                    else:
                        sprint('Starting Download...')

                    # get all image items and download images
                    items, errorCount, abs_path = self._get_all_items(
                            raw_html, arguments.main_directory, dir_name,
                            arguments.limit,
                            arguments)
                    paths[search_term] = abs_path

                    # dumps into a json file
                    if self.extract_metadata:
                        try:
                            if not os.path.exists('logs'):
                                os.makedirs('logs')
                        except OSError as e:
                            print(e)
                        json_file = open('logs/{}.json'.format(ky), 'w')
                        json.dump(items, json_file, indent=4, sort_keys=True)
                        json_file.close()

                    # Related images
                    if self.related_images:
                        print('\nGetting list of related keywords...'
                              'this may take a few moments')
                        tabs = self.get_all_tabs(raw_html)
                        for key, value in tabs.items():
                            final_search_term = '{}-{}'.format(search_term, key)
                            print('\nNow Downloading - ' + final_search_term)
                            new_raw_html = self.download_page(value)
                            self.create_directories(
                                    arguments.main_directory,
                                    final_search_term,
                                    self.thumbnail,
                                    self.thumbnail_only)
                            self._get_all_items(new_raw_html, arguments.main_directory,
                                                search_term + ' - ' + key,
                                                arguments.limit, arguments)

                    i += 1
                    total_errors = total_errors + errorCount
                    sprint('\nErrors: ' + str(errorCount) + '\n')

        return paths, total_errors


# ------------ Main Program -------------#
def main():
    records = user_input()
    total_errors = 0
    t0 = time.time()
    for arguments in records:
        if arguments.single_image:
            downloader = GoogleImagesDownloader()
            downloader.single_image(arguments.single_image)
        else:
            downloader = GoogleImagesDownloader()
            paths, errors = downloader.download(arguments)
            total_errors = total_errors + errors

        t1 = time.time()
        total_time = int(t1) - int(t0)
        sprint('\nEverything downloaded!\nTotal errors: {}\nTotal time taken: {} Seconds'.format(
               total_errors, total_time))
    print('Done')


if __name__ == '__main__':
    main()
