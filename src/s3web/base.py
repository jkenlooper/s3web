from shutil import move
from glob import glob
import os
import os.path
import time
import datetime
import hashlib
import ConfigParser

from boto.s3.key import Key

from media import cType

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
  '.*',
  ])

EXCLUDE_FILES = set([
  ])

BUCKET_PREFIX = 'wot-'

def Property(func):
  """ http://adam.gomaa.us/blog/the-python-property-builtin/ """
  return property(**func())

class WebBucketController(object):
  def __init__(self, s3connection, domain_name, dir):
    self.s3connection = s3connection
    self.domain_name = domain_name
    self.bucket = self.s3connection.get_bucket(''.join((BUCKET_PREFIX, self.domain_name)))
    if not self.bucket:
      print 'creating bucket'
      self.bucket = self.s3connection.create_bucket(''.join((BUCKET_PREFIX, self.domain_name))) 
    self.bucket.set_acl('public-read')
    self.bucket.configure_website('index.html', error_key='404.html')

    self.url = self.bucket.get_website_endpoint()
    self.dir = os.path.normpath(dir)
    self._include_file_extensions = INCLUDE_FILE_EXTENSIONS
    ds = []
    for d in EXCLUDE_DIRECTORIES:
      ds.extend(glob(os.path.join(self.dir, d)))
    self._exclude_directories = set(ds)
    fs = []
    for f in EXCLUDE_FILES:
      fs.extend(glob(os.path.join(self.dir, f)))
    self._exclude_files = set(fs)

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
        fs.extend(glob(os.path.join(self.dir, f)))
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
                keys.add(f_path[len(self.dir)+1:])

          filtered_dir = dir
          for d in dir:
            d_path = os.path.join(root, d)
            for ex in self.exclude_directories:
              if d_path[:len(ex)] == ex:
                filtered_dir.remove(d)
          for d in filtered_dir:
            d_path = os.path.join(root, d)
            keys.add(d_path[len(self.dir)+1:])
          dir = filtered_dir
      return keys
    return locals()

  def sync_list(self):
    """ return a synced list of files/directories to upload  """
    local_list = list(self.local_keys)
    for remote_key in self.bucket.list():
      if remote_key.name not in local_list:
        self.bucket.delete_key(remote_key.name)
      else:
        local_file_path = os.path.join(self.dir, remote_key.name)
        if os.path.isfile(local_file_path):
          lf = open(local_file_path, 'r')
          local_hash = remote_key.compute_md5(lf)[0]
          if local_hash in remote_key.etag: # comparing md5 and etag; this may fail
            local_list.remove(remote_key.name)


    return local_list

  def upload_list(self, local_list):
    """ upload list of files """
    for local_name in local_list:
      k = self.bucket.get_key(local_name)
      if not k:
        k = self.bucket.new_key(local_name)
      local_file_path = os.path.join(self.dir, local_name)
      if os.path.isfile(local_file_path):
        lf = open(local_file_path, 'r')
        (base_name, ext) = os.path.splitext(local_file_path)
        local_hash_tuple = k.compute_md5(lf)
        k.set_contents_from_file(lf, md5=local_hash_tuple)
        k.set_metadata('Content-Type', cType.get(ext, 'application/octet-stream'))
        k.set_metadata('md5-hex', local_hash_tuple[0])
        k.set_acl('public-read')
        lf.close()

  def upload(self):
    """ convience function to sync list and upload it """
    self.upload_list(self.sync_list())

