# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


import json
import csv
from io import StringIO
from data_aggregator import utilities
from data_aggregator.dao import BaseDAO
from data_aggregator.models import Term
from data_aggregator.views.api import RESTDispatch
from django.conf import settings
from django.utils.decorators import method_decorator
from collections import OrderedDict
from uw_saml.decorators import group_required


@method_decorator(group_required(settings.DATA_AGGREGATOR_ACCESS_GROUP),
                  name='dispatch')
class BaseMetadataView(RESTDispatch):

    def parse_file_name(self, file_name):
        file_name = file_name.split("/")[-1]
        parts = file_name.split("-")
        sis_term_id = "-".join(parts[:2])
        upload_type = "-".join(parts[2:])
        upload_type = upload_type.split(".")[0]
        return sis_term_id, upload_type

    def get_full_file_path(self, file_name):
        _, upload_type = self.parse_file_name(file_name)
        if upload_type == "eop-advisers":
            return f"application_metadata/eop_advisers/{file_name}"
        elif upload_type == "iss-advisers":
            return f"application_metadata/iss_advisers/{file_name}"
        elif upload_type == "pred-proba":
            return f"application_metadata/predicted_probabilites/{file_name}"
        elif upload_type == "netid-name-stunum-categories":
            return f"application_metadata/student_categories/{file_name}"
        else:
            raise ValueError(f"Unable to determine upload type from filename: "
                             f"{file_name}")


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
            sis_term_id, upload_type = self.parse_file_name(file_name)
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
            url_key = self.get_full_file_path(new_file_name)
            content = request.FILES['upload'].\
                read().decode('utf-8').splitlines()
            # process file from bytestring to stringIO object for the
            # gcs blob upload_from_file method
            reader = csv.DictReader(content)
            output = StringIO()
            fieldnames = ['system_key', 'yrq', 'pred0', 'pred1']
            writer = csv.DictWriter(output,
                                    fieldnames,
                                    delimiter=',',
                                    quotechar='"', )
            writer.writeheader()
            for row in reader:
                writer.writerow(row)

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
            _, upload_type = self.parse_file_name(file_name)
            url_key = self.get_full_file_path(file_name)
            dao.delete_from_gcs_bucket(url_key)
            return self.json_response(content={"deleted": True})
        except Exception as e:
            return self.error_response(500, message=e)
