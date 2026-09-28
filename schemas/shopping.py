from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class PageInfo(BaseModel):
    limit: int
    offset: int
    count: int


class ParkingPlace(BaseModel):
    equipamento: str
    lugar: Optional[str] = None
    tipo: Optional[str] = None


class ParkingPlacesPage(PageInfo):
    items: list[ParkingPlace]


class HotspotAccess(BaseModel):
    id: Optional[int] = None
    dh_acesso: Optional[datetime] = None
    dt_acesso: Optional[date] = None
    hr_acesso: Optional[time] = None
    sexo: Optional[str] = None
    dt_nascimento: Optional[date] = None
    tp_aparelho: Optional[str] = None
    cep: Optional[str] = None
    uf: Optional[str] = None
    cidade: Optional[str] = None
    bairro: Optional[str] = None
    ar_influencia: Optional[str] = None
    id_lancamento: int | str
    cpf: Optional[str] = Field(
        None,
        description="CPF supplied by the hotspot source; confidential personal data",
    )


class HotspotAccessPage(PageInfo):
    items: list[HotspotAccess]


class PeopleAccess(BaseModel):
    id: int
    dt_acesso: date
    clima: Optional[str] = None
    entrada: Optional[str] = None
    pessoas: Optional[int] = None


class PeopleAccessPage(PageInfo):
    items: list[PeopleAccess]


class ParkingAccess(BaseModel):
    id: int
    tp_acesso: Optional[str] = None
    placa: Optional[str] = Field(
        None,
        description="Vehicle plate supplied by Per2Park; confidential data",
    )
    plano: Optional[str] = None
    tp_veiculo: Optional[str] = None
    dh_entrada: Optional[datetime] = None
    dt_entrada: Optional[date] = None
    hr_entrada: Optional[time] = None
    eq_entrada: Optional[str] = None
    entrada_local: Optional[ParkingPlace] = None
    dh_saida: Optional[datetime] = None
    dt_saida: Optional[date] = None
    hr_saida: Optional[time] = None
    eq_saida: Optional[str] = None
    saida_local: Optional[ParkingPlace] = None
    dh_pagamento: Optional[datetime] = None
    dt_pagamento: Optional[date] = None
    hr_pagamento: Optional[time] = None
    eq_pagamento: Optional[str] = None
    pagamento_local: Optional[ParkingPlace] = None
    vl_pagamento: Optional[Decimal] = None
    fr_pagamento: Optional[str] = None
    bandeira: Optional[str] = None
    mi_duracao: Optional[int] = None
    nm_voucher: Optional[str] = None
    dh_voucher: Optional[datetime] = None
    dt_voucher: Optional[date] = None
    hr_voucher: Optional[time] = None
    eq_voucher: Optional[str] = None
    voucher_local: Optional[ParkingPlace] = None


class ParkingAccessPage(PageInfo):
    items: list[ParkingAccess]


class ShoppingSale(BaseModel):
    id: int
    loja: str
    luc: str
    dt_referencia: date
    vl_vendido: Decimal
    categoria: str
    segmento: str
    classificacao: str


class ShoppingSalesPage(PageInfo):
    items: list[ShoppingSale]
