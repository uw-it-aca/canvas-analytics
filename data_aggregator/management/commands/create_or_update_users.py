
import logging
from django.db import transaction
from csv import DictReader, reader
from django.core.management.base import BaseCommand
from data_aggregator.models import User
from data_aggregator.dao import CanvasDAO
from uw_sws.term import get_current_term
from uw_pws import PWS


class Command(BaseCommand):

    help = ("Loads or updates list of students for the current term.")

    @transaction.atomic
    def create_users(self, users, batch_size=1000):
        User.objects.bulk_create(users, batch_size=batch_size)

    @transaction.atomic
    def update_users(self, users, batch_size=1000):
        User.objects.bulk_update(
            users,
            ["login_id", "sis_user_id", "first_name",
             "last_name", "full_name", "sortable_name",
             "short_name", "email", "status"],
            batch_size=batch_size)

    def handle(self, *args, **options):
        self.logger = logging.getLogger(__name__)

        # get the current term object from sws
        sws_term = get_current_term()
        # get provising data and load courses
        sis_data = CanvasDAO().get_canvas_user_provisioning_report(
            sws_term.canvas_sis_id())
        user_count = 0
        updated = {}
        created = {}

        self.logger.info(f"Parsing Canvas user provisioning report "
                         f"containing {len(sis_data)} rows.")

        pws = PWS()
        existing_users = {}
        for user in User.objects.all():
            existing_users[int(user.canvas_user_id)] = user
        for row in DictReader(sis_data):
            if not len(row):
                continue
            created_by_sis = row['created_by_sis']
            status = row['status']
            sis_user_id = row['user_id']
            if created_by_sis == "true" and status == "active" and \
                    pws.valid_uwregid(sis_user_id):
                # we need to cast the canvas_user_id from the file to an int
                # so that the dictionary lookup works
                canvas_user_id = int(row['canvas_user_id'])
                user = existing_users.get(canvas_user_id)
                if user:
                    new_user = False
                else:
                    user = User()
                    user.canvas_user_id = canvas_user_id
                    new_user = True

                user.sis_user_id = sis_user_id
                user.login_id = row['login_id']
                user.first_name = row['first_name']
                user.last_name = row['last_name']
                user.full_name = row['full_name']
                user.sortable_name = row['sortable_name']
                user.email = row['email']
                user.status = status
                if new_user:
                    created[user.canvas_user_id] = user
                else:
                    updated[user.canvas_user_id] = user
                user_count += 1
        self.create_users(created.values())
        print("Created {} users".format(len(created)))
        self.update_users(updated.values())
        print("Updated {} users".format(len(updated)))
        self.logger.info('Finished creating / updating users')
