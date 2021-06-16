from data_aggregator.management.commands._base import CreateDBViewCommand
from data_aggregator.dao import TaskDAO


class Command(CreateDBViewCommand):

    help = ("Creates assignment db view for given week.")

    def create(self, sis_term_id, week):
        TaskDAO().create_assignment_db_view(sis_term_id, week)
