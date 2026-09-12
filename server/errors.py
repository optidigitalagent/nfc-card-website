"""Redacted client-safe validation error shared by current and legacy contracts."""


class LeadError(Exception):
    def __init__(self, status, code, fields=None):
        self.status = status
        self.code = code
        self.fields = fields or {}
        super().__init__(code)
