from fastapi import FastAPI
from app.database import engine, Base
from app.routes.users_route import router as user_router
from app.routes.auth_route import router as auth_router
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.telegram_bot.support import router as telegram_router
from app.routes.thends_route import router as thends_router
from app.routes.chats_route import router as chats_router
from app.models.user import UserModel
from app.models.thend import ThendModel
from app.models.comment import CommentModel

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
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "https://thender-frontend.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0", "web", "thender-backend.onrender.com"]
)

@app.get('/')
async def root():
    return {'message': 'Hello World'}

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(telegram_router)
app.include_router(thends_router)
app.include_router(chats_router)