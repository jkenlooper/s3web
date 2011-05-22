from optparse import OptionParser
import os
import os.path
import ConfigParser

from progressbar import FileTransferSpeed, ETA, Bar, Percentage, ProgressBar

import base
from _version import __version__

def main(config_file=False):
  if not config_file:
    config_file = "s3web.cfg"
  parser = OptionParser(version=__version__, description="upload files to s3 and set them up for a website")

  parser.add_option("--config",
      action="store",
      type="string",
      default=config_file,
      help="specify a s3web config file to use.")
  parser.add_option("--dry_run", "-n",
      action="store_true",
      help="just show the files that will be uploaded.")

  (options, args) = parser.parse_args()

  config = ConfigParser.SafeConfigParser()
  #config.read(options.config)

  web_bucket = base.WebBucketController(None, None, '.')
  print web_bucket.local_keys

