from datetime import datetime


class ApiResponse:

    @staticmethod
    def success(message: str, data=None):

        return {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def error(message: str):

        return {
            "success": False,
            "message": message,
            "data": None,
            "timestamp": datetime.utcnow().isoformat(),
        }