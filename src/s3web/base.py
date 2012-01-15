from shutil import move
from glob import glob
import os
import os.path
import time
import datetime
import hashlib
import ConfigParser
import logging
from mimetypes import types_map

from boto.s3.key import Key

log = logging.getLogger('s3web.base')

INCLUDE_FILE_EXTENSIONS = set([
  '.html',
  '.js',
  '.css',
  '.png',
  '.gif',
  '.jpg',
  '.jpeg',
  '.bmp',
  '.ico',
  '.pdf',
  '.doc'
  ])

EXCLUDE_DIRECTORIES = set([
  '.*',
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
    #if not self.bucket:
      #print 'creating bucket'
    self.bucket = self.s3connection.create_bucket(self.domain_name) 
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
        if f != "":
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
        if d != "":
          d = os.path.join(self.dir, d)
          ds.extend(glob(d))
      self._exclude_directories = set(ds)
    return locals()

  @Property
  def local_keys():
    doc = "list of local files/directories returned as key names"
    def fget(self):
      keys = set()
      for root, dir, file_names in os.walk(self.dir, topdown=True, followlinks=True):
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
            log.debug('d_path: %s', d_path)
            for ex in self.exclude_directories:
              log.debug('ex = %s', ex)
              if d_path[:len(ex)] == ex:
                log.debug('removing %s', d)
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
        print 'local_file_path', local_file_path
        if os.path.isfile(local_file_path):
          lf = open(local_file_path, 'r')
          local_hash = remote_key.compute_md5(lf)[0]
          #local_hash = hashlib.md5(lf.read()).hexdigest()
          print 'comparing_keys:', local_hash, remote_key.etag
          if local_hash == remote_key.etag.replace('"',''): # comparing md5 and etag; this may fail
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
        k.set_metadata('Content-Type', types_map.get(ext, 'application/octet-stream'))
        k.set_metadata('md5-hex', local_hash_tuple[0])
        k.set_acl('public-read')
        lf.close()

  def upload(self):
    """ convience function to sync list and upload it """
    self.upload_list(self.sync_list())

