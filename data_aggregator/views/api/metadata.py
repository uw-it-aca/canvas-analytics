# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import json
from data_aggregator import utilities
from data_aggregator.dao import BaseDAO
from data_aggregator.models import Term
from data_aggregator.views.api import RESTDispatch
from data_aggregator.utilities import parse_metadata_file_name, \
    get_full_metadata_file_path
from django.conf import settings
from django.utils.decorators import method_decorator
from collections import OrderedDict
from uw_saml.decorators import group_required


@method_decorator(group_required(settings.DATA_AGGREGATOR_ACCESS_GROUP),
                  name='dispatch')
class BaseMetadataView(RESTDispatch):
    pass


class MetadataFileListView(BaseMetadataView):
    '''
    API endpoint get list of metadata files

    /api/internal/metadata/
    '''

    def get_metadata_files_dict(self):
        dao = BaseDAO()
        files = dao.get_filenames_from_gcs_bucket(
            'application_metadata/'
        )
        metadata_files = {}
        for term in Term.objects.all():
            metadata_files[term.sis_term_id] = {}
        for file_path in files:
            file_name = file_path.split("/")[-1]
            sis_term_id, week, upload_type = parse_metadata_file_name(file_name)
            if sis_term_id not in metadata_files:
                metadata_files[sis_term_id] = {}
            metadata_files[sis_term_id][upload_type] = {
                'file_name': file_name
            }
        metadata_files = OrderedDict(sorted(
            metadata_files.items(),
            key=lambda item: utilities.get_sortable_term_id(item[0])
        ))
        return metadata_files

    def post(self, request, *args, **kwargs):
        metadata_files = self.get_metadata_files_dict()
        return self.json_response(content={"metadata_files": metadata_files})


class MetadataFileUploadView(BaseMetadataView):
    '''
    API endpoint to upload a metadata file

    /api/internal/metadata/upload/
    '''

    def post(self, request, *args, **kwargs):
        try:
            dao = BaseDAO()
            new_file_name = request.POST["newFileName"]
            url_key = get_full_metadata_file_path(new_file_name)
            content = request.FILES['upload']
            dao.upload_to_gcs_bucket(url_key, content)
            return self.json_response(content={"uploaded": True})
        except Exception as e:
            return self.error_response(500, message=e)


class MetadataFileDeleteView(BaseMetadataView):
    '''
    API endpoint to delete a metadata file

    /api/internal/metadata/delete/
    '''

    def post(self, request, *args, **kwargs):
        try:
            dao = BaseDAO()
            data = json.loads(request.body.decode('utf-8'))
            file_name = data["file_name"]
            url_key = get_full_metadata_file_path(file_name)
            dao.delete_from_gcs_bucket(url_key)
            return self.json_response(content={"deleted": True})
        except Exception as e:
            return self.error_response(500, message=e)
