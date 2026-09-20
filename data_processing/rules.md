# BOUNDARY
get data from sectors api only focused on current data and short term data
get data from yfinance api focused on long term and cover-additional data

**# UNIFIED DATA LAYER**

START

    receive stock ticker

    request data from Sectors Data Pipeline

        get current data
        get short-term data

    request data from yfinance Data Pipeline

        get long-term data
        get additional data

    receive processed data
    from both pipelines

    check data availability

        if required dataset unavailable

            mark dataset as WARNING

        else

            continue

    resolve overlapping data

        if the same variable exists
        in both data sources

            prioritize Sectors data

            use yfinance data
            as supporting data

        if values differ significantly

            flag data discrepancy

    combine data from both sources

        current data
        +
        short-term data
        +
        long-term data
        +
        additional data

        → unified dataset

    organize unified dataset

        company data
        valuation data
        peer data
        forecast data
        ownership data
        institutional data
        insider data
        historical data
        dividend data
        financial data
        market data

    provide unified dataset

    send unified dataset
    to Intelligence Engine

END

## ENDPOINT FOR FINAL DATA (apply to endpoint_finaldata.py)
**# UNIFIED DATA API**

**# UNIFIED DATA API**

START

    receive API request

    receive ticker

    receive data type

    receive period if required

    identify data source

        if data type is current or short-term

            use Sectors Data Pipeline

        else if data type is long-term
        or additional data

            use yFinance Data Pipeline

    request data from selected pipeline

        if period is provided

            request data based on period

        else

            request default data period

    receive processed data

    resolve data overlap

        if data exists from both sources

            prioritize Sectors data

            use yFinance data
            as supporting data

    organize requested data

        classify data into

            current_data
            short_term_data
            long_term_data
            additional_data

    transform data into
    team's unified data structure

    create JSON response

        include ticker

        include requested data

        include data period

        include data source

        include data status

    return JSON response

END

# HOW TO GET

# UNIFIED DATA API — GET INPUT FORMAT

## 1. GENERAL FORMAT

The Unified Data API uses GET requests to request data based on:

- ticker
- data_type
- period

General format:

GET /api/{ticker}/{data_type}?period={period}

Example:

GET /api/BBCA/price?period=10y


---

## 2. INPUT PARAMETERS

### 2.1 Ticker

The ticker represents the company stock symbol.

Format:

ticker = {STOCK_TICKER}

Example:

BBCA
BBRI
BMRI
TLKM


### 2.2 Data Type

The data_type determines which data is requested.

Available data types:

- price
- valuation
- peers
- forecast
- dividend
- executives
- executive_shareholdings
- major_shareholders
- shareholder_composition
- institutional_transactions
- financials
- balance_sheet
- cash_flow
- company
- sector
- industry
- all


### 2.3 Period

The period determines the time range of the requested data.

Period can be:

- current
- years
- months
- weeks


---

# 3. PERIOD FORMAT

## 3.1 Current

Use `current` when only the latest available data is required.

Format:

period=current

Example:

GET /api/BBCA/valuation?period=current

GET /api/BBCA/forecast?period=current

GET /api/BBCA/ownership?period=current


---

## 3.2 Years

Use years when historical data is required for a number of years.

Format:

period={number}y

Examples:

period=1y

period=5y

period=10y

API examples:

GET /api/BBCA/price?period=10y

GET /api/BBCA/dividend?period=5y

GET /api/BBCA/financials?period=10y


---

## 3.3 Months

Use months when data is required for a number of months.

Format:

period={number}m

Examples:

period=1m

period=3m

period=6m

period=12m

API examples:

GET /api/BBCA/price?period=3m

GET /api/BBCA/institutional_transactions?period=6m


---

## 3.4 Weeks

Use weeks when data is required for a number of weeks.

Format:

period={number}w

Examples:

period=1w

period=2w

period=4w

period=12w

API examples:

GET /api/BBCA/price?period=4w

GET /api/BBCA/institutional_transactions?period=12w


---

# 4. DATA ENDPOINTS

## 4.1 Price

Used to retrieve stock price data.

Endpoint:

GET /api/{ticker}/price?period={period}

Examples:

GET /api/BBCA/price?period=current

GET /api/BBCA/price?period=1y

GET /api/BBCA/price?period=10y


---

## 4.2 Valuation

Used to retrieve valuation metrics.

Endpoint:

GET /api/{ticker}/valuation?period={period}

Examples:

GET /api/BBCA/valuation?period=current

GET /api/BBCA/valuation?period=1y


---

## 4.3 Peers

Used to retrieve peer and comparison data.

Endpoint:

GET /api/{ticker}/peers?period={period}

Examples:

GET /api/BBCA/peers?period=current

GET /api/BBCA/peers?period=1y


---

## 4.4 Future Forecast

Used to retrieve company forecast data.

Endpoint:

GET /api/{ticker}/forecast?period={period}

Examples:

GET /api/BBCA/forecast?period=current

GET /api/BBCA/forecast?period=1y


---

## 4.5 Dividend History

Used to retrieve dividend history.

Endpoint:

GET /api/{ticker}/dividend?period={period}

Examples:

GET /api/BBCA/dividend?period=5y

GET /api/BBCA/dividend?period=10y


---

## 4.6 Key Executives

Used to retrieve company management information.

Endpoint:

GET /api/{ticker}/executives?period={period}

Example:

GET /api/BBCA/executives?period=current


---

## 4.7 Executive Shareholdings

Used to retrieve executive ownership information.

Endpoint:

GET /api/{ticker}/executive_shareholdings?period={period}

Examples:

GET /api/BBCA/executive_shareholdings?period=current

GET /api/BBCA/executive_shareholdings?period=1y


---

## 4.8 Major Shareholders

Used to retrieve major shareholder information.

Endpoint:

GET /api/{ticker}/major_shareholders?period={period}

Examples:

GET /api/BBCA/major_shareholders?period=current

GET /api/BBCA/major_shareholders?period=1y


---

## 4.9 Shareholder Composition

Used to retrieve shareholder composition.

Endpoint:

GET /api/{ticker}/shareholder_composition?period={period}

Examples:

GET /api/BBCA/shareholder_composition?period=current

GET /api/BBCA/shareholder_composition?period=1y


---

## 4.10 Institutional Transactions

Used to retrieve institutional transaction data.

Endpoint:

GET /api/{ticker}/institutional_transactions?period={period}

Examples:

GET /api/BBCA/institutional_transactions?period=1m

GET /api/BBCA/institutional_transactions?period=6m

GET /api/BBCA/institutional_transactions?period=1y


---

## 4.11 Financials

Used to retrieve historical financial data.

Endpoint:

GET /api/{ticker}/financials?period={period}

Examples:

GET /api/BBCA/financials?period=5y

GET /api/BBCA/financials?period=10y


---

## 4.12 Balance Sheet

Used to retrieve historical balance sheet data.

Endpoint:

GET /api/{ticker}/balance_sheet?period={period}

Examples:

GET /api/BBCA/balance_sheet?period=5y

GET /api/BBCA/balance_sheet?period=10y


---

## 4.13 Cash Flow

Used to retrieve historical cash flow data.

Endpoint:

GET /api/{ticker}/cash_flow?period={period}

Examples:

GET /api/BBCA/cash_flow?period=5y

GET /api/BBCA/cash_flow?period=10y


---

## 4.14 Company Information

Used to retrieve company information.

Endpoint:

GET /api/{ticker}/company?period={period}

Example:

GET /api/BBCA/company?period=current


---

## 4.15 Sector

Used to retrieve sector information.

Endpoint:

GET /api/{ticker}/sector?period={period}

Example:

GET /api/BBCA/sector?period=current


---

## 4.16 Industry

Used to retrieve industry information.

Endpoint:

GET /api/{ticker}/industry?period={period}

Example:

GET /api/BBCA/industry?period=current


---

# 5. COMPLETE DATA REQUEST

The `all` endpoint is used when the Intelligence Engine requires the complete unified dataset.

Endpoint:

GET /api/{ticker}/all?period={period}

Examples:

GET /api/BBCA/all?period=current

GET /api/BBCA/all?period=1y

GET /api/BBCA/all?period=5y

GET /api/BBCA/all?period=10y


The API determines which data source is required for each dataset.

Sectors Pipeline:

- current data
- short-term data

yFinance Pipeline:

- long-term data
- additional data


---

# 6. DATA SOURCE MAPPING

| Data Type | Primary Source | Typical Period |
|---|---|---|
| price | yFinance | weeks / months / years |
| valuation | Sectors | current |
| peers | Sectors | current |
| forecast | Sectors | current |
| dividend | yFinance | years |
| executives | Sectors / yFinance | current |
| executive_shareholdings | Sectors | current / short-term |
| major_shareholders | Sectors | current |
| shareholder_composition | Sectors | current |
| institutional_transactions | Sectors / yFinance | weeks / months |
| financials | yFinance | years |
| balance_sheet | yFinance | years |
| cash_flow | yFinance | years |
| company | yFinance | current |
| sector | yFinance / Sectors | current |
| industry | yFinance / Sectors | current |


---

# 7. REQUEST EXAMPLES

## Current Valuation

GET /api/BBCA/valuation?period=current


## Current Forecast

GET /api/BBCA/forecast?period=current


## Historical Price 10 Years

GET /api/BBCA/price?period=10y


## Historical Price 6 Months

GET /api/BBCA/price?period=6m


## Historical Price 4 Weeks

GET /api/BBCA/price?period=4w


## Dividend History 10 Years

GET /api/BBCA/dividend?period=10y


## Financial Data 5 Years

GET /api/BBCA/financials?period=5y


## Institutional Transactions 6 Months

GET /api/BBCA/institutional_transactions?period=6m


## Complete Current Data

GET /api/BBCA/all?period=current


## Complete Historical Dataset

GET /api/BBCA/all?period=10y


---

# 8. REQUEST FLOW

START

    receive GET request

    extract ticker

    extract data_type

    extract period

    identify requested data

    identify required data source

        if current or short-term

            use Sectors Data Pipeline

        else if long-term or additional

            use yFinance Data Pipeline

    request processed data

    organize data according to
    Unified Data Schema

    create JSON response

    return JSON response

END


## UPDATE FOR GET DIVIDENT GROWTH DATA
divident_growth = get divident_growth data from API and data source

if period = current
    get divident_growth priority from sectors API

if period = long term(years, month, week)
    get dividen_growth priority from yfinance

add method
get data (data type = dividen growth) from endpoint_finadata.py and unified_data folder context

if data not exist
    return error
    

