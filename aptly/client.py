# -*- coding: utf-8 -*-

import requests
import json
import logging
from aptly.exceptions import AptlyException

lg = logging.getLogger(__name__)


class Aptly(object):
    def __init__(self, url, auth=None, timeout=300, dry=False):
        self.url = '%s%s' % (url, '/api')
        self.timeout = timeout
        self.dry = dry

        self.session = requests.Session()
        if auth is not None:
            self.session.auth = auth
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-type': 'application/json',
        })
        self.api_version = self.get_version()

    def get_version(self):
        return self.do_get('/version')["Version"]

    def _process_result(self, res):
        if res.status_code < 200 or res.status_code >= 300:
            raise AptlyException(
                res,
                "Something went wrong: %s (%s)" % (res.reason, res.status_code)
            )
        try:
            return res.json()
        except ValueError:
            return res.text

    def do_get(self, uri, kwargs=None, timeout=None):
        url = '%s%s' % (self.url, uri)
        lg.debug("GET %s, args=%s" % (url, kwargs))
        res = self.session.get(
            url,
            timeout=timeout or self.timeout,
            params=kwargs,
        )
        return self._process_result(res)

    def do_post(self, uri, data, timeout=None):
        data_json = json.dumps(data)
        url = '%s%s' % (self.url, uri)
        lg.debug("POST %s, data=%s" % (url, data_json))

        if self.dry:
            return

        res = self.session.post(
            url,
            timeout=timeout or self.timeout,
            data=data_json,
        )
        return self._process_result(res)

    def do_delete(self, uri, timeout=None):
        url = '%s%s' % (self.url, uri)
        lg.debug("DELETE %s" % url)

        if self.dry:
            return

        res = self.session.delete(
            url,
            timeout=timeout or self.timeout,
        )
        return self._process_result(res)

    def do_put(self, uri, data, timeout=None):
        data_json = json.dumps(data)
        url = '%s%s' % (self.url, uri)
        lg.debug("PUT %s, data=%s" % (url, data_json))

        if self.dry:
            return

        res = self.session.put(
            url,
            timeout=timeout or self.timeout,
            data=data_json,
        )
        return self._process_result(res)
