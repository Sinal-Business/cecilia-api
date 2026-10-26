from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, condecimal, model_validator


Money = condecimal(max_digits=18, decimal_places=2)


class FinancialCashRecord(BaseModel):
    lancamento: int = Field(..., description="Identificador unico do lancamento")
    empresa: str = Field(..., description="Empresa responsavel pelo lancamento")
    filial: str = Field(..., description="Filial responsavel pelo lancamento")
    co_contabilcod: Optional[str] = Field(None, description="Codigo da conta contabil original")
    co_contabil: Optional[str] = Field(None, description="Descricao da conta contabil original")
    co_contabilrecla: Optional[str] = Field(None, description="Conta contabil padronizada")
    cc_analiticocd: Optional[str] = Field(None, description="Codigo do centro de custo analitico")
    cc_analitico: Optional[str] = Field(None, description="Centro de custo analitico original")
    cc_analiticorecla: Optional[str] = Field(None, description="Centro de custo analitico padronizado")
    cc_sinteticonm: Optional[str] = Field(None, description="Centro de custo sintetico")
    fc_codigo: Optional[str] = Field(None, description="Codigo do fornecedor ou cliente")
    fc_nome: Optional[str] = Field(None, description="Nome original do fornecedor ou cliente")
    fc_nomerecla: Optional[str] = Field(None, description="Nome padronizado do fornecedor ou cliente")
    fc_nomesociedade: Optional[str] = Field(None, description="Grupo ou sociedade do fornecedor ou cliente")
    dat_emissao: Optional[date] = Field(None, description="Data de emissao")
    dat_vencimento: Optional[date] = Field(None, description="Data de vencimento")
    dat_pagamento: date = Field(..., description="Data de pagamento usada no filtro obrigatorio")
    dat_ano: int = Field(..., description="Ano contabil")
    dat_periodo: str = Field(..., description="Periodo contabil no formato YYYY-MM")
    vlr_bruto: Decimal = Field(..., description="Valor bruto")
    vlr_liquido: Decimal = Field(..., description="Valor liquido")
    vlr_titulo: Decimal = Field(..., description="Valor do titulo")
    vlr_pago: Decimal = Field(..., description="Valor pago")
    vlr_abs: Decimal = Field(..., description="Valor absoluto usado nas analises")
    descricao: Optional[str] = Field(None, description="Descricao do lancamento")
    tip_movimentacao: Optional[str] = Field(None, description="Tipo de movimentacao financeira")
    req_original: Optional[str] = Field(None, description="Codigo original da requisicao")
    req_acumulada: Optional[str] = Field(None, description="Requisicao consolidada ou corrigida")
    titulo: Optional[str] = Field(None, description="Numero ou identificador do titulo")
    pro_codigo: Optional[str] = Field(None, description="Codigo do projeto")
    pro_nome: Optional[str] = Field(None, description="Nome original do projeto")
    pro_nomerecla: Optional[str] = Field(None, description="Nome padronizado do projeto")
    cb_codigo: Optional[str] = Field(None, description="Codigo da conta bancaria")
    cb_completa: Optional[str] = Field(None, description="Descricao original da conta bancaria")
    cb_completarecla: Optional[str] = Field(None, description="Conta bancaria padronizada")
    pag_identificacao: Optional[str] = Field(None, description="Identificacao do pagamento")
    fcx_sintetico: Optional[str] = Field(None, description="Classificacao financeira sintetica")
    fcx_analitico: Optional[str] = Field(None, description="Classificacao financeira analitica")
    fcx_dretipo: Optional[str] = Field(None, description="Tipo de demonstracao de resultado")
    fcx_subgrupo: Optional[str] = Field(None, description="Subgrupo financeiro")
    gpa_reclassif: Optional[str] = Field(None, description="Classificacao geral")
    fcx_variacao: Optional[str] = Field(None, description="Tipagem ou variacao financeira")
    sis_origem: Optional[str] = Field(None, description="Sistema de origem")
    ult_alteracao: Optional[datetime] = Field(None, description="Data e hora da ultima alteracao")


class FinancialCashPage(BaseModel):
    items: list[FinancialCashRecord]
    limit: int
    offset: int
    count: int


class FinancialCashCreate(BaseModel):
    empresa: str = Field(..., min_length=1, max_length=70)
    filial: str = Field(..., min_length=1, max_length=70)
    co_contabilcod: Optional[str] = Field(None, max_length=10)
    co_contabil: Optional[str] = Field(None, max_length=50)
    co_contabilrecla: Optional[str] = Field(None, max_length=255)
    cc_analiticocd: Optional[str] = Field(None, max_length=7)
    cc_analitico: Optional[str] = Field(None, max_length=50)
    cc_analiticorecla: Optional[str] = Field(None, max_length=100)
    cc_sinteticonm: Optional[str] = Field(None, max_length=50)
    fc_codigo: Optional[str] = Field(None, max_length=15)
    fc_nome: Optional[str] = Field(None, max_length=255)
    fc_nomerecla: Optional[str] = Field(None, max_length=255)
    fc_nomesociedade: Optional[str] = Field(None, max_length=255)
    dat_emissao: Optional[date] = None
    dat_vencimento: Optional[date] = None
    dat_pagamento: date
    dat_ano: int = Field(..., ge=2000, le=2100)
    dat_periodo: str = Field(..., pattern=r"^\d{4}-\d{2}$", max_length=7)
    vlr_bruto: Money
    vlr_liquido: Money
    vlr_titulo: Money
    vlr_pago: Money
    vlr_abs: Money
    descricao: Optional[str] = Field(None, max_length=500)
    tip_movimentacao: Optional[str] = Field(None, max_length=50)
    req_original: Optional[str] = Field(None, max_length=6)
    req_acumulada: Optional[str] = Field(None, max_length=100)
    titulo: Optional[str] = Field(None, max_length=20)
    pro_codigo: Optional[str] = Field(None, max_length=100)
    pro_nome: Optional[str] = Field(None, max_length=255)
    pro_nomerecla: Optional[str] = Field(None, max_length=255)
    cb_codigo: Optional[str] = Field(None, max_length=10)
    cb_completa: Optional[str] = Field(None, max_length=30)
    cb_completarecla: Optional[str] = Field(None, max_length=255)
    pag_identificacao: Optional[str] = Field(None, max_length=500)
    fcx_sintetico: Optional[str] = Field(None, max_length=11)
    fcx_analitico: Optional[str] = Field(None, max_length=20)
    fcx_dretipo: Optional[str] = Field(None, max_length=20)
    fcx_subgrupo: Optional[str] = Field(None, max_length=30)
    gpa_reclassif: Optional[str] = Field(None, max_length=50)
    fcx_variacao: Optional[str] = Field(None, max_length=27)
    sis_origem: Optional[str] = Field(None, max_length=10)
    ult_alteracao: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_payment_period(self):
        if self.dat_ano != self.dat_pagamento.year:
            raise ValueError("dat_ano must match dat_pagamento year")
        if self.dat_periodo != self.dat_pagamento.strftime("%Y-%m"):
            raise ValueError("dat_periodo must match dat_pagamento month")
        return self

    model_config = ConfigDict(extra="forbid")


class FinancialCashBulkCreate(BaseModel):
    items: list[FinancialCashCreate] = Field(..., min_length=1, max_length=500)


class FinancialCashBulkCreateResponse(BaseModel):
    ok: bool
    inserted_count: int
    first_lancamento: int
    last_lancamento: int


class FinancialCashPatch(BaseModel):
    co_contabilrecla: Optional[str] = Field(None, max_length=255)
    cc_analiticorecla: Optional[str] = Field(None, max_length=100)
    cc_sinteticonm: Optional[str] = Field(None, max_length=50)
    fc_nomerecla: Optional[str] = Field(None, max_length=255)
    fc_nomesociedade: Optional[str] = Field(None, max_length=255)
    req_acumulada: Optional[str] = Field(None, max_length=100)
    pro_nomerecla: Optional[str] = Field(None, max_length=255)
    cb_completarecla: Optional[str] = Field(None, max_length=255)
    fcx_analitico: Optional[str] = Field(None, max_length=20)
    fcx_dretipo: Optional[str] = Field(None, max_length=20)
    fcx_subgrupo: Optional[str] = Field(None, max_length=30)
    gpa_reclassif: Optional[str] = Field(None, max_length=50)
    fcx_variacao: Optional[str] = Field(None, max_length=27)

    @model_validator(mode="before")
    @classmethod
    def reject_unsupported_fields(cls, value):
        if isinstance(value, dict):
            unsupported = sorted(set(value) - set(cls.model_fields))
            if unsupported:
                raise ValueError(
                    "Campos nao autorizados: "
                    + ", ".join(unsupported)
                    + ". Solicite a alteracao ao responsavel tecnico."
                )
        return value

    model_config = ConfigDict(extra="forbid")


class FinancialCashPatchResponse(BaseModel):
    ok: bool
    lancamento: int
    updated_fields: list[str]
    ult_alteracao: datetime
