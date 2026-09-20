class LedgerError(Exception):
    """Base exception for all wallet/ledger invariant violations."""


class InsufficientFundsError(LedgerError):
    """Raised when a debit would push a wallet's balance below zero."""


class InvalidWalletTypeError(LedgerError):
    """Raised when an operation targets a wallet of the wrong wallet_type."""
