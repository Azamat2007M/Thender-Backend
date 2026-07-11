import jwt
import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, HTTPException, status, Cookie, UploadFile, File, Form, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, or_
from typing import List, Optional
from app.database import get_db
from app.config import settings
from app.models.user import UserModel
from app.models.thend import ThendModel, thend_likes
from app.schemas.thend_schema import SearchResultResponse, ThendResponse, ThendDetailResponse
from app.crud import thend as thend_crud
from app.crud.user import get_user_by_email
from app.schemas.comment_schema import CommentCreate, CommentResponse

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

router = APIRouter(
    prefix="/thends",
    tags=["Thends (Posts)"]
)

async def get_current_user(
    request: Request, 
    db: AsyncSession = Depends(get_db)
) -> UserModel:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    access_token = request.cookies.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing from cookies. Please log in."
        )

    try:
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = await get_user_by_email(db, email=email)
    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    return user


async def get_optional_current_user(
        access_token: Optional[str] = Cookie(None),
        db: AsyncSession = Depends(get_db)
) -> Optional[UserModel]:
    if not access_token:
        return None
    try:
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        user = await get_user_by_email(db, email=email)
        return user if user and user.is_active else None
    except jwt.PyJWTError:
        return None


@router.post("/", response_model=ThendResponse, status_code=status.HTTP_201_CREATED)
async def create_new_thend(
        content: str = Form(...),
        image: Optional[UploadFile] = File(None),
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    image_url = None

    if image:
        if image.content_type not in ["image/jpeg", "image/png", "image/webp", "image/gif"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid image format. Only JPEG, PNG, WEBP, GIF are allowed."
            )
        
        try:
            file_bytes = await image.read()
            upload_result = cloudinary.uploader.upload(
                file_bytes,
                folder="thender_posts"
            )
            image_url = upload_result.get("secure_url")
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image to cloud: {str(e)}"
            )

    thend_obj = await thend_crud.create_thend(
        db=db, 
        content=content, 
        author_id=current_user.id, 
        image_url=image_url
    )
    
    stmt = (
        select(ThendModel)
        .options(selectinload(ThendModel.author))
        .where(ThendModel.id == thend_obj.id)
    )
    res = await db.execute(stmt)
    thend_obj = res.scalar_one()

    thend_obj.is_liked = False
    thend_obj.likes_count = 0
    thend_obj.comments_count = 0
    
    return thend_obj


@router.get("/", response_model=List[ThendResponse])
async def read_global_thends_feed(
        skip: int = 0,
        limit: int = 7,
        db: AsyncSession = Depends(get_db),
        current_user: UserModel | None = Depends(get_optional_current_user)
):
    likes_subquery = (
        select(thend_likes.c.thend_id, func.count(thend_likes.c.user_id).label("total_likes"))
        .group_by(thend_likes.c.thend_id)
        .subquery()
    )

    stmt = (
        select(ThendModel)
        .outerjoin(likes_subquery, ThendModel.id == likes_subquery.c.thend_id)
        .options(
            selectinload(ThendModel.author),
            selectinload(ThendModel.liked_by_users),
            selectinload(ThendModel.comments)
        )
        .order_by(
            func.coalesce(likes_subquery.c.total_likes, 0).desc(),
            ThendModel.created_at.desc(),
            func.random() 
        )
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    thends = result.scalars().all()

    for thend in thends:
        thend.likes_count = len(thend.liked_by_users)
        thend.is_liked = any(user.id == current_user.id for user in thend.liked_by_users) if current_user else False
        thend.comments_count = len(thend.comments)

    return thends

@router.get("/search", response_model=SearchResultResponse) 
async def global_search_thends_and_channels(
        q: str = Query(...),
        tab: str = Query("posts"),
        db: AsyncSession = Depends(get_db),
        current_user: Optional[UserModel] = Depends(get_optional_current_user)
):
    if not q or not q.strip():
        return {"posts": [], "channels": []}

    stop_words = {"from", "about", "with", "the", "this", "that", "posts", "post", "для", "про", "от"}
    words = [w.strip() for w in q.split() if w.strip()]
    filtered_words = [w for w in words if w.lower() not in stop_words]
    search_tokens = filtered_words if filtered_words else words

    if not search_tokens:
        return {"posts": [], "channels": []}

    if tab != "channels":
        post_conditions = []
        for token in search_tokens:
            post_conditions.append(ThendModel.content.ilike(f"%{token}%"))
            post_conditions.append(UserModel.username.ilike(f"%{token}%"))

        stmt = (
            select(ThendModel)
            .join(UserModel, ThendModel.author_id == UserModel.id)
            .options(selectinload(ThendModel.author)) 
            .where(or_(*post_conditions))
            .order_by(ThendModel.created_at.desc())
            .limit(40)
        )
        result = await db.execute(stmt)
        thends = result.scalars().all()

        for thend in thends:
            thend.likes_count = 0
            thend.is_liked = False
            thend.comments_count = 0

        return {"posts": thends, "channels": []}

    else:
        user_conditions = [UserModel.username.ilike(f"%{token}%") for token in search_tokens]
        stmt = (
            select(UserModel)
            .where(or_(*user_conditions))
            .limit(25)
        )
        result = await db.execute(stmt)
        users = result.scalars().all()

        channels_data = []
        for user in users:
            channels_data.append({
                "id": user.id,
                "name": user.username,
                "is_active": user.is_active
            })

        return {"posts": [], "channels": channels_data}


@router.post("/{thend_id}/like", response_model=ThendResponse)
async def toggle_thend_like(
        thend_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    updated_thend = await thend_crud.toggle_like_thend(db=db, thend_id=thend_id, user_id=current_user.id)
    if not updated_thend:
        raise HTTPException(status_code=404, detail="Thend not found")

    db.expire(updated_thend)

    stmt = (
        select(ThendModel)
        .options(selectinload(ThendModel.author), selectinload(ThendModel.liked_by_users))
        .where(ThendModel.id == thend_id)
    )
    res = await db.execute(stmt)
    thend_obj = res.scalar_one()

    thend_obj.is_liked = any(user.id == current_user.id for user in thend_obj.liked_by_users)
    thend_obj.likes_count = len(thend_obj.liked_by_users)

    return thend_obj

@router.get("/me", response_model=List[ThendResponse])
async def read_my_thends(
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    stmt = (
        select(ThendModel)
        .options(
            selectinload(ThendModel.author),
            selectinload(ThendModel.liked_by_users),
            selectinload(ThendModel.comments)
        )
        .where(ThendModel.author_id == current_user.id)
        .order_by(ThendModel.created_at.desc())
    )
    result = await db.execute(stmt)
    thends = result.scalars().all()

    for thend in thends:
        thend.likes_count = len(thend.liked_by_users)
        thend.is_liked = any(user.id == current_user.id for user in thend.liked_by_users)
        thend.comments_count = len(thend.comments)

    return thends

@router.get("/liked", response_model=List[ThendResponse])
async def read_my_liked_thends(
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    stmt = (
        select(ThendModel)
        .join(ThendModel.liked_by_users)
        .options(
            selectinload(ThendModel.author),
            selectinload(ThendModel.liked_by_users),
            selectinload(ThendModel.comments)
        )
        .where(UserModel.id == current_user.id)
        .order_by(ThendModel.created_at.desc())
    )
    result = await db.execute(stmt)
    thends = result.scalars().all()

    for thend in thends:
        thend.likes_count = len(thend.liked_by_users)
        thend.is_liked = True
        thend.comments_count = len(thend.comments)

    return thends


@router.get("/{thend_id}", response_model=ThendDetailResponse)
async def read_single_thend(
        thend_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: UserModel | None = Depends(get_optional_current_user)
):
    thend = await thend_crud.get_thend_by_id(db, thend_id)
    if not thend:
        raise HTTPException(status_code=404, detail="Thend not found")

    thend.likes_count = len(thend.liked_by_users)
    thend.is_liked = any(user.id == current_user.id for user in thend.liked_by_users) if current_user else False

    thend.comments_count = len(thend.comments)

    return thend

@router.post("/{thend_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_thend_comment(
        thend_id: int,
        payload: CommentCreate,
        db: AsyncSession = Depends(get_db),
        current_user: UserModel = Depends(get_current_user)
):
    thend = await thend_crud.get_thend_by_id(db, thend_id)
    if not thend:
        raise HTTPException(status_code=404, detail="Thend not found")

    return await thend_crud.create_comment(
        db=db,
        comment_data=payload,
        thend_id=thend_id,
        author_id=current_user.id
    )


