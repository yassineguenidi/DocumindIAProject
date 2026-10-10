from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class InvoiceLine(BaseModel):
    description: Optional[str] = Field(None, description="Désignation de la ligne")
    quantity: Optional[float] = None
    unit_price: Optional[float] = Field(None, description="Prix unitaire HT")
    vat_rate: Optional[float] = Field(None, description="Taux de TVA en pourcentage (20 pour 20 %)")
    total_ht: Optional[float] = Field(None, description="Total HT de la ligne")


class VatBreakdown(BaseModel):
    rate: Optional[float] = Field(None, description="Taux de TVA en pourcentage")
    base: Optional[float] = Field(None, description="Base HT soumise à ce taux")
    amount: Optional[float] = Field(None, description="Montant de TVA pour ce taux")


class InvoiceData(BaseModel):
    document_kind: Literal["invoice", "credit_note"] = Field("invoice", description="credit_note pour un avoir")
    language: Optional[str] = Field(None, description="Langue principale du document, code ISO 639-1 (fr, en...)")
    supplier_name: Optional[str] = Field(None, description="Émetteur de la facture")
    supplier_address: Optional[str] = None
    supplier_siret: Optional[str] = Field(None, description="SIRET du fournisseur (14 chiffres)")
    supplier_vat_number: Optional[str] = Field(None, description="N° de TVA intracommunautaire du fournisseur")
    customer_name: Optional[str] = Field(None, description="Destinataire de la facture")
    customer_siren: Optional[str] = Field(None, description="SIREN du client (9 chiffres), s'il est indiqué")
    invoice_number: Optional[str] = None
    purchase_order_ref: Optional[str] = Field(None, description="Référence de commande ou de bon de commande citée sur la facture")
    invoice_date: Optional[str] = Field(None, description="Date de facture, format AAAA-MM-JJ")
    due_date: Optional[str] = Field(None, description="Date d'échéance, format AAAA-MM-JJ")
    currency: Optional[str] = Field(None, description="Code ISO, par exemple EUR")
    total_ht: Optional[float] = None
    total_vat: Optional[float] = None
    total_ttc: Optional[float] = None
    iban: Optional[str] = Field(None, description="IBAN de paiement indiqué sur la facture")
    lines: List[InvoiceLine] = Field(default_factory=list, description="Une entrée par article ou prestation")
    vat_breakdown: List[VatBreakdown] = Field(default_factory=list, description="Une entrée par taux de TVA du récapitulatif")