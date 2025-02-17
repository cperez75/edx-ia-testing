'''
Add in /edx/app/edxapp/edx-platform/lms/envs/aws.py:
ORA2_SWIFT_URL = AUTH_TOKENS["ORA2_SWIFT_URL"]
ORA2_SWIFT_KEY = AUTH_TOKENS["ORA2_SWIFT_KEY"]

Add in /edx/app/edxapp/lms.auth.json
"ORA2_SWIFT_URL": "https://EXAMPLE",
"ORA2_SWIFT_KEY": "EXAMPLE",

ORA2_SWIFT_KEY should correspond to Meta Temp-Url-Key configure in swift. Run
'swift stat -v' to get it.
'''

import logging

import urllib
import requests

from django.conf import settings

import swiftclient

from ..exceptions import FileUploadInternalError
from .base import BaseBackend

logger = logging.getLogger("ieia.fileupload.api")  # pylint: disable=invalid-name

# prefix paths with current version, in case we need to roll it at some point
SWIFT_BACKEND_VERSION = 1


class Backend(BaseBackend):
    """
    Upload ieia student files to swift
    """

    def get_upload_url(self, key, content_type):
        bucket_name, key_name = self._retrieve_parameters(key)
        key, url = get_settings()
        try:
            temp_url = swiftclient.utils.generate_temp_url(
                path=f'/v{SWIFT_BACKEND_VERSION}{url.path}/{bucket_name}/{key_name}',
                key=key,
                method='PUT',
                seconds=self.UPLOAD_URL_TIMEOUT
            )
            return f'{url.scheme}://{url.netloc}{temp_url}'
        except Exception as ex:
            logger.exception(
                "An internal exception occurred while generating an upload URL."
            )
            raise FileUploadInternalError(ex) from ex

    def get_download_url(self, key):
        bucket_name, key_name = self._retrieve_parameters(key)
        key, url = get_settings()
        try:
            temp_url = swiftclient.utils.generate_temp_url(
                path=f'/v{SWIFT_BACKEND_VERSION}{url.path}/{bucket_name}/{key_name}',
                key=key,
                method='GET',
                seconds=self.DOWNLOAD_URL_TIMEOUT
            )
            download_url = f'{url.scheme}://{url.netloc}{temp_url}'
            response = requests.get(download_url)
            return download_url if response.status_code == 200 else ""
        except Exception as ex:
            logger.exception(
                "An internal exception occurred while generating a download URL."
            )
            raise FileUploadInternalError(ex) from ex

    def remove_file(self, key):
        bucket_name, key_name = self._retrieve_parameters(key)
        key, url = get_settings()
        try:
            temp_url = swiftclient.utils.generate_temp_url(
                path=f'{url.path}/{bucket_name}/{key_name}',
                key=key,
                method='DELETE',
                seconds=self.DOWNLOAD_URL_TIMEOUT)
            remove_url = f'{url.scheme}://{url.netloc}{temp_url}'
            response = requests.delete(remove_url)
            return response.status_code == 204
        except Exception as ex:
            logger.exception(
                "An internal exception occurred while removing object on swift storage."
            )
            raise FileUploadInternalError(ex) from ex


def get_settings():
    """
    Returns the swift key and a parsed url.
    Both are generated from django settings.
    """

    url = getattr(settings, 'ORA2_SWIFT_URL', None)
    key = getattr(settings, 'ORA2_SWIFT_KEY', None)
    url = urllib.parse.urlparse(url)
    return key, url
