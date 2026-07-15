from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router

app = FastAPI(title="AdsControl IA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # ajustar con el dominio de Vercel en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
