from datetime import datetime


class AuditLogger:

    @staticmethod
    def log(action: str, resource: str):

        print(
            f"[{datetime.utcnow()}] "
            f"{action} -> {resource}"
        )