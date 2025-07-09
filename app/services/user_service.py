from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User, UserPreference
from schemas.user import UserRegister, UserLogin, UserResponse, UserPreferences
from config.logger import logger
import secrets
import string
from typing import Optional
from datetime import datetime

class UserService:
    
    @staticmethod
    def generate_user_id() -> str:
        """Generate a unique 8-character user ID"""
        characters = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(characters) for _ in range(8))
   
    async def register_user(db: AsyncSession, user_data: UserRegister) -> UserResponse:
        """Register new user with 3 questions and generate user_id"""
        try:
            # Generate unique user_id
            user_id = UserService.generate_user_id()
            
            # Check if user_id already exists (very rare)
            while await UserService.get_user_by_id(db, user_id):
                user_id = UserService.generate_user_id()
            
            # Create new user
            new_user = User(
                user_id=user_id,
                monthly_income=user_data.monthly_income,
                savings_goal=user_data.savings_goal,
                target_amount=user_data.target_amount,
                target_date=user_data.target_date
            )
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            # Create default preferences
            default_preferences = UserPreference(
                user_id=user_id,
                preferences={
                    "default_categories": ["Food", "Transportation", "Entertainment", "Shopping", "Bills"],
                    "currency": "USD"
                }
            )
            
            db.add(default_preferences)
            await db.commit()
            
            logger.info(f"User registered successfully with ID: {user_id}")
            return UserResponse.model_validate(new_user)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error registering user: {e}")
            raise
   
    async def login_user(db: AsyncSession, login_data: UserLogin) -> Optional[UserResponse]:
        """Login existing user using UserLogin schema"""
        try:
            user = await UserService.get_user_by_id(db, login_data.user_id)
            if user:
                logger.info(f"User logged in: {login_data.user_id}")
                return UserResponse.model_validate(user)
            else:
                logger.warning(f"Login attempt with invalid user_id: {login_data.user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            raise
    
    
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by user_id"""
        try:
            result = await db.execute(select(User).where(User.user_id == user_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            raise
    
    
    async def get_user_preferences(db: AsyncSession, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences"""
        try:
            result = await db.execute(
                select(UserPreference).where(UserPreference.user_id == user_id)
            )
            user_pref = result.scalar_one_or_none()
            
            if user_pref:
                return UserPreferences.model_validate(user_pref)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching preferences for user {user_id}: {e}")
            raise
    
    
    async def update_user_preferences(db: AsyncSession, user_id: str, preferences_data: dict) -> UserPreferences:
        """Update user preferences"""
        try:
            result = await db.execute(
                select(UserPreference).where(UserPreference.user_id == user_id)
            )
            user_pref = result.scalar_one_or_none()
            
            if user_pref:
                user_pref.preferences.update(preferences_data)
                user_pref.updated_at = datetime.utcnow()
            else:
                user_pref = UserPreference(
                    user_id=user_id,
                    preferences=preferences_data
                )
                db.add(user_pref)
            
            await db.commit()
            await db.refresh(user_pref)
            
            logger.info(f"Preferences updated for user: {user_id}")
            return UserPreferences.model_validate(user_pref)
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating preferences for user {user_id}: {e}")
            raise