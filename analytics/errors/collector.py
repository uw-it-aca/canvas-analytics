

class ErrorCollector(object):
    errors = []
    def add_error(self, error_msg):
        ErrorCollector.errors.append(error_msg)

    def get_errors(self):
        return ErrorCollector.errors
