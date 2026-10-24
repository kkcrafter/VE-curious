"""Reservation core: the only place that changes reservation state and calls hardware."""


class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def mask_plate(plate):
    # GDPR: plates of non-customers pass through events; log only a prefix [TEAM B6]
    return plate[:2] + "***" if plate else None
