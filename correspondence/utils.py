import requests
from core.models import SystemParameter
from django.conf import settings
from requests.auth import HTTPBasicAuth
from django.contrib.postgres.search import SearchVector, SearchQuery
from correspondence.models import Radicate
import os
import logging

logger = logging.getLogger(__name__)

from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage
from django.core.files.temp import NamedTemporaryFile
from django.core import files


def search_by_term(term):
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(
            settings.ECM_SEARCH_URL,
            json={
                "query": {"query": term},
                "highlight": {
                    "mergeContiguous": True, "fragmentSize": 150, 
                    "usePhraseHighlighter": True,
                    "fields": [
                        {"field": "name", "prefix": "( ", "postfix": " )"},
                        {"field": "content", "prefix": "( ", "postfix": " )"}
                    ]
                }
            },
            auth=HTTPBasicAuth(settings.ECM_USER, settings.ECM_PASSWORD),
            headers=headers
        )

        # list of responses from ECM
        entries = response.json()['list']['entries']
        # list of cmis id's from response
        cmis_id_list = [data['entry']['id'] for data in entries]

        vector = SearchVector('number', 'subject', 'person__name', 'person__document_number')
        query = SearchQuery(term)

        # list of radicates with the cmis id's
        radicate_list = Radicate.objects.annotate(search=vector).filter(search=query) | Radicate.objects.filter(cmis_id__in=cmis_id_list)

    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as Error:
        raise

    return radicate_list
