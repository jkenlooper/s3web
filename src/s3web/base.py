from shutil import move
import os
import os.path
import time
import datetime
import hashlib
import ConfigParser

"""
get a connection to the bucket
  create bucket if not existing
    setup bucket to be available to the web
get a list of all files in local dir
  filter out files not in the include list
walk through all remote files and delete keys that aren't available locally
compare hash of remote file and local file and remove from local list if the same
upload all remaining files in local list
  update hash in metadata of remote file

"""

INCLUDE_FILE_EXTENSIONS = set([
  '.html',
  '.js',
  '.css',
  '.png',
  '.gif',
  '.jpg',
  '.pdf',
  '.doc'
  ])

EXCLUDE_DIRECTORIES = set([
  '.*'
  ])

EXCLUDE_FILES = set([
  ])

def Property(func):
  """ http://adam.gomaa.us/blog/the-python-property-builtin/ """
  return property(**func())

class WebBucketController(object):
  def __init__(self, s3connection, domain_name, dir):
    self.s3connection = s3connection
    self.domain_name = domain_name
    self.dir = dir
    self._include_file_extensions = INCLUDE_FILE_EXTENSIONS
    self._exclude_directories = set(glob(EXCLUDE_DIRECTORIES))
    self._exclude_files = set(glob(EXCLUDE_FILES))

  @Property
  def include_file_extensions():
    doc = "Acceptable file extensions to upload"
    def fget(self):
      return self._include_file_extensions
    def fset(self, exts):
      self._include_file_extensions = exts
    return locals()


  @Property
  def exclude_files():
    doc = "path to files that should be excluded"
    def fget(self):
      return self._exclude_files
    def fset(self, files):
      fs = []
      for f in files:
        fs.extend(glob(f))
      self._exclude_files = set(fs)
    return locals()

  @Property
  def exclude_directories():
    doc = "directories that should be excluded"
    def fget(self):
      return self._exclude_directories
    def fset(self, dirs):
      ds = []
      for d in dirs:
        ds.extend(glob(d))
      self._exclude_directories = set(ds)
    return locals()

  @Property
  def local_keys():
    doc = "list of local files/directories returned as key names"
    def fget(self):
      keys = set()
      for root, dir, file_names in os.walk(self.dir, topdown=True):
        if root not in self.exclude_directories:
          for f in file_names:
            f_path = os.path.join(root, f)
            (f_root, f_ext) = os.path.splitext(f_path)
            if f_ext in self.include_file_extensions:
              if f_path not in self.exclude_files:
                keys.add(f_path)
          for d in dir:
            d_path = os.path.join(root, d)
            if d_path not in self.exclude_directories
              keys.add(d_path)
      return keys
    return locals()

