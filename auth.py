from datetime import datetime, timedelta
from jose import jwt
import bcrypt

# Secret Key for the VIP Wristbands (Tokens)
SECRET_KEY = "super_secret_trading_key_do_not_share"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- Updated Functions (Bypassing passlib) ---

def get_password_hash(password: str) -> str:
    """Takes a plain text password and scrambles it securely."""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode('utf-8') 

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks if the typed password matches the scrambled one in the database."""
    password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password=password_bytes, hashed_password=hashed_password_bytes)

def create_access_token(data: dict):
    """Creates the digital VIP wristband valid for 30 minutes."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt