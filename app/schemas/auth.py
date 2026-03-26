from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    password: str
    is_admin: bool = False


class UsuarioResponse(BaseModel):
    id: str
    nome: str
    email: str
    is_active: bool
    is_admin: bool

    model_config = {"from_attributes": True}


class PerfilClienteResponse(BaseModel):
    cliente_id: str
    perfil: str


class MeResponse(BaseModel):
    id: str
    nome: str
    email: str
    is_active: bool
    is_admin: bool
    perfis: list[PerfilClienteResponse]
