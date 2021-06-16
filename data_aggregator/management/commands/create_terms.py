import logging
from django.core.management.base import BaseCommand
from data_aggregator.dao import BaseDAO
from data_aggregator.models import Term


class Command(BaseCommand):

    help = ("Creates current term and all future terms.")

    def add_arguments(self, parser):
        parser.add_argument("--sis_term_id",
                            type=str,
                            help=("Starting term to create entries for."),
                            default=None,
                            required=False)

    def handle(self, *args, **options):
        sis_term_id = options["sis_term_id"]

        sws_terms = BaseDAO().get_sws_terms(sis_term_id=sis_term_id)
        for sws_term in sws_terms:
            term, created = \
                Term.objects.get_or_create_from_sws_term(sws_term)
            if created:
                logging.info("Created term {}".format(term.sis_term_id))
