import json
import logging
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.pipeline import llm
from app.services.pipeline.errors import PipelineError
from app.services.pipeline.reader import ReadResult

log = logging.getLogger(__name__)


class TitleItem(BaseModel):
    index: int = Field(description="Indice de l'expérience (0 = la première)")
    normalized_title: str = Field(description="Intitulé standardisé en français, sans entreprise ni niveau")


class InferredSkill(BaseModel):
    name: str
    experience_index: int = Field(description="Indice de l'expérience qui justifie cette compétence")
    evidence: str = Field(description="Courte justification tirée des missions de cette expérience")


class CVEnrichment(BaseModel):
    job_family: Literal[
        "software", "data_ai", "it_ops", "product_design", "finance_accounting", "hr", "sales_marketing",
        "operations", "engineering", "healthcare", "legal", "education", "admin_support", "other",
    ]
    titles: List[TitleItem] = Field(default_factory=list)
    inferred_skills: List[InferredSkill] = Field(default_factory=list)


TASK = (
    "Voici un CV sans identité. Renseigne : job_family (famille de métier principale) ; titles (pour chaque expérience, "
    "un intitulé standardisé, par exemple « Ingénieur data » ou « Comptable fournisseurs ») ; inferred_skills "
    "(compétences NON écrites telles quelles mais clairement impliquées par les missions décrites, 10 au maximum, "
    "avec l'expérience source et une justification courte). Ne répète aucune compétence déjà déclarée. "
    "N'invente rien et n'utilise jamais l'âge, le genre, la nationalité ni aucune autre caractéristique personnelle."
)


def enrich_cv(cv_input: dict) -> Optional[dict]:
    doc = ReadResult(mode="text", text=json.dumps(cv_input, ensure_ascii=False), pages=1)
    try:
        res = llm.call_tool(settings.LLM_MODEL_FAST, "enrich_cv", "Normalise le profil du CV", CVEnrichment, doc, TASK, 2000)
        return CVEnrichment.model_validate(res.data).model_dump()
    except (PipelineError, ValueError):
        log.warning("Enrichissement du CV impossible", exc_info=True)
        return None