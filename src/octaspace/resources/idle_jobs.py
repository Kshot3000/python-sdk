from __future__ import annotations

from ..response import APIResponse
from .base import Resource


class IdleJobsResource(Resource):
    def find(self, *, node_id: int | str, job_id: int | str) -> APIResponse:
        return self.get(f"/idle_jobs/{self.encode(node_id)}/{self.encode(job_id)}")

    def logs(self, *, node_id: int | str, job_id: int | str) -> APIResponse:
        return self.get(f"/idle_jobs/{self.encode(node_id)}/{self.encode(job_id)}/logs")
