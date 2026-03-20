from pydantic import BaseModel


class CampaignCreate(BaseModel):
    id: str
    name: str
    goal: str
    segment_filter: dict


class CampaignApprove(BaseModel):
    approved_by: str


class CampaignDeploy(BaseModel):
    batch_limit: int = 200
    dry_run: bool = False
    cta_link: str = 'https://example.org/apply'
