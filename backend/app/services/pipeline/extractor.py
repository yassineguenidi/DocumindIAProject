import logging
from dataclasses import dataclass
from typing import List

from pydantic import ValidationError

from app.core.config import settings
from app.services.pipeline import llm
from app.services.pipeline.errors import PipelineError
from app.services.pipeline.reader import ReadResult
from app.services.pipeline.registry import DocTypeDef

log = logging.getLogger(__name__)


@dataclass
class Extraction:
    data: dict
    issues: List[dict]
    meta: dict


def _errors(issues: List[dict]) -> int:
    return sum(1 for i in issues if i["severity"] == "error")


def extract(defn: DocTypeDef, doc: ReadResult) -> Extraction:
    task = f"Extrais les informations de ce document ({defn.label}). {defn.instructions}"

    plan = [(settings.LLM_MODEL_FAST, 4096)]
    if settings.LLM_MODEL_STRONG and settings.LLM_MODEL_STRONG != settings.LLM_MODEL_FAST:
        plan.append((settings.LLM_MODEL_STRONG, 8192))

    attempts, last_error, tokens_in, tokens_out, models = [], None, 0, 0, []
    for model, max_tokens in plan:
        models.append(model)
        try:
            res = llm.call_tool(model, "record_document", f"Enregistre les données de la {defn.label}",
                                defn.schema, doc, task, max_tokens)
            tokens_in += res.input_tokens
            tokens_out += res.output_tokens
            data = defn.schema.model_validate(res.data).model_dump()
        except (PipelineError, ValidationError) as exc:
            log.warning("Tentative échouée avec %s : %s", model, exc)
            last_error = exc
            continue
        # issues = defn.validate(data)
        issues = defn.validate(data, doc.text) 
        attempts.append((data, issues))
        if _errors(issues) == 0:
            break  # contrôles satisfaisants : pas besoin du modèle suivant

    if not attempts:
        raise last_error if isinstance(last_error, PipelineError) else PipelineError("Résultat inexploitable")

    data, issues = min(reversed(attempts), key=lambda a: _errors(a[1]))  # à égalité, on préfère le dernier
    if defn.enrich:                                      # ← à ajouter juste après
        data["derived"] = defn.enrich(data)
    meta = {
        "provider": settings.LLM_PROVIDER, "mode": doc.mode, "pages": doc.pages, "models": models,
        "escalated": len(models) > 1, "input_tokens": tokens_in, "output_tokens": tokens_out,
    }
    return Extraction(data, issues, meta)


# import logging
# from dataclasses import dataclass
# from typing import List

# from pydantic import ValidationError

# from app.core.config import settings
# from app.services.pipeline import llm
# from app.services.pipeline.errors import PipelineError
# from app.services.pipeline.reader import ReadResult
# from app.services.pipeline.registry import DocTypeDef

# log = logging.getLogger(__name__)


# @dataclass
# class Extraction:
#     data: dict
#     issues: List[dict]
#     meta: dict


# def _errors(issues: List[dict]) -> int:
#     return sum(1 for i in issues if i["severity"] == "error")


# def extract(defn: DocTypeDef, doc: ReadResult) -> Extraction:
#     schema = defn.schema.model_json_schema()
#     task = f"Extrais les informations de ce document ({defn.label}). {defn.instructions}"
#     attempts, last_error, tokens_in, tokens_out, models = [], None, 0, 0, []

#     for model, max_tokens in ((settings.LLM_MODEL_FAST, 4096), (settings.LLM_MODEL_STRONG, 8192)):
#         models.append(model)
#         try:
#             res = llm.call_tool(model, "record_document", f"Enregistre les données de la {defn.label}",
#                                 schema, doc, task, max_tokens)
#             tokens_in += res.input_tokens
#             tokens_out += res.output_tokens
#             data = defn.schema.model_validate(res.data).model_dump()
#         except (PipelineError, ValidationError) as exc:
#             log.warning("Tentative échouée avec %s : %s", model, exc)
#             last_error = exc
#             continue
#         issues = defn.validate(data)
#         attempts.append((data, issues))
#         if _errors(issues) == 0:
#             break  # contrôles satisfaisants : pas besoin du modèle puissant

#     if not attempts:
#         raise last_error if isinstance(last_error, PipelineError) else PipelineError("Résultat inexploitable")

#     data, issues = min(reversed(attempts), key=lambda a: _errors(a[1]))  # à égalité, on préfère le dernier
#     meta = {
#         "mode": doc.mode, "pages": doc.pages, "models": models, "escalated": len(models) > 1,
#         "input_tokens": tokens_in, "output_tokens": tokens_out,
#     }
#     return Extraction(data, issues, meta)