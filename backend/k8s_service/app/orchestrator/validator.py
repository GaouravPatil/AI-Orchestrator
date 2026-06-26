class RequestValidator:

    @staticmethod
    def validate_namespace(namespace: str):

        if not namespace:
            raise ValueError("Namespace is required")

        return True

    @staticmethod
    def validate_name(name: str):

        if not name:
            raise ValueError("Resource name is required")

        return True