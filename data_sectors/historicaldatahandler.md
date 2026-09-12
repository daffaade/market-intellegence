**# HISTORICAL DATA HANDLING**

Historical data handling dilakukan untuk mengelola data berdasarkan waktu sehingga data historis dapat digunakan untuk analisis perubahan harga, event study, forecasting, dan proses machine learning.

**## HISTORICAL DATA COLLECTION**

while historical data is requested from API

    request data based on defined date range

    receive historical data

    validate data

    normalize data

    store historical data locally

**## DATE ORDERING**

check historical data

sort data based on date or timestamp

if date is older than the next data

    place data before the next data

else

    continue

**## HISTORICAL DATA COMPLETENESS**

check each date within the requested period

if historical data exists

    status = AVAILABLE

else if data is not available

    status = MISSING

    record missing date

**## DUPLICATE HISTORICAL DATA**

check each historical record

if ticker + date already exists

    reject duplicate record

else

    store historical record

**## HISTORICAL DATA UPDATE**

when new data is received

    compare new data with existing historical data

    if data does not exist

        add new data

    else if data already exists

        update existing data if necessary

    else

        keep existing data

**## HISTORICAL DATA PERIOD**

define historical data period

example:

    1 year
    3 years
    5 years

store data according to its date

**## DATA VERSION / REVISION HANDLING**

check historical data

if API provides revised data

    update existing data

    record updated_at

else

    keep existing data

**## HISTORICAL DATA STORAGE**

store historical data using structured format

example:

    ticker
    date
    open
    high
    low
    close
    volume

data is stored locally until database is ready

**## HISTORICAL DATA RESULT**

if historical data is complete and valid

    status = READY

else if there is missing historical data

    status = INCOMPLETE

else

    status = ERROR