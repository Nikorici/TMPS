class PaymentDeclined(Exception):
    pass


class SoldOut(Exception):
    pass


class AccessDenied(Exception):
    pass


class InvalidTransition(Exception):
    pass
