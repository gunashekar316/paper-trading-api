from pydantic import BaseModel

# This defines what the 'Entry Form' looks like
class UserCreate(BaseModel):
    username: str
    password: str

# This defines what we send BACK to the user (we don't send the password back!)
class UserResponse(BaseModel):
    id: int
    username: str
    cash_balance: float

    class Config:
        from_attributes = True

class TradeCreate(BaseModel):
    user_id: int
    ticker: str
    shares: int

class Token(BaseModel):
    access_token: str
    token_type: str
