from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, busca, homologacao, servicos

router = APIRouter()

router.include_router(auth.router)
router.include_router(busca.router)
router.include_router(servicos.router)
router.include_router(homologacao.router)
router.include_router(admin.router)
