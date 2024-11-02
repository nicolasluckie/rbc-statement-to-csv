# RBC Statement To CSV

This program will parse transaction data out of RBC credit card and chequing statements to `.csv` files with the following columns:

**Credit Statements:**

- Transaction Date
- Posting Date
- Description
- Credit Amount
- Debit Amount
- Amount Foreign Currency
- Foreign Currency
- Exchange Rate
- Raw

**Chequing Statement:**

- Transaction Date
- Description
- Withdrawl Amount
- Deposit Amount
- Balance

## Folder Structure

Before running:

```
.
├── convert.bat
├── convert.py
├── convert.sh
├── Visa Statement-1234 2024-11-02.pdf
└── Chequing Statement-1234 2024-11-02.pdf
```

After running:

```
.
├── convert.bat
├── convert.py
├── convert.sh
├── Visa Statement-1234 2024-11-02.pdf
├── Chequing Statement-1234 2024-11-02.pdf
├── credit_transactions.csv
└── chequing_transactions.csv
```

## Requirements
- Python 3.8+
- [PdfMiner](https://github.com/pdfminer/pdfminer.six)

Ensure `python` is in your PATH.

## Installation

Clone or download this repository.

## Usage
Drop all PDF statements into the project directory.

> [!NOTE]
> - **Credit** statements must include ***"visa"*** in the filename.
> - **Chequing** statements must include ***"chequing"*** in the filename.

### Windows
Run (double-click) `convert.bat`.

### Linux

```sh
./convert.sh
```

The program will detect and setup a new virtual environment (if not already setup) then read all transactions, sort them, and consolidate them into separate `credit_transactions.csv` and `chequing_transactions.csv` files.

## License
This project is forked from [mindcruzer/rbc-statement-to-csv](https://github.com/mindcruzer/rbc-statement-to-csv), licensed under the [MIT License](./LICENSE). All changes and contributions made in this fork continue to be available under the same license.

## Disclaimer
This project is an independent effort and is neither affiliated with nor endorsed by RBC. It is intended solely for open-source use. All concepts and implementations are original, no proprietary information or data from RBC is utilized or disclosed. The author disclaims any liability for misuse or damages arising from the use of this code.
