@echo off
Rem Ensure python is in your PATH.

set script_path=%~dp0
set output_file_credit="credit_transactions.csv"
set output_file_chequing="chequing_transactions.csv"
set pdf2txt_path="%script_path%.venv\Scripts\pdf2txt.py"

Rem Check if virtual environment exists
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    echo Installing dependencies...
    call .venv\Scripts\activate.bat & pip install -r requirements.txt
) else (
    echo Virtual environment already exists. Skipping setup...
)

Rem Activate the virtual environment
call .venv\Scripts\activate.bat

Rem Remove any existing output files
if exist %output_file_credit% (
    del %output_file_credit%
)
if exist %output_file_chequing% (
    del %output_file_chequing%
)

Rem Convert each .pdf file in the directory to .xml using pdf2txt.py
for /r %%v in (*.pdf) do (
    IF not exist "%%v.xml" (
        echo Converting %%v...
        python %pdf2txt_path% -o "%%v.xml" "%%v"
    ) 
)

Rem Get a list of .xml files in the directory
set input_files=
for /f "delims=" %%a in ('dir "*.xml" /on /b /a-d ') do call set input_files=%%input_files%% "%%a"

Rem Extract the transactions from every .xml file and add to the output files
python convert.py %input_files%

Rem Remove the .xml files that were generated
echo Cleaning up...
del "*.xml"

echo ------
echo Credit transaction data is available in %output_file_credit%.
echo Chequing transaction data is available in %output_file_chequing%.

pause