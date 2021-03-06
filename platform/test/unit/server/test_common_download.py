# -*- coding: utf-8 -*-
#
# Copyright © 2013 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the License
# (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied, including the
# implied warranties of MERCHANTABILITY, NON-INFRINGEMENT, or FITNESS FOR A
# PARTICULAR PURPOSE.
# You should have received a copy of GPLv2 along with this software; if not,
# see http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt

import os
import re
import shutil
import tempfile
import unittest

import mock
import pycurl

from pulp.common.download import factory as download_factory
from pulp.common.download.backends import curl as curl_backend
from pulp.common.download.config import DownloaderConfig
from pulp.common.download.request import DownloadRequest

from http_static_test_server import HTTPStaticTestServer

# mock and test data classes ---------------------------------------------------

class MockEventListener(mock.Mock):

    def __init__(self):
        super(MockEventListener, self).__init__()

        self.batch_started = mock.Mock()
        self.batch_finished = mock.Mock()

        self.download_started = mock.Mock()
        self.download_progress = mock.Mock()
        self.download_succeeded = mock.Mock()
        self.download_failed = mock.Mock()


def mock_curl_multi_factory():

    mock_curl_multi = mock.Mock()
    mock_curl_multi._curls = []
    mock_curl_multi._opts = {}

    def _add_handle(curl):
        curl._is_active = True
        mock_curl_multi._curls.append(curl)

    def _info_read():
        return 0, [c for c in mock_curl_multi._curls if c._is_active], []

    def _perform():
        for curl in mock_curl_multi._curls:
            curl.perform()
        return 0, len(mock_curl_multi._curls)

    def _remove_handle(curl):
        curl._is_active = False
        mock_curl_multi._curls.remove(curl)

    def _setopt(opt, setting):
        mock_curl_multi._opts[opt] = setting

    mock_curl_multi.add_handle = mock.Mock(wraps=_add_handle)
    mock_curl_multi.close = mock.Mock()
    mock_curl_multi.info_read = mock.Mock(wraps=_info_read)
    mock_curl_multi.perform = mock.Mock(wraps=_perform)
    mock_curl_multi.remove_handle = mock.Mock(wraps=_remove_handle)
    mock_curl_multi.select = mock.Mock()
    mock_curl_multi.setopt = mock.Mock(wraps=_setopt)

    return mock_curl_multi


def mock_curl_factory():

    mock_curl = mock.Mock()
    mock_curl._is_active = False
    mock_curl._opts = {}

    def _perform():
        # strip off the protocol scheme + hostname + port and use the remaining *relative* path
        input_file_path = re.sub(r'^[a-z]+://localhost:8088/', '', mock_curl._opts[pycurl.URL], 1)
        input_fp = open(input_file_path, 'rb')

        output_fp = mock_curl._opts[pycurl.WRITEDATA]

        progress_callback = mock_curl._opts[pycurl.PROGRESSFUNCTION]
        progress_callback(0, 0, 0, 0)

        shutil.copyfileobj(input_fp, output_fp)

        file_size = os.fstat(input_fp.fileno())[6]
        progress_callback(file_size, file_size, 0, 0)

        input_fp.close()

    def _setopt(opt, setting):
        mock_curl._opts[opt] = setting

    mock_curl.perform = mock.Mock(wraps=_perform)
    mock_curl.setopt = mock.Mock(wraps=_setopt)

    return mock_curl


class MockObjFactory(object):

    def __init__(self, mock_obj_factory):
        self.mock_obj_factory = mock_obj_factory
        self.mock_objs = []

    def __call__(self):
        mock_instance = self.mock_obj_factory()
        self.mock_objs.append(mock_instance)
        return mock_instance

# test suite -------------------------------------------------------------------

class FactoryTests(unittest.TestCase):

    def test_http_factory(self):
        config = DownloaderConfig('http')
        downloader = download_factory.get_downloader(config)

        self.assertTrue(isinstance(downloader, curl_backend.HTTPCurlDownloadBackend))

    def test_https_factory(self):
        config = DownloaderConfig('https')
        downloader = download_factory.get_downloader(config)

        self.assertTrue(isinstance(downloader, curl_backend.HTTPSCurlDownloadBackend))

        ssl_working_dir = downloader.ssl_working_dir
        self.assertTrue(os.path.exists(ssl_working_dir))

        del downloader
        self.assertFalse(os.path.exists(ssl_working_dir))


class DownloadTests(unittest.TestCase):
    data_dir = 'data/test_common_download/'
    file_list = ['100K_file', '500K_file', '1M_file']
    file_sizes = [102400, 512000, 1048576]

    def setUp(self):
        self.storage_dir = tempfile.mkdtemp(prefix='test_common_download-')

    def tearDown(self):
        shutil.rmtree(self.storage_dir)
        self.storage_dir = None

    def _download_requests(self, protocol='http'):
        # localhost:8088 is here for the live tests
        return [DownloadRequest(protocol + '://localhost:8088/' + self.data_dir + f, os.path.join(self.storage_dir, f))
                for f in self.file_list]


class MockCurlDownloadTests(DownloadTests):
    # test suite that really tests the download framework built on top of pycurl

    @mock.patch('pycurl.CurlMulti', MockObjFactory(mock_curl_multi_factory))
    @mock.patch('pycurl.Curl', MockObjFactory(mock_curl_factory))
    def test_download_single_file(self):
        config = DownloaderConfig('http')
        downloader = download_factory.get_downloader(config)
        request_list = self._download_requests()[:1]
        downloader.download(request_list)

        self.assertEqual(len(pycurl.CurlMulti.mock_objs), 1)
        self.assertEqual(len(pycurl.Curl.mock_objs), curl_backend.DEFAULT_MAX_CONCURRENT)

        mock_multi_curl = pycurl.CurlMulti.mock_objs[0]

        self.assertEqual(mock_multi_curl.setopt.call_count, 2) # dangerous as this could easily change
        self.assertEqual(mock_multi_curl.add_handle.call_count, 1)
        self.assertEqual(mock_multi_curl.select.call_count, 1)
        self.assertEqual(mock_multi_curl.perform.call_count, 1)
        self.assertEqual(mock_multi_curl.info_read.call_count, 1)
        self.assertEqual(mock_multi_curl.remove_handle.call_count, 1)

        mock_curl = pycurl.Curl.mock_objs[-1] # curl objects are used from back of the list

        self.assertEqual(mock_curl.setopt.call_count, 9) # also dangerous for the same reasons
        self.assertEqual(mock_curl.perform.call_count, 1)

    @mock.patch('pycurl.CurlMulti', MockObjFactory(mock_curl_multi_factory))
    @mock.patch('pycurl.Curl', MockObjFactory(mock_curl_factory))
    def test_download_multi_file(self):
        config = DownloaderConfig('http')
        downloader = download_factory.get_downloader(config)
        request_list = self._download_requests()
        downloader.download(request_list)

        # this is really just testing my mock curl objects, but it's nice to know
        for file_name, file_size in zip(self.file_list, self.file_sizes):
            input_file = os.path.join(self.data_dir, file_name)
            input_file_size = os.stat(input_file)[6]

            output_file = os.path.join(self.storage_dir, file_name)
            output_file_size = os.stat(output_file)[6]

            self.assertEqual(input_file_size, file_size)
            self.assertEqual(output_file_size, file_size) # does check that close() was called properly

        mock_curl_multi = pycurl.CurlMulti.mock_objs[0]
        self.assertEqual(mock_curl_multi.perform.call_count, 1)

        num_unused_curl_objs = max(0, curl_backend.DEFAULT_MAX_CONCURRENT - len(self.file_list))
        unused_mock_curl_objs = pycurl.Curl.mock_objs[:num_unused_curl_objs]

        for mock_curl in unused_mock_curl_objs:
            self.assertEqual(mock_curl.perform.call_count, 0)

        used_mock_curl_objs = pycurl.Curl.mock_objs[num_unused_curl_objs:]

        for mock_curl in used_mock_curl_objs:
            self.assertEqual(mock_curl.perform.call_count, 1)

    @mock.patch('pycurl.CurlMulti', MockObjFactory(mock_curl_multi_factory))
    @mock.patch('pycurl.Curl', MockObjFactory(mock_curl_factory))
    def test_download_event_listener(self):
        config = DownloaderConfig('http')
        listener = MockEventListener()
        downloader = download_factory.get_downloader(config, listener)
        request_list = self._download_requests()[:1]
        downloader.download(request_list)

        self.assertEqual(listener.batch_started.call_count, 1)
        self.assertEqual(listener.batch_finished.call_count, 1)
        self.assertEqual(listener.download_started.call_count, 1)
        self.assertEqual(listener.download_progress.call_count, 2) # this one only tests the mock curl
        self.assertEqual(listener.download_succeeded.call_count, 1)
        self.assertEqual(listener.download_failed.call_count, 0)

    @mock.patch('pycurl.CurlMulti', MockObjFactory(mock_curl_multi_factory))
    @mock.patch('pycurl.Curl', MockObjFactory(mock_curl_factory))
    def test_https_download(self):
        config = DownloaderConfig('https')
        downloader = download_factory.get_downloader(config)

        for attr in ('ssl_working_dir', 'ssl_ca_cert', 'ssl_client_cert', 'ssl_client_key'):
            self.assertTrue(hasattr(downloader, attr))

        request_list = self._download_requests('https')[:1]
        downloader.download(request_list)

        mock_curl = pycurl.Curl.mock_objs[-1] # curl objects are used from the end

        self.assertEqual(mock_curl.setopt.call_count, 11) # dangerous as this could easily change

class LiveCurlDownloadTests(DownloadTests):
    # test suite that tests that pycurl is being used (mostly) correctly

    http_server = HTTPStaticTestServer()

    @classmethod
    def setUpClass(cls):
        cls.http_server.start()

    @classmethod
    def tearDownClass(cls):
        cls.http_server.stop()

    def test_download_single(self):
        config = DownloaderConfig('http')
        downloader = download_factory.get_downloader(config)
        request_list = self._download_requests()[:1]
        downloader.download(request_list)

        input_file_name = self.file_list[0]
        input_file_size = self.file_sizes[0]

        output_file_path = os.path.join(self.storage_dir, input_file_name)
        output_file_size = os.stat(output_file_path)[6]

        self.assertEqual(input_file_size, output_file_size)

    def test_download_multiple(self):
        config = DownloaderConfig('http')
        downloader = download_factory.get_downloader(config)
        request_list = self._download_requests()

        try:
            downloader.download(request_list)

        except Exception, e:
            self.fail(str(e))

    def test_download_even_listener(self):
        config = DownloaderConfig('http')
        listener = MockEventListener()
        downloader = download_factory.get_downloader(config, listener)
        request_list = self._download_requests()[:1]
        downloader.download(request_list)

        self.assertEqual(listener.batch_started.call_count, 1)
        self.assertEqual(listener.batch_finished.call_count, 1)
        self.assertEqual(listener.download_started.call_count, 1)
        self.assertNotEqual(listener.download_progress.call_count, 0) # not sure how many times
        self.assertEqual(listener.download_succeeded.call_count, 1)
        self.assertEqual(listener.download_failed.call_count, 0)

