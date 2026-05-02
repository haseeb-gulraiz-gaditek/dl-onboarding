"""Pydantic shapes for the votes endpoint.

Per spec-delta communities-and-flat-comments F-COM-6, F-COM-7.
"""
from typing import Literal

from pydantic import BaseModel, Field


VoteTarget = Literal["post", "comment", "tool"]
VoteDirection = Literal[-1, 1]


class VoteRequest(BaseModel):
    """POST /api/votes body."""

    target_type: VoteTarget
    target_id: str
    direction: VoteDirection


class VoteResponse(BaseModel):
    voted: bool                  # True if there is a vote in place after the call
    current_direction: int       # -1, 0, 1
