
import logging
from django.db import transaction
from csv import DictReader
from django.core.management.base import BaseCommand
from data_aggregator.models import User
from data_aggregator.dao import CanvasDAO
from uw_pws import PWS


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


class Command(BaseCommand):

    help = ("Loads or updates list of students for the current term.")

    def add_arguments(self, parser):
        parser.add_argument("--sis_term_id",
                            type=str,
                            help=("Term to update users for."),
                            default=None,
                            required=False)

    @transaction.atomic
    def create_users(self, users, batch_size=100):
        if users:
            User.objects.bulk_create(users, batch_size=batch_size)
            print("Created {} user(s)".format(len(users)))

    @transaction.atomic
    def update_users(self, users, batch_size=100):
        if users:
            User.objects.bulk_update(
                users,
                ["login_id", "sis_user_id", "first_name",
                 "last_name", "full_name", "sortable_name",
                 "email", "status"],
                batch_size=batch_size)
            print("Updated {} user(s)".format(len(users)))

    def handle(self, *args, **options):
        sis_term_id = options["sis_term_id"]

        cd = CanvasDAO(sis_term_id=sis_term_id)
        # get provising data and load courses
        sis_data = cd.download_user_provisioning_report()
        user_count = 0
        update = {}
        create = {}

        logging.info(f"Parsing Canvas user provisioning report "
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
                    create[user.canvas_user_id] = user
                else:
                    update[user.canvas_user_id] = user
                user_count += 1
        for users in chunker(list(create.values()), 1000):
            self.create_users(users)
        for users in chunker(list(update.values()), 1000):
            self.update_users(users)
        logging.info('Finished creating / updating users')
