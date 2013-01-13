#!/usr/bin/python
# -*- coding: utf-8 -*-
from optparse import OptionParser
import os
import os.path
import ConfigParser

from boto.s3.connection import S3Connection
from progressbar import FileTransferSpeed, ETA, Bar, Percentage, \
    ProgressBar

import base
from _version import __version__


def main(config_file=False):
    if not config_file:
        config_file = 's3web.cfg'
    parser = OptionParser(version=__version__,
                          description='upload files to s3 and set them up for a website'
                          )

    parser.add_option('--config', action='store', type='string',
                      default=config_file,
                      help='specify a s3web config file to use.')
    parser.add_option('--dry_run', '-n', action='store_true',
                      help='just show the files that will be uploaded.')

    (options, args) = parser.parse_args()

    web_dir = '.'
    if args:
        web_dir = args[0]

    config = ConfigParser.SafeConfigParser()
    config.read(options.config)
    s3conn = S3Connection(config.get('s3web', 'api_key'),
                          config.get('s3web', 'api_secret'))

    web_bucket = base.WebBucketController(s3conn, config.get('s3web',
            'domain_name'), web_dir)
    print web_bucket.url

    web_bucket.upload()
