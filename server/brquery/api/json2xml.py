#!/usr/bin/python

import sys
import json
import traceback
import getopt
import numbers

from xml.dom.minidom import Document

def parse_element(doc, root, j):
  if isinstance(j, dict):
    for key in j.keys():
      value = j[key]
      if isinstance(value, list):
        for e in value:
          elem = doc.createElement(key)
          parse_element(doc, elem, e)
          root.appendChild(elem)
      else:
        if key.isdigit():
          elem = doc.createElement('item')
          elem.setAttribute('value', key)
        else:
          elem = doc.createElement(key)
        parse_element(doc, elem, value)
        root.appendChild(elem)
  elif isinstance(j, str) or isinstance(j, unicode):
    text = doc.createTextNode(j)
    root.appendChild(text)
  elif isinstance(j, numbers.Number):
    text = doc.createTextNode(str(j))
    root.appendChild(text)
  else:
    raise Exception("bad type '%s' for '%s'" % (type(j), j,))

def parse_doc(root, j):
  doc = Document()
  if root is None:
    if len(j.keys()) > 1:
      raise Exception('Expected one root element, or use --root to set root')
    root = j.keys()[0]
    elem = doc.createElement(root)
    j = j[root]
  else:
    elem = doc.createElement(root)
  parse_element(doc, elem, j)
  doc.appendChild(elem)
  return doc

def parse_json_example():
  js = r"""{"object": {"content": "bla bla bla", "type": "note", "links": {"alternate": [{"href": "http://www.google.com/buzz/111/222", "type": "text/html"}, {"href": "http://www.google.com/buzz/1111/2222", "type": "text/html"}]}}, "id": "tag:google.com,2010:buzz:1111", "links": {"alternate": [{"href": "http://www.google.com/buzz/11111/222", "type": "text/html"}]}}"""
  j = json.loads(js)
  doc = parse_doc("post", j)
  print doc.toprettyxml(encoding="utf-8", indent="  ")

def parse_json_stdin(root):
  js = "".join(sys.stdin.readlines())
  j = json.loads(js)
  doc = parse_doc(root, j)
  print doc.toprettyxml(encoding="utf-8", indent="  ")

def usage():
  print '''
Usage:    %s <-r root element>

-r (--root):        root element name

Exiting...
  ''' % (sys.argv[0])


def main():

  root = None

  if len(sys.argv[1:]):
    try:
      (opts, args) = getopt.getopt(sys.argv[1:], 'r:', ['root']) 
      if (len(args)):
        raise getopt.GetoptError('bad parameter')
    except getopt.GetoptError:
      usage()
      sys.exit(0)

    for (opt, arg) in opts:
      if opt in ('-r', '--root'):
        root = arg

  parse_json_stdin(root)

if __name__ == '__main__':
  try:
    main()
  except:
      print >> sys.stderr, '\nException!!!'
      print >> sys.stderr, '-' * 50
      traceback.print_exc()
      print >> sys.stderr, '-' * 50

