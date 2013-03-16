s3web
=====

Simple upload files to amazon s3 as a website.

Usage
=====

s3web --config path/to/s3web.cfg path/to/directory-to-upload

An example of a s3web.cfg::

  [s3web]
  api_key = Some-api-key
  api_secret = The-api-secret
  domain_name = www.example.com

Then just set the CNAME and all that other stuff.
