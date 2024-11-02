#!/bin/bash

# define output filenames
OUTPUT_FILE_CREDIT='credit_transactions.csv'
OUTPUT_FILE_CHEQUING='chequing_transactions.csv'

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Installing dependencies..."
    source .venv/bin/activate
    pip install -r requirements.txt
else
    echo "Virtual environment already exists. Skipping setup..."
    source .venv/bin/activate
fi

# find pdf2txt.py
PDF2TXT=$(which pdf2txt.py)
mkdir -p ./tmp

# Convert each .pdf file in the directory to .xml using pdf2txt.py
find . -name '*.pdf' -print0 | while IFS= read -r -d '' PDF; do
    XML_FILE=$(basename -s .pdf "$PDF")
    python "$PDF2TXT" -o "./tmp/${XML_FILE}.xml" "$PDF"
done

# Collect XML filenames into an array, handling spaces properly
XML_FILES=()
while IFS=  read -r -d $'\0'; do
    XML_FILES+=("$REPLY")
done < <(find ./tmp -name '*.xml' -print0)

# Extract the transactions from every .xml file and add to the output files
python convert.py "${XML_FILES[@]}"

# Clean up XML files
rm -rf tmp/*.xml

echo "Credit transaction data is available in $OUTPUT_FILE_CREDIT."
echo "Chequing transaction data is available in $OUTPUT_FILE_CHEQUING."