#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import os
import sys
import re
import traceback

import argparse
from ruamel.yaml import YAML
yaml = YAML()

reload(sys)
sys.setdefaultencoding('utf-8')


content_regex = re.compile(r'---([\s\S]*?)---([\s\S]*)')
replace_regex_list = [
    # (re.compile(r'^```(.*?)\n(.*?)\n```', re.DOTALL), r'{{< highlight \1 >}}\n\2\n{{< /highlight >}}'),
    (re.compile(r'<!--\smore\s-->'), '<!--more-->'),
    (re.compile(r'\{%\sraw\s%\}(.*)\{%\sendraw\s%\}'), r'\1')
]
filename_regex = re.compile(r'(\d+-\d+-\d+)-(.*)')


# class MyDumper(yaml.RoundTripDumper):
#     def increase_indent(self, flow=False, sequence=None, indentless=False):
#         return super(MyDumper, self).increase_indent(
#             flow=flow,
#             sequence=sequence,
#             indentless=indentless)


def convert_front_matter(front_data, post_date, url):
    del front_data['id']
    del front_data['layout']
    front_data["date"] = post_date.strftime('%Y-%m-%dT%H:%M:%S+08:00')

    for tag in ['tags', 'categories', 'category']:
        if tag in front_data and isinstance(front_data[tag], basestring):
            front_data[tag] = front_data[tag].split(' ')

    if 'category' in front_data:
        front_data['categories'] = front_data['category']
        del front_data['category']

    front_data['title'] = front_data.pop("title")
    # front_data['author'] =
    # front_data['tagline'] = front_data.pop("tagline", None)
    front_data['date'] = front_data.pop("date")
    front_data['draft'] = False
    # front_data['type'] = "single"
    front_data['layout'] = "single"
    front_data['comment'] = True
    front_data['keywords'] = []
    front_data['description'] = None

    _url = url.split('/')
    _url.pop(-1)
    front_data['aliases'] = [
        "/{}{}".format(front_data['categories'][0], url),
        "/{}{}.html".format(front_data['categories'][0], "/".join(_url))
    ]
    front_data['categories'] = front_data.pop("categories")
    front_data['tags'] = front_data.pop("tags")
    front_data['original'] = True
    front_data['reference'] = []

    print front_data, post_date, url


def convert_body_text(body_text):
    result = body_text
    for regex, replace_with in replace_regex_list:
        result = regex.sub(replace_with, result)

    return result


def write_out_file(front_data, body_text, out_file_path):
    with open(out_file_path, 'w') as f:
        f.write('---\n')
        yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.dump(front_data, f)
        f.write('---\n')
        f.write('\n'.join(body_text.splitlines()))


def parse_from_filename(filename):
    slug = os.path.splitext(filename)[0]
    m = filename_regex.match(slug)
    if m:
        slug = m.group(2)
        post_date = datetime.strptime(m.group(1), '%Y-%m-%d')
        return post_date, '/%s/%s/' % (post_date.strftime('%Y/%m/%d'), slug)
    return None, '/' + slug


def convert_post(file_path, out_dir):
    filename = os.path.basename(file_path)
    post_date, url = parse_from_filename(filename)

    content = ''
    with open(file_path, 'r') as f:
        content = f.read()

    m = content_regex.match(content)
    if not m:
        print 'Error match content: %s' % file_path
        return False

    front_data = yaml.load(m.group(1))
    if not front_data:
        print 'Error load yaml: %s' % file_path
        return False

    '''
    if 'layout' in front_data:
        if post_date:
            out_dir = os.path.join(out_dir, front_data['layout'], str(post_date.year))
        else:
            out_dir = os.path.join(out_dir, front_data['layout'])
    '''

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    out_file_path = os.path.join(out_dir, filename)

    convert_front_matter(front_data, post_date, url)
    body_text = convert_body_text(m.group(2))
    write_out_file(front_data, body_text, out_file_path)

    return True


def convert(src_dir, out_dir):
    count = 0
    error = 0
    for root, dirs, files in os.walk(src_dir):
        for filename in files:
            try:
                if os.path.splitext(filename)[1] != '.md' \
                        or filename in ['README.md', 'LICENSE.md']:
                    continue
                file_path = os.path.join(root, filename)
                common_prefix = os.path.commonprefix(
                    [src_dir, file_path])
                rel_path = os.path.relpath(
                    os.path.dirname(file_path), common_prefix)
                real_out_dir = os.path.join(out_dir, rel_path)
                if convert_post(file_path, real_out_dir):
                    print 'Converted: %s' % file_path
                    count += 1
                else:
                    error += 1
            except Exception as e:
                error += 1
                print 'Error convert: %s \nException: %s' % (file_path, e)
                print traceback.print_exc()

    print '--------\n%d file converted! %s' % (count, 'Error count: %d' % error if error > 0 else 'Congratulation!!!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert Jekyll blog to Hugo')
    parser.add_argument(
        'src_dir', help='jekyll post dir')
    parser.add_argument(
        'out_dir', help='hugo root path')
    args = parser.parse_args()

    convert(
        os.path.abspath(args.src_dir),
        os.path.abspath(args.out_dir))
