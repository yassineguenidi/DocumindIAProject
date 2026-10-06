from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Experience(BaseModel):
    title: Optional[str] = Field(None, description="Intitulé du poste")
    company: Optional[str] = Field(None, description="Employeur ou client")
    location: Optional[str] = Field(None, description="Ville ou pays du poste")
    start_date: Optional[str] = Field(None, description="Début, format AAAA-MM (AAAA si le mois n'est pas indiqué)")
    end_date: Optional[str] = Field(None, description="Fin, format AAAA-MM (AAAA si le mois n'est pas indiqué) ; null si le poste est en cours")
    is_current: bool = Field(False, description="True si le poste est en cours (présent, aujourd'hui, en cours, current, present)")
    description: Optional[str] = Field(None, description="Missions et réalisations, résumées fidèlement, sans rien ajouter")


class Education(BaseModel):
    degree: Optional[str] = Field(None, description="Diplôme ou intitulé de la formation")
    field: Optional[str] = Field(None, description="Spécialité ou domaine")
    institution: Optional[str] = Field(None, description="École ou université")
    year: Optional[int] = Field(None, description="Année d'obtention ou de fin")


class Skill(BaseModel):
    name: str = Field(description="Compétence telle qu'écrite dans le CV")
    source: Literal["skills_section", "experience"] = Field(
        "skills_section",
        description="skills_section si elle figure dans une rubrique compétences, experience si elle n'apparaît que dans la description d'un poste",
    )


class SpokenLanguage(BaseModel):
    language: str
    level: Optional[str] = Field(None, description="Niveau tel qu'écrit (C1, courant, natif...)")


class Certification(BaseModel):
    name: str
    issuer: Optional[str] = None
    year: Optional[int] = None


class CVData(BaseModel):
    language: Optional[str] = Field(None, description="Langue principale du CV, code ISO 639-1 (fr, en...)")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    headline: Optional[str] = Field(None, description="Titre professionnel ou poste visé, tel qu'écrit")
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = Field(None, description="Ville et pays uniquement, jamais l'adresse complète")
    links: List[str] = Field(default_factory=list, description="LinkedIn, GitHub, site personnel...")
    summary: Optional[str] = Field(None, description="Résumé de profil, recopié fidèlement")
    experiences: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    languages: List[SpokenLanguage] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)