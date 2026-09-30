class LedgerError(Exception):
    """Base exception for all wallet/ledger invariant violations."""


class InsufficientFundsError(LedgerError):
    """Raised when a debit would push a wallet's balance below zero."""


class InvalidWalletTypeError(LedgerError):
    """Raised when an operation targets a wallet of the wrong wallet_type."""


class ServiceError(Exception):
    """
    A business-rule refusal raised by a service function (Part 2+).

    `code` is a stable, machine-readable snake_case reason (clients switch on
    it); `message` is a translated, human-readable explanation; `status` is
    the HTTP status the API layer should answer with. Views never build these
    responses by hand -- `core.exceptions_handler.api_exception_handler`
    converts any ServiceError into `{"code": ..., "detail": ...}`.
    """

    status = 400

    def __init__(self, code, message=None, *, status=None, extra=None):
        self.code = code
        self.message = str(message) if message is not None else code
        if status is not None:
            self.status = status
        self.extra = extra or {}
        super().__init__(f"{code}: {self.message}")


class DebitRefused(ServiceError):
    """Raised by `wallets.services.authorize_debit()` (or a caller of it) when
    a debit is not allowed. `code` is one of the documented reason codes:
    insufficient_funds, card_frozen, card_lost, daily_cap_exceeded,
    weekly_cap_exceeded, per_transaction_cap_exceeded, category_blocked,
    category_not_allowed, item_blocked, merchant_blocked, p2p_disabled,
    p2p_cap_exceeded."""

    status = 422
