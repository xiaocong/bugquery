#!/usr/bin/env python
import urllib2
import json
import os
import dcrator


BRAUTH = 'http://localhost:%s/api/brauth' % os.environ.get("SERVER_PORT", 8010)


def access(url, headers=None, data=None):
    req = urllib2.Request(url)
    if data is not None:
        req.add_data(json.dumps(data))
    if headers is not None:
        for key in headers:
            req.add_header(key, headers[key])
    f = urllib2.urlopen(req)
    return f.readline()


@dcrator.timeit
def getAccessibleProducts(token):
    '''
    Get accessible products for the given token.
    Parameter: token
    Return: {'products':['P1','P2','P3']} or {'error':{'code':'123','msg':'abc'}} or None
    '''
    url = BRAUTH + "/accessible_products?token=" + token
    try:
        msg = json.loads(access(url))
        if 'results' in msg:
            results = json.loads(msg['results'])
            if 'products' in results or 'error' in results:
                return results
            else:
                raise Exception('Invalid response:%s' % msg)
        else:
            raise Exception('Invalid response:%s' % msg)
    except Exception, e:
        print "getAccessibleProducts(),error:%s" % e
        return {'error': 'Encounter error while authenticating.'}

if (__name__ == '__main__'):
    ret = getAccessibleProducts('6dd851bd-f8fc-4984-832c-88493d8b6314')
    print type(ret)
    print ret
