import logging
from typing import Optional, Tuple

from src import app_manager
from src.modules.database import User
from src.utils.security import check_password, generate_jwt_token

logger = logging.getLogger(__name__)

user_db = User(app_manager.get_database_instance())


def authenticate(username: str, password: str) -> Tuple[Optional[str], Optional[dict]]:
    user_data = user_db.get_user_by_username(username)
    if user_data and check_password(user_data['password'], password):
        return generate_jwt_token(user_data['id'], user_data['password']), user_data
    return None, None
