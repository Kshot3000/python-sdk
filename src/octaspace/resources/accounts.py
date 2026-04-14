from __future__ import annotations

from ..response import APIResponse
from .base import Resource


class AccountsResource(Resource):
    def profile(self) -> APIResponse:
        return self.get("/accounts")

    def balance(self) -> APIResponse:
        return self.get("/accounts/balance")

    def generate_wallet(self) -> APIResponse:
        return self.post("/accounts")
