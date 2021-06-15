import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
from django.contrib.postgres.search import SearchVector, SearchQuery
from correspondence.models import Radicate
from django.core.files.temp import NamedTemporaryFile
import logging
import json
from core.models import AppParameter

logger = logging.getLogger(__name__)

class ECMService(object):
    '''ECM handler for Alfresco'''

    _params = {}

    @classmethod
    def get_basic_authentication(cls):
        return HTTPBasicAuth(cls._params['ECM_USER'], cls._params['ECM_PASSWORD'])

    def get_params(func):
        '''Lazy load of ECM database parameters'''
    
        def wrapper(*args, **kwargs):
            # Lazy load
            if not ECMService._params:
                # Get only ECM related parameters
                qs = AppParameter.objects.filter(name__startswith='ECM_')
                ECMService._params = {entry.name : entry.value for entry in qs}
            return func(*args, **kwargs)
        return wrapper

    @classmethod
    @get_params
    def search_by_term(cls, term):
        '''Term based query'''

        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(
                cls._params['ECM_SEARCH_URL'],
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
                auth=cls.get_basic_authentication(),
                headers=headers
            )

            # list of responses from ECM
            entries = response.json()['list']['entries']
            # list of cmis id's from response
            cmis_id_list = [data['entry']['id'] for data in entries]

            vector = SearchVector('number', 'subject', 'person__name', 'person__document_number')
            query = SearchQuery(term)

            # list of radicates with the cmis id's
            radicate_list = Radicate.objects.annotate(search=vector).filter(search=query) | \
                            Radicate.objects.filter(cmis_id__in=cmis_id_list)

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as Error:
            raise

        return radicate_list

    @classmethod
    @get_params
    def get_thumbnail(cls, cmis_id):
        ''' Retrieve the thumbnail image based on the CMIS ID'''

        try:
            prev_response = requests.get(
                cls._params['ECM_PREVIEW_URL'].replace('{nodeId}', cmis_id), 
                auth=cls.get_basic_authentication())

            if prev_response.ok and prev_response.headers['Content-Type'] == "image/jpeg;charset=UTF-8":
                return prev_response

        except Exception as Err:
            logger.error(Err)

    @classmethod
    @get_params
    def create_record(cls, name):
        ''' '''

        try:
            r = requests.post(
                cls._params['ECM_RECORD_URL'], 
                data=json.dumps({"name": name, "nodeType": "cm:folder"}), 
                auth=cls.get_basic_authentication())

            if r.ok:
                json_response = (json.loads(r.text))
                return json_response['entry']['id']

        except Exception as Error:
            logger.error(Error)

    @classmethod
    @get_params
    def update_record(cls, id, name):
        ''' '''

        try:
            r = requests.put(
                cls._params['ECM_RECORD_UPDATE_URL'] + id, 
                data=json.dumps({"name": name}),
                auth=cls.get_basic_authentication())

            return r.ok

        except Exception as Error:
            logger.error(Error)

    @classmethod
    @get_params
    def assign_record(cls, id, record_id):
        ''' '''

        try:
            r = requests.post(
                cls._params['ECM_RECORD_ASSIGN_URL'] + id + '/move', 
                data=json.dumps({"targetParentId": record_id}),
                auth=cls.get_basic_authentication())

            return r.ok

        except Exception as Error:
            logger.error(Error)
        

    @classmethod
    @get_params
    def upload(cls, file):
        ''' '''

        try:

            res_upload = requests.post(
                cls._params['ECM_UPLOAD_URL'],
                files={"filedata": file},
                data={"nodeType": "cm:content"},
                auth=cls.get_basic_authentication())
            print(res_upload)
            print(res_upload.text)

            if res_upload.ok:  
                json_response = (json.loads(res_upload.text))
                return json_response['entry']['id']

        except Exception as Error:
            logger.error(Error)


    @classmethod
    @get_params
    def request_renditions(cls, node_id):
        ''' '''

        try:
            res_upload = requests.post(
                cls._params['ECM_REQUEST_RENDITIONS'].replace('{nodeId}', node_id),
                data='{"id": "imgpreview"}',
                auth=cls.get_basic_authentication())

            return res_upload.ok 

        except Exception as Error:
            logger.error(Error)
