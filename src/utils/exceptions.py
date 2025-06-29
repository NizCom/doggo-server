class MissingFieldsError(Exception):
    def __init__(self, missing_fields):
        self.missing_fields = {field.replace('_', ' ') for field in missing_fields}
        message = f"Missing required fields: {', '.join(self.missing_fields)}"
        super().__init__(message)


class DataNotFoundError(Exception):
    def __init__(self, table, column, data):
        self.table = table
        self.column = column
        self.data = data
        super().__init__(f"'{data}' was not found in table '{table}': [{column}].")


class ActiveActivityExistsError(Exception):
    def __init__(self, message="An active activity already exists for this dog."):
        self.message = message
        super().__init__(self.message)
