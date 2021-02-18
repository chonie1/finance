# C$50 Finance Project

C$50 Finance is a full stack web application developed with Flask that allows users to manage a paper trading account

## Final Product
!["Screenshot of main page"](/docs/index.png)
!["screenshot querying a stoack"](/docs/query.png)
!["screenshot of history"](/docs/history.png)
!["screenshot of login page"](/docs/login.png)

## Dependencies
- cs50
- Flask
- Flask-Session
- requests

## Getting Started
- Install all dependencies using the command:
 `pip install -r requirements.txt` 
- Register for IEX API key: [iexcloud.io/cloud-login#/register/](iexcloud.io/cloud-login#/register/) 
- Export your key as an environment variable:
  `export API_KEY=[your_API_KEY]`
- Run the development web server using the command:
 `flask run` 

## Features
* Query Stock Prices
* Buy & Sell Stocks
* Add Funds
* Login & Register
* View Transaction History
