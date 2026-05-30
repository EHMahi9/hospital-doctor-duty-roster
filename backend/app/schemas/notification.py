from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import NotificationChannel, NotificationStatus


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    title: str
    message: str
    channel: NotificationChannel
    status: NotificationStatus
    scheduled_at: datetime | None
    sent_at: datetime | None
    created_at: datetime


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int | None
    action: str
    entity_type: str
    entity_id: str | None
    metadata_json: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime
