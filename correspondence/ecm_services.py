import requests
from requests.auth import HTTPBasicAuth
from django.contrib.postgres.search import SearchVector, SearchQuery
from correspondence.models import Radicate
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
            #if not ECMService._params:
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

            if prev_response.ok and prev_response.headers['Content-Type'].startswith("image/"):
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
    def move_item(cls, cmis_id, target):
        ''' '''

        try:
            r = requests.post(
                cls._params['ECM_MOVE_URL'].replace('{nodeId}', cmis_id), 
                data=json.dumps({"targetParentId": target}), 
                auth=cls.get_basic_authentication())

            if r.ok:
                json_response = (json.loads(r.text))
                return json_response['entry']['id']

        except Exception as Error:
            logger.error(Error)

    @classmethod
    @get_params
    def copy_item(cls, cmis_id, target):
        ''' '''
        try:
            r = requests.post(
                cls._params['ECM_COPY_URL'].replace('{nodeId}', cmis_id), 
                data=json.dumps({"targetParentId": target}), 
                auth=cls.get_basic_authentication())

            if r.ok:
                json_response = (json.loads(r.text))
                return json_response['entry']['id']

        except Exception as Error:
            logger.error(Error)

    @classmethod
    @get_params
    def create_folder(cls, cmis_id, name):
        ''' '''

        try:
            print(name)
            r = requests.post(
                cls._params['ECM_FOLDER_URL'].replace('{nodeId}', cmis_id), 
                data=json.dumps({"name": name, "nodeType": "cm:folder"}), 
                auth=cls.get_basic_authentication())
            print(r.__dict__)
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
    def upload(cls, file, folder_id, name=None):
        ''' Upload file to ECM'''

        try:
            if name:
                data = {"nodeType": "cm:content", "autoRename": "true", "name": name}
            else:
                data = {"nodeType": "cm:content", "autoRename": "true"}
            res_upload = requests.post(
                cls._params['ECM_UPLOAD_URL'].replace('{nodeId}', folder_id),
                files={"filedata": file},
                data=data,
                auth=cls.get_basic_authentication())
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

    @classmethod
    @get_params
    def download(cls, node_id):
        ''' Download file from ECM'''

        try:
            res = requests.get(
                cls._params['ECM_DOWNLOAD_URL'].replace('{nodeId}', node_id),
                auth=cls.get_basic_authentication())
 
            if res.ok: 
                return res.content, res.headers['content-disposition']

        except Exception as Error:
            logger.error(Error)
