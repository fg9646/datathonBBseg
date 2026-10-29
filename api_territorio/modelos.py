"""Modelos da interface 1.0.0, separados da camada de persistência."""
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .validadores import MAX_CONSULTAS, validar_estado_valor, validar_periodo


class Modelo(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


class Periodo(Modelo):
    inicio: str
    fim: str

    @model_validator(mode='after')
    def validar(self) -> "Periodo":
        validar_periodo(self.model_dump())
        return self


class Consulta(Modelo):
    indicador: Annotated[str, Field(min_length=1, max_length=128)]
    periodo: Periodo | None = None

    @model_validator(mode='before')
    @classmethod
    def sem_null(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get('periodo', False) is None:
            raise ValueError('Período deve ser omitido ou informado por completo.')
        return data


class Pedido(Modelo):
    codigo_ibge: Annotated[str, Field(pattern=r'^[0-9]{7}$')]
    versao_base: Annotated[str, Field(min_length=1, max_length=128)] | None = None
    consultas: Annotated[list[Consulta], Field(min_length=1, max_length=MAX_CONSULTAS)] | None = None

    @model_validator(mode='before')
    @classmethod
    def sem_null(cls, data: Any) -> Any:
        if isinstance(data, dict) and any(k in data and data[k] is None for k in ['versao_base', 'consultas']):
            raise ValueError('Campos opcionais devem ser omitidos ou preenchidos.')
        return data


class Fonte(Modelo):
    instituicao: str
    url: str
    coletado_em: str


class Estacao(Modelo):
    codigo: str
    nome: str


class Cobertura(Modelo):
    numerador: Annotated[int, Field(ge=0)]
    denominador: Annotated[int, Field(gt=0)]
    proporcao: Annotated[float, Field(ge=0, le=1)]
    unidade: Literal['dias']


class Indicador(Modelo):
    id: str
    valor: int | float | None
    unidade: Literal[
        'mm/ano', 'dias/ano', '°C', 'fracao', 'km/h', 'protocolos',
        'ocorrencias', 'ocorrencias/100mil_habitantes',
    ]
    periodo: Periodo
    disponibilidade: Literal['DISPONIVEL', 'AUSENTE']
    motivo_ausencia: Literal[
        'FONTE_SEM_VALOR', 'SEM_RECORTE_RESIDENCIAL',
        'SEM_COBERTURA_TERRITORIAL', 'PERIODO_NAO_DISPONIVEL',
    ] | None
    fontes: list[Fonte]
    metodo: str
    estacao: Estacao | None
    cobertura: Cobertura | None
    limitacoes: list[str]

    @model_validator(mode='after')
    def ausencia_coerente(self) -> "Indicador":
        validar_estado_valor(self.valor, self.disponibilidade, self.motivo_ausencia)
        return self


class Territorio(Modelo):
    codigo_ibge: Annotated[str, Field(pattern=r'^[0-9]{7}$')]
    municipio: str
    uf: str
    abrangencia: Literal['municipio', 'distrito_federal']


class Atualizacao(Modelo):
    ultima_coleta_em: str | None
    situacao: Literal['SEM_FALHA_REGISTRADA', 'FALHA_NA_ULTIMA_TENTATIVA']


class RespostaConsulta(Modelo):
    versao_contrato: Literal['1.0.0']
    versao_base: str
    consultado_em: str
    territorio: Territorio
    atualizacao: Atualizacao
    indicadores: list[Indicador]


class DetalheErro(Modelo):
    codigo: str
    mensagem: str


class RespostaErro(Modelo):
    erro: DetalheErro
