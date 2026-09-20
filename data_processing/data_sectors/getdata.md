**# THIS IS FOR GETTING THE FINAL DATA**

after data mining and data processing, display the final data in a well-structured format for inteligence engine and analysis

DATA WAJIB

Valuation

Peer

Future Forecast

Institutional Transactions

Executive Shareholdings

Major Shareholders

Shareholder Composition

Dividend

Executives

Historical Price

**# FORMAT**

displaying all data as table

plus data processing status (okay, warning, error)



**# WORK FLOW**

data miner.py -> data validator.py -> data normalizer.py -> data caching.py -> getdata.py


**# GET DATA METHOD**

get price (stock)

get variable (stock)

get all data (stock)


**# GET PRICE**

get_price(ticker)

receive stock ticker

check cached stock price

if cached price exists and is valid

    return cached stock price

else

    get stock price from final data

    return stock price


**# GET VARIABLE**

get_variable(ticker, variable)

receive stock ticker

receive requested variable

check variable availability

if variable exists

    check data processing status

    if status = OKAY

        return requested variable

    else if status = WARNING

        return requested variable with warning

    else if status = ERROR

        reject requested variable

else

    return variable not found


**# GET ALL DATA**

get_all_data(ticker)

receive stock ticker

check all required data

if all required data exists

    retrieve all final data

    check data processing status

    return all data

else if some data has WARNING

    retrieve available data

    return data with warning status

else if required data has ERROR

    reject invalid data

    display error status


**# DATA AVAILABILITY CHECK**

check each required data

if Valuation exists

    status = OKAY

else

    status = ERROR

if Peer exists

    status = OKAY

else

    status = ERROR

if Future Forecast exists

    status = OKAY

else

    status = ERROR

if Institutional Transactions exists

    status = OKAY

else

    status = ERROR

if Executive Shareholdings exists

    status = OKAY

else

    status = ERROR

if Major Shareholders exists

    status = OKAY

else

    status = ERROR

if Shareholder Composition exists

    status = OKAY

else

    status = ERROR

if Dividend exists

    status = OKAY

else

    status = ERROR

if Executives exists

    status = OKAY

else

    status = ERROR

if Historical Price exists

    status = OKAY

else

    status = ERROR


**# DATA PROCESSING STATUS**

check processing status of each data

if data passed validation and normalization

    status = OKAY

else if data passed validation but has missing optional data

    status = WARNING

else if data failed validation or normalization

    status = ERROR


**# FINAL DATA STATUS**

check all required data status

if all required data status = OKAY

    final status = OKAY

    data is ready for intelligence engine

else if required data has WARNING

    final status = WARNING

    data is still available

    display warning

else if required data has ERROR

    final status = ERROR

    do not send invalid data to intelligence engine


**# DATA STRUCTURE**

create final data structure

    ticker

    valuation

    peer

    future_forecast

    institutional_transactions

    executive_shareholdings

    major_shareholders

    shareholder_composition

    dividend

    executives

    historical_price

    processing_status


**# TABLE OUTPUT**

display final data as table

    DATA TYPE
    VALUE
    STATUS

example:

    Valuation               | data | OKAY
    Peer                    | data | OKAY
    Future Forecast         | data | WARNING
    Institutional Trans.    | data | OKAY
    Executive Shareholding  | data | OKAY
    Major Shareholders      | data | OKAY
    Shareholder Composition | data | OKAY
    Dividend                | data | WARNING
    Executives              | data | OKAY
    Historical Price        | data | OKAY


**# INTELLIGENCE ENGINE REQUEST**

when intelligence engine requests data

    receive request

    identify requested ticker

    identify requested data method

    if request = get_price

        get stock price

    else if request = get_variable

        get requested variable

    else if request = get_all_data

        get all required data

    check cache

    if cache exists and is valid

        retrieve data from cache

    else

        retrieve data from local storage

    check data availability

    check processing status

    return final data to intelligence engine