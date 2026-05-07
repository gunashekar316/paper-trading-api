from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import SessionLocal, engine
import yfinance as yf
import auth
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

# This helps us talk to the database for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/signup", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Check if user already exists
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # 2. SCRAMBLE THE PASSWORD!
    hashed_pwd = auth.get_password_hash(user.password)
    
    # 3. Create the new user with the scrambled password
    new_user = models.User(username=user.username, hashed_password=hashed_pwd)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/price/{ticker}")
def get_stock_price(ticker: str):
    # 1. Ask Yahoo Finance for the stock data
    stock = yf.Ticker(ticker)
    
    # 2. Get the most recent price
    try:
        # 'fast_info' gives us quick access to the current price
        price = stock.fast_info['last_price']
        
        if price is None:
            raise HTTPException(status_code=404, detail="Stock ticker not found")
            
        return {"ticker": ticker.upper(), "current_price": round(price, 2)}
    
    except Exception:
        raise HTTPException(status_code=404, detail="Could not fetch price")
    
# This tells FastAPI where users go to get their token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# THE BOUNCER
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. Decode the token using your secret key
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # 2. Find the user in the database
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
        
    return user

@app.post("/buy")
def buy_stock(trade: schemas.TradeCreate, db: Session = Depends(get_db)):
    # 1. Get the User from the database
    user = db.query(models.User).filter(models.User.id == trade.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Get the Real-Time Price
    stock = yf.Ticker(trade.ticker)
    try:
        current_price = stock.fast_info['last_price']
    except:
        raise HTTPException(status_code=400, detail="Invalid ticker")

    # 3. Calculate Total Cost
    total_cost = current_price * trade.shares

    # 4. THE JUDGE: Does the user have enough money?
    if user.cash_balance < total_cost:
        raise HTTPException(status_code=400, detail="Not enough cash!")

    # 5. THE ACCOUNTANT: Subtract money & Update Portfolio
    user.cash_balance -= total_cost

    # Check if they already own some of this stock
    portfolio_item = db.query(models.Portfolio).filter(
        models.Portfolio.user_id == trade.user_id, 
        models.Portfolio.stock_ticker == trade.ticker.upper()
    ).first()

    if portfolio_item:
        portfolio_item.total_shares += trade.shares
    else:
        new_item = models.Portfolio(
            user_id=trade.user_id, 
            stock_ticker=trade.ticker.upper(), 
            total_shares=trade.shares
        )
        db.add(new_item)

    db.commit()
    return {"message": f"Successfully bought {trade.shares} shares of {trade.ticker.upper()}"}

# Notice we removed {user_id} from the URL! The token tells us who they are now.
@app.get("/portfolio")
def get_user_portfolio(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    # Fetch all stocks owned by the currently logged-in user
    user_stocks = db.query(models.Portfolio).filter(models.Portfolio.user_id == current_user.id).all()

    return {
        "username": current_user.username,
        "remaining_cash": round(current_user.cash_balance, 2),
        "stocks": user_stocks
    }

@app.post("/sell")
def sell_stock(trade: schemas.TradeCreate, db: Session = Depends(get_db)):
    # 1. Get the User from the database
    user = db.query(models.User).filter(models.User.id == trade.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. THE JUDGE: Do they actually own enough of this stock to sell?
    portfolio_item = db.query(models.Portfolio).filter(
        models.Portfolio.user_id == trade.user_id, 
        models.Portfolio.stock_ticker == trade.ticker.upper()
    ).first()

    if not portfolio_item or portfolio_item.total_shares < trade.shares:
        raise HTTPException(status_code=400, detail="Not enough shares to sell!")

    # 3. Get the CURRENT Real-Time Price
    stock = yf.Ticker(trade.ticker)
    try:
        current_price = stock.fast_info['last_price']
    except:
        raise HTTPException(status_code=400, detail="Could not fetch current price")

    # 4. Calculate Total Value of the Sale
    total_value = current_price * trade.shares

    # 5. THE ACCOUNTANT: Add money & Subtract Shares
    user.cash_balance += total_value
    portfolio_item.total_shares -= trade.shares

    # Clean-up: If they sold everything, delete that row from the portfolio
    if portfolio_item.total_shares == 0:
        db.delete(portfolio_item)

    db.commit()
    return {
        "message": f"Successfully sold {trade.shares} shares of {trade.ticker.upper()}",
        "money_earned": round(total_value, 2)
    }

@app.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Find the user
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    # 2. Verify user exists AND password matches the scrambled version
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Create the VIP Token
    access_token = auth.create_access_token(data={"sub": user.username})
    
    return {"access_token": access_token, "token_type": "bearer"}
