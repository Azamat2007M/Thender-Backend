from fastapi import FastAPI
from app.database import engine, Base
from app.routes.users_route import router as user_router
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()

app = FastAPI(
    title="My FastAPI Project",
    description="My FastAPI project for crud operation.",
    lifespan=lifespan,
)

origins = [
    "http://localhost:3000",      # Стандартный адрес для локального React приложения
    "http://127.0.0.1:3000",    # Он же, но через IP
    "http://localhost:5173",      # Стандартный адрес для Vite (React/Vue)
    # Сюда же потом добавишь боевой адрес своего фронтенда, когда выкатишь в интернет
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
async def root():
    return {'message': 'Hello World'}

app.include_router(user_router)