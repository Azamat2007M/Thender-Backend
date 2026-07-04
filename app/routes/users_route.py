from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemes.user_scheme import UserResponse, UserCreate, UserUpdate
from app.crud import user as crud_user
from typing import List

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.get("/", response_model=List[UserResponse])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    users_data = await crud_user.get_users(db)
    return users_data

@router.get("/{user_id}", response_model=UserResponse)
async def get_users(user_id: int, db: AsyncSession = Depends(get_db)):
    db_user = await crud_user.get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return db_user

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await crud_user.create_user(db, user)

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update_body: UserUpdate, db: AsyncSession = Depends(get_db)):
    user_data = await crud_user.get_user_by_id(db, user_id)

    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return await crud_user.update_user(db, user_data, user_update_body)

@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user_data = await crud_user.get_user_by_id(db, user_id)

    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return await crud_user.delete_user(db, user_data)