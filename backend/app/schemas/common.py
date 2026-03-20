from datetime import datetime
from pydantic import BaseModel


class APIMessage(BaseModel):
    message: str
    ts: datetime = datetime.utcnow()
