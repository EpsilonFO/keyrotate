from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class APIKey(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    provider: str
    expires_at: date
    rotation_url: Optional[str] = None
    notify_days_before: str = "14,7,1"
    notify_channel: str = "email"
    status: str = "active"
    notes: Optional[str] = None
    notified_thresholds: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_rotated_at: Optional[datetime] = None

    def thresholds(self) -> list[int]:
        return sorted({int(x) for x in self.notify_days_before.split(",") if x.strip()}, reverse=True)

    def already_notified(self, threshold: int) -> bool:
        sent = {int(x) for x in self.notified_thresholds.split(",") if x.strip()}
        return threshold in sent

    def mark_notified(self, threshold: int) -> None:
        sent = {int(x) for x in self.notified_thresholds.split(",") if x.strip()}
        sent.add(threshold)
        self.notified_thresholds = ",".join(str(x) for x in sorted(sent))
