from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.user import UserRegister, UserLogin, UserResponse, UserPreferences
from schemas.transaction import NaturalLanguageInput, TransactionResponse, TransactionSearch
from schemas.analysis import FinancialInsights
from services.user_service import UserService
from services.workflow import FinanceWorkflow
from database.database import get_db
from typing import Dict, List

router= APIRouter(prefix="/api", tags=['Finance'])

workflow = FinanceWorkflow()
user_service = UserService()

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    try:
        result= await UserService().register_user(db, user_data) 
        return result
    except HTTPException as e:
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/login", response_model= UserResponse)
async def login_user(login_data: UserLogin, db: AsyncSession = Depends(get_db)) :
    result = await user_service.login_user(db, login_data)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user_id")
    return result

@router.post("/preferences", response_model= UserPreferences)
async def update_preferences(user_id: str, preferences_data: Dict, db: AsyncSession = Depends(get_db)):
    try:
        result = await user_service.update_user_preferences(db, user_id, preferences_data)
        return result
    except Exception as e:
        raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.get("/user/{user_id}", response_model= UserResponse)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user= await user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)

router.post("/transactions", response_model= TransactionResponse)
async def create_transaction(input_data: NaturalLanguageInput, db: AsyncSession= Depends(get_db)):
    return await workflow.process_transaction(db, input_data)

@router.get("/search", response_model= List[TransactionResponse])
async def search_transactions(user_id: str, query: str, db: AsyncSession = Depends(get_db)):
    search_data = TransactionSearch(user_id=user_id, query=query)
    return await workflow.search_transactions(db, search_data)

@router.get("/insights/{user_id}", response_model= FinancialInsights)
async def get_financial_insights(user_id: str, period: str = "this month", db: AsyncSession = Depends(get_db)):
    
    return await workflow.generate_financial_insights(db, user_id, period)