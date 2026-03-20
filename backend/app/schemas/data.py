from pydantic import BaseModel, Field


class RegionalSkillIngestRow(BaseModel):
    state_code: str = Field(min_length=2, max_length=10)
    state_name: str
    district_code: str
    district_name: str
    youth_population: int = 0
    female_participation_rate: float = 0.0
    unemployment_rate: float = 0.0
    median_household_income: float = 0.0
    internet_penetration_rate: float = 0.0
    skill_gap_index: float = 0.0
    top_skills: list[str] = Field(default_factory=list)
    demand_skills: list[str] = Field(default_factory=list)
    source: str = 'manual_upload'


class RegionalSkillIngestRequest(BaseModel):
    rows: list[RegionalSkillIngestRow]
