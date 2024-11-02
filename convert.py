#!/usr/bin/env python3
from datetime import datetime
from dateutil.parser import parse
import sys
import xml.etree.ElementTree as ET
import re
import csv

output_file_credit = 'credit_transactions.csv'
output_file_chequing = 'chequing_transactions.csv'
input_files = sys.argv[1:]

font_header = "MetaBookLF-Roman"
font_txn = "MetaBoldLF-Roman"

class Block:
    def __init__(self, page, x, x2, y, text):
        self.page = page
        self.x = x
        self.x2 = x2
        self.text = text
        self.y = y
    
    def __repr__(self):
        return f"<Block page={self.page} x={self.x} x2={self.x2} y={self.y} text={self.text} />"

def process_credit_statements(input_files, output_file):
    txns = []
    re_exchange_rate = re.compile(r'Exchange rate-([0-9]+\.[0-9]+)', re.MULTILINE)
    re_foreign_currency = re.compile(r'Foreign Currency-([A-Z]+) ([0-9]+\.[0-9]+)', re.MULTILINE)

    for input_file in input_files:
        tree = ET.parse(input_file)
        root = tree.getroot()
        rows = []

        print(f'Processing {input_file}...')

        for page in root:
            figure = page[1]
            row = ''
            last_x2 = None
            for tag in figure:
                if tag.tag == 'text':
                    size = float(tag.attrib['size'])
                    x_pos = float(tag.attrib["bbox"].split(",")[0])
                    x2_pos = float(tag.attrib["bbox"].split(",")[2])

                    if last_x2 is not None:
                        if x2_pos < last_x2:
                            row += "\n"
                        if len(row) > 10 and (x_pos - last_x2) > 0.7:
                            row += " "
                    last_x2 = x2_pos
                    if size >= 5 and size <= 9:
                        row += tag.text
                elif tag.tag != 'text' and row != '':
                    rows.append(row)
                    row = ''
                    last_x2 = None

        date_range_regex = re.compile(r'^.*STATEMENT FROM ([A-Z]{3}) \d{2},? ?(\d{4})? TO ([A-Z]{3}) \d{2}, (\d{4})', re.MULTILINE)
        date_range = {}

        for row in rows:
            if match := date_range_regex.search(row):
                date_range[match.group(1)] = match.group(2) or match.group(4)
                date_range[match.group(3)] = match.group(4)
                break

        MONTHS = {
            'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
            'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'
        }
        txn_rows = []

        for row in rows:
            if len(row) >= 10:
                month_1 = row[:3]
                month_2 = row[5:8]
                if month_1 in MONTHS and month_2 in MONTHS:
                    txn_rows.append(row)

        for row in txn_rows:
            date_1_month = row[:3]
            date_1_day = row[3:5]
            date_2_month = row[5:8]
            date_2_day = row[8:10]

            transaction_date = None
            try:
                transaction_date = datetime.strptime(f'{date_1_month}-{date_1_day}-{date_range[date_1_month]}', '%b-%d-%Y')
            except KeyError:
                first_year = min([int(year) for year in date_range.values()])
                transaction_date = datetime.strptime(f'{date_1_month}-{date_1_day}-{first_year}', '%b-%d-%Y')
            posting_date = datetime.strptime(f'{date_2_month}-{date_2_day}-{date_range[date_2_month]}', '%b-%d-%Y')
            
            description, amount = row[10:].split('$')

            if description.endswith('-'):
                description = description[:-1]
                amount = '-' + amount

            description = description.split("\n")[0]
            raw = row.strip()

            amount = amount.replace(',', '').replace("\n", "")
            match_exchange_rate = re_exchange_rate.search(raw)
            match_foreign_currency = re_foreign_currency.search(raw)
            
            if float(amount) > 0:
                txns.append({
                    'transaction_date': transaction_date,
                    'posting_date': posting_date,
                    'description': description,
                    'credit': '',
                    'debit': amount,
                    'raw': raw,
                    'exchange_rate': match_exchange_rate.group(1) if match_exchange_rate else None,
                    'foreign_currency': match_foreign_currency.group(1) if match_foreign_currency else None,
                    'amount_foreign': match_foreign_currency.group(2) if match_foreign_currency else None,
                })
            else:
                txns.append({
                    'transaction_date': transaction_date,
                    'posting_date': posting_date,
                    'description': description,
                    'credit': amount,
                    'debit': '',
                    'raw': raw,
                    'exchange_rate': match_exchange_rate.group(1) if match_exchange_rate else None,
                    'foreign_currency': match_foreign_currency.group(1) if match_foreign_currency else None,
                    'amount_foreign': match_foreign_currency.group(2) if match_foreign_currency else None,
                })

    txns = sorted(txns, key = lambda txn: txn['transaction_date'])

    with open(output_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([
            'Transaction Date',
            'Posting Date',
            'Description',
            'Credit',
            'Debit',
            'Amount Foreign Currency',
            'Foreign Currency',
            'Exchange Rate',
            'Raw',
        ])

        for txn in txns:
            csv_writer.writerow([
                txn['transaction_date'].strftime('%Y-%m-%d'),
                txn['posting_date'].strftime('%Y-%m-%d'),
                txn['description'],
                txn['credit'],
                txn['debit'],
                txn['amount_foreign'],
                txn['foreign_currency'],
                txn['exchange_rate'],
                txn['raw'],
            ])

def process_chequing_statements(input_files, output_file):
    csv_rows = []

    for input_file in input_files:
        tree = ET.parse(input_file)
        root = tree.getroot()
        rows = []

        continue_input_loop = False
        for i_tag, tag in enumerate(root[0][1]):
            if i_tag > 10:
                continue_input_loop = True
                break
            if font := tag.get("font"):
                if font.endswith("MetaBoldLF-Roman") or font.endswith("Utopia-Bold"):
                    break
        
        if continue_input_loop:
            print(f"Skipping {input_file}...")
            continue

        print(f'Processing {input_file}...')

        blocks = []
        pages = set()
        for page_num, page in enumerate(root):
            pages.add(page_num)
            figure = page[1]
            text = ''
            last_x = None
            last_x2 = None
            block_x = None
            width = 0
            seen_text = False
            for tag in figure:
                clear_text = False
                append_block = ""
                if tag.tag == 'text':
                    seen_text = True
                    font = tag.attrib.get("font")
                    if font:
                        font = font.split("+")[1]
                    size = float(tag.attrib['size'])
                    x_pos = float(tag.attrib["bbox"].split(",")[0])
                    y_pos = float(tag.attrib["bbox"].split(",")[1])
                    x2_pos = float(tag.attrib["bbox"].split(",")[2])

                    if last_x2 is not None:
                        if x_pos - last_x2 > 5:
                            append_block = text
                            text = ""
                            width = 0
                        elif (x_pos - last_x2) > 0.7:
                            text += " "
                    last_x = x_pos
                    last_x2 = x2_pos
                    width += size
                    if font in (font_txn, font_header):
                        text += tag.text
                    if block_x is None:
                        block_x = x_pos
                elif tag.tag != 'text' and text != '':
                    if seen_text:
                        append_block = text
                    seen_text = False
                    clear_text = True
                    width = 0
                    last_x2 = None
                
                if append_block:
                    block = Block(page_num, block_x, x2_pos, y_pos, append_block.strip())
                    blocks.append(block)
                    block_x = None

                if clear_text:
                    text = ''

        open_balance_parts = [b.text for b in blocks if b.text.startswith("Your opening balance")][0].split(" ")[-3:]
        open_balance_date = parse(" ".join(open_balance_parts))
        start_year = int(open_balance_parts[2])

        header_sets = []
        for page in pages:
            page_blocks = [b for b in blocks if b.page == page]
            end_of_header_index = 0

            for i, block in enumerate(page_blocks):
                if block.text == "Date":
                    if other_blocks := page_blocks[i+1:i+5]:
                        header_sets.append([block, *other_blocks])
                        end_of_header_index = i + 4

            page_blocks = [block for i, block in enumerate(page_blocks) if i > end_of_header_index]

            if len(header_sets) <= page:
                break

            cell_pos = 0
            i = 0
            block_pos = 0
            row = []
            last_date = None

            while block_pos < len(page_blocks):
                row_pos = 0
                block = page_blocks[block_pos]
                block_consumed = False

                headers = header_sets[block.page]

                mid_point = (block.x2 - block.x) / 2 + block.x
                for header in headers:
                    if mid_point > header.x and mid_point < header.x2:
                        row_pos = headers.index(header)

                if i % 5 == row_pos:
                    if i % 5 == 0:
                        date = parse(f"{block.text} {start_year}")

                        if date < open_balance_date:
                            date = parse(f"{block.text} {start_year+1}")
                        block.text = str(date.date())
                        if block.text.strip():
                            last_date = block.text
                    block_consumed = True
                    row.append(block.text)
                elif i % 5 == 0 and page_blocks[block_pos].text == "Opening Balance":
                    row.append(str(open_balance_date.date()))
                elif last_date and i % 5 == 0:
                    row.append(last_date)
                else:
                    row.append("")
                if i % 5 == 4:
                    csv_rows.append(row)
                    row = []
                if block_consumed:
                    block_pos += 1
                i += 1

    with open(output_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([
            "Date",
            "Description",
            "Withdrawls",
            "Deposits",
            "Balance"
        ])

        for row in csv_rows:
            if "Opening Balance" in row:
                description = "Opening Balance"
                deposits = ""
                withdrawals = ""
            else:
                description = row[1]
                deposits = row[2]
                withdrawals = row[3]

            csv_writer.writerow([
                row[0],
                description,
                withdrawals,
                deposits,
                row[4]
            ])

if __name__ == "__main__":
    credit_files = [f for f in input_files if "visa" in f.lower()]
    chequing_files = [f for f in input_files if "chequing" in f.lower()]

    process_credit_statements(credit_files, output_file_credit)
    process_chequing_statements(chequing_files, output_file_chequing)