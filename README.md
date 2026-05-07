# 📈 Paper Trading API

A RESTful backend service built with FastAPI that allows users to simulate stock market trading using real-time market data. This engine handles user authentication, live price fetching, portfolio management, and secure trade validations.

## 🚀 Features

* **JWT Authentication:** Secure user sign-up and login using Bcrypt password hashing and JSON Web Tokens.
* **Real-Time Market Data:** Integrates with `yfinance` to fetch live stock prices for accurate trade execution.
* **Transaction Engine:** Validates every trade to ensure users cannot spend money they don't have or sell shares they don't own.
* **Portfolio Tracking:** Maintains a persistent SQLite database tracking user cash balances and aggregate stock holdings.

## 🛠️ Tech Stack

* **Framework:** FastAPI (Python 3)
* **Database:** SQLite with SQLAlchemy (ORM)
* **Market Data:** yfinance
* **Security:** passlib, bcrypt, python-jose (JWT)
* **Deployment:** Render

## 🔗 Live Demo
*Base URL:* `https://paper-trading-api-1.onrender.com/docs`

## 📖 API Endpoints

### Authentication
* `POST /signup` - Register a new user (initializes with $100,000 paper cash).
* `POST /login` - Authenticate and receive a JWT Bearer token.

### Trading (Requires Bearer Token)
* `GET /price/{ticker}` - Fetch the real-time price of a specific stock.
* `POST /buy` - Execute a buy order (calculates total cost, deducts cash, adds to portfolio).
* `POST /sell` - Execute a sell order (calculates total value, adds cash, removes from portfolio).
* `GET /portfolio` - View current cash balance and all active stock holdings.

## 💻 Local Setup
1. `Clone the repository`:
   git clone https://github.com/gunashekar316/paper-trading-api.git
2. `Install the required dependencies`:
   pip install -r requirements.txt
3. `Run the development server`:
   python -m uvicorn main:app --reload
4. `Access the interactive documentation`: http://localhost:8000/docs.
