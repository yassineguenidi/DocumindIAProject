from typing import List, Optional

from pydantic import BaseModel, Field


class JobCriteria(BaseModel):
    title: Optional[str] = Field(None, description="Intitulé du poste")
    must_have: List[str] = Field(default_factory=list, description="Compétences, outils ou qualifications indispensables, une par entrée")
    nice_to_have: List[str] = Field(default_factory=list, description="Atouts souhaités mais non indispensables")
    min_years: Optional[float] = Field(None, description="Années d'expérience minimales demandées")
    languages: List[str] = Field(default_factory=list, description="Langues exigées")


class JobTextRequest(BaseModel):
    text: str = Field(min_length=20, max_length=20000)


class MatchRequest(BaseModel):
    criteria: JobCriteria
    job_text: str = Field("", max_length=20000)
    anonymous: bool = False