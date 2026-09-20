**# DATA NORMALIZATION**

Data normalization dilakukan untuk mengubah data yang telah lolos validation menjadi format yang seragam dan konsisten sebelum disimpan ke database atau digunakan oleh Intelligence Engine.

**## FIELD NAME NORMALIZATION**

check each field name

if field name is different from defined schema

    change field name to standard field name

else

    keep field name

**## DATA TYPE NORMALIZATION**

check each data type

if data type is different from standard data type

    convert data to standard data type

else

    keep data type

**## NUMERIC NORMALIZATION**

check each numeric data

if numeric data uses different decimal format

    convert to standard numeric format

else

    keep numeric format

**## PERCENTAGE NORMALIZATION**

check percentage data

if percentage is stored as percentage value

    convert to decimal format

else if percentage is already decimal

    keep data

**## DATETIME / TIMESTAMP NORMALIZATION**

check each datetime or timestamp data

if timezone is different from standard timezone

    convert to standard timezone

else

    keep timezone

convert datetime to standard format

**## CURRENCY NORMALIZATION**

check currency for each financial data

if currency is different from standard currency

    convert to standard currency

else

    keep currency

**## NULL VALUE NORMALIZATION**

check each field

if data = null

    keep data as null

else

    keep data

**## CATEGORICAL DATA NORMALIZATION**

check categorical data

if category format is different from standard category

    convert to standard category

else

    keep category

**## TEXT NORMALIZATION**

check text data

remove unnecessary whitespace

standardize text format

keep important company and ticker information

**## PRECISION NORMALIZATION**

check numeric precision

if decimal places are more than required

    round data to standard precision

else

    keep data

**## FINAL NORMALIZATION RESULT**

if all data follows the standard format

    status = NORMALIZED

else

    status = NORMALIZATION_ERROR


**## OUTPUT FORMAT**
-no capital at beginning word
-change blankspace with "_"
-remove symbol special from field name
-no symbol at the end of line
-text must be readable
