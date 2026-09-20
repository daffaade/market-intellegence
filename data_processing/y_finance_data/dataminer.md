# DATA MINING

get this from api
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

    if not exist skip

    
    get data as json


**# DATA VALIDATION**

**## SCHEMA VALIDATION**

while data requested from API

    check each field if exist or not

    if Required field missing → ERROR

        reject the data

    else if Optional field missing → WARNING

        continue validation

    else → SUCCESS

**## DATA TYPE VALIDATION**

while data received from API

    check data type for each field

    if data type is not correct → ERROR

        reject the current data

        record validation error

    else if data type is correct → SUCCESS

        continue validation

**## MISSING VALUE VALIDATION**

check each field in data

if data = null

    if field is Required → ERROR

        reject the current data

    else if field is Optional → WARNING

        keep data as null

else → SUCCESS

**## RANGE VALIDATION**

check each numeric data

if data is outside the defined valid range → ERROR

    reject the current data

    record validation error

else if data is outside the normal range but still possible → WARNING

    keep data

    record validation warning

else → SUCCESS

**## DUPLICATE VALIDATION**

check each data based on unique identifier

if data already exists → ERROR

    reject duplicate data

    record validation error

else → SUCCESS

    continue validation

**## DATETIME / TIMESTAMP VALIDATION**

check each datetime or timestamp data

if datetime format is invalid → ERROR

    reject the current data

    record validation error

else if timezone is missing when required → WARNING

    normalize timezone

else → SUCCESS

    continue validation

**## CROSS-FIELD CONSISTENCY VALIDATION**

check relationship between related fields

if field values are logically inconsistent → ERROR

    reject the current data

    record validation error

else if field values are unusual but still possible → WARNING

    keep data

    record validation warning

else → SUCCESS

**## FINAL VALIDATION STATUS**

if there is ERROR → INVALID

else if there is WARNING → WARNING

else → VALID
