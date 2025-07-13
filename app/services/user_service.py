from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
import string
from typing import Optional
from datetime import datetime
from config.logger import logger
from database.models import User, UserPreference
from schemas.user import UserRegister, UserLogin, UserResponse, UserPreferences

class UserService:
    
    def generate_user_id(self) -> str:
        """Generate a unique 8-character user ID"""
        characters = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(characters) for _ in range(8))
   
    async def register_user(self, db: AsyncSession, user_data: UserRegister) -> UserResponse:
        """Register new user with 3 questions and generate user_id"""
        try:
            user_id = self.generate_user_id()

            while await self.get_user_by_id(db, user_id):
                user_id = self.generate_user_id()
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

    async def login_user(self, db: AsyncSession, login_data: UserLogin) -> Optional[UserResponse]:
        """Login existing user using UserLogin schema"""
        try:
            user = await self.get_user_by_id(db, login_data.user_id)
            if user:
                logger.info(f"User logged in: {login_data.user_id}")
                return UserResponse.model_validate(user)
            else:
                logger.warning(f"Login attempt with invalid user_id: {login_data.user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            raise
    
    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        try:
            result = await db.execute(select(User).where(User.user_id == user_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            raise
    
    async def get_user_preferences(self, db: AsyncSession, user_id: str) -> Optional[UserPreferences]:
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
    
    async def update_user_preferences(self, db: AsyncSession, user_id: str, preferences_data: dict) -> UserPreferences:
        try:
            result = await db.execute( select(UserPreference).where(UserPreference.user_id == user_id) )
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
        
    async def user_exists(self, db: AsyncSession, user_id: str) -> bool:
        try:
            user = await self.get_user_by_id(db, user_id)
            return user is not None
        except Exception as e:
            logger.error(f"Error checking user existence for {user_id}: {e}")
            return False