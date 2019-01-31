import datetime
import os
import re

class OperatingMode(object): #pylint: disable=too-few-public-methods
    CHASE_CREDIT = 1
    CHASE_CHECKING = 2
    SCHWAB_CHECKING = 3
    SCHWAB_BROKERAGE = 4

# MODIFY THIS DEPENDING ON WHAT DATA WE'RE PROCESSING
OP_MODE = OperatingMode.CHASE_CHECKING

FIRST_TX_DATE = datetime.datetime(2018, 2, 16) # first day of joblessness
LAST_TX_DATE = datetime.datetime(2019, 1, 8) # last date we have data across all sources

# TODO: randomize and check for multiple matches

# terms with spaces are deliberate so as to minimize false positives
# terms with substrinfs of read words are meant to capture variations on a word
chase_credit_terms = {
    'CNC': ["TRAVEL CREDIT", "AUTOMATIC PAYMENT", "ANNUAL MEMBERSHIP FEE"],

    # flight, train, uber, other transport
    'F': ["airline", "FRONTIER", " air ", "UNITED 0", "PEGASUS", "NORWEGIAN", "KIWI.COM", "RYANAIR"],
    'TR': ["WWW.CD.CZ", "AMTRAK", "LE.CZ", "CALTRAIN"],
    'UB': ["uber", "LYFT"],
    'OT': ["limebike", "BIRD", "PARKING KITTY", "MTA", "CITY OF PORTLAND DEPT", "76 -", "fuel", "HUB", "CHEVRON", "SHELL"],

    # housing, activities
    'H': ["AIRBNB", "hotel"],
    'A': ["VIATOR"], # visas go in here too

    # coffee, restaurant, booze, store
    'C': ["coffee", "costa", "starbucks", "philz", "java", "LOFT CAFE", "Tiny's", "KAFE", "KAVA", "STUMPTOWN", "COFFE"],
    'R': ["restaur", "sushi", "BILA VRANA", "pizza", "grill", "AGAVE", "thai", "ramen", "bagel", "pub ",
          "taco", "VERTSHUSET", "MIKROFARMA", "LTORGET", "POULE", "CHIPOTLE", "BIBIMBAP", "Khao", "EAST PEAK",
          "ZENBU", "EUREKA", "KERESKEDO", "CRAFT", "BURGER", "BAO", "ESPRESSO", "CAFE", "house",
          "PHO", "pizz", "REST", "TAVERN"],
    'B': ["brew", "liquor", "beer", "PUBLIC HO", "TAPROOM", "wine", "VINOTEKA", "PONT OLOMOUC", "BAR ", "hops",
          "BOTTLE", " PIV", "POPOLARE", "NELSON", "GROWLERS", "HOP SHOP", "BARREL", "BLACK CAT", "VENUTI",
          "BODPOD", "VINEYARD", "MIKKELLER", "CANNIBAL"],
    'S': ["Billa", "ALBERT", "market", "SAFEWAY", "CVS", "7-ELEVEN", "GROCERY", "Strood", "DROGERIE", "WHOLEFDS", "FOOD", "RITE"],

    # entertainment (gifts-books-games)
    'E': ["AMAZON", "POWELL", "NINTENDO", "GOPAY.CZ", "FREEDOM INTERNET", "AMZN", "FLORA", "BARNES"],
    # body (clothes-hair-spa),
    'BDY': ["NORDSTROM", "spa", "ALEXANDRA D GRECO", "FIT FOR LIFE", "MANYOCLUB"],
    # digital (vpn-spotify-website-phone)
    'DIG': ["AVNGATE", "Spotify", "GHOST", "google"],

    # misc
    'EDU': ["CZLT.CZ"], # language-course / EFT course / license renewal
    'MOV': [], # moving
    'HLT': [], # insurance, doctors, etc
    'HMM': [], # sketchy shit
    'I': [] # unknown small charge, ignore
}

chase_checking_terms = {
    'CNC': ["CHASE CREDIT CRD AUTOPAY", "SCHWAB", "DEPOSIT", "TRANSFER", "TAX", "C PAYROLL",
            "payment from MIROSLAV", "payment to Sophia", "payment from VERONIKA KUKLA", "POPMONEY"],
    'ATM': ["ATM", "CHECK_PAID"],
    'MOV': ["WIRE FEE", "Pacific Gas"],
    'FEE': ["ATM FEE", "ADJUSTMENT FEE", "SERVICE FEE", "COUNTER CHECK"],
    'SQR': ["SQC*", "VENMO", "payment from SUZANNE", "payment to Mom", "payment to Suzy"],
    'F': ["NORWEGIAN", "EXPEDIA"],
    'HMM': ["PIZTUZTIYA"],
    'TR': ["RAIL"],

}

schwab_checking_terms = {
    'CNC': ["TRANSFER", "ACH"],
    'ATM': ["ATM"],
    'FEE': ["INTADJUST"]
}

schwab_brokerage_terms = {
    'CNC': ["TRANSFER", "VANGUARD"],
    'I': ["Interest"]
}


# TERM-SPECIFIC STUFF

def get_terms(mode=OP_MODE):
    terms_by_mode = {
        OperatingMode.CHASE_CREDIT: chase_credit_terms,
        OperatingMode.CHASE_CHECKING: chase_checking_terms,
        OperatingMode.SCHWAB_CHECKING: schwab_checking_terms,
        OperatingMode.SCHWAB_BROKERAGE: schwab_brokerage_terms
    }
    return terms_by_mode[mode]

def get_all_legal_categories():
    all_mode_values = [v for k, v in OperatingMode.__dict__.iteritems() if not k.startswith('__')]
    categories = set()
    for mode_value in all_mode_values:
        listed_categories_for_mode = get_terms(mode_value).keys()
        categories.update(listed_categories_for_mode)
    return categories


# PATH-RELATED STUFF

def get_base_folder_path(mode=OP_MODE):
    folder_by_mode = {
        OperatingMode.CHASE_CREDIT: "chase_extract_credit_data",
        OperatingMode.CHASE_CHECKING: "chase_extract_checking_data",
        OperatingMode.SCHWAB_CHECKING: "schwab_extract_checking_data",
        OperatingMode.SCHWAB_BROKERAGE: "schwab_extract_brokerage_data"
    }
    return os.path.abspath("/Users/mirek/" + folder_by_mode[mode])


def get_extracted_tx_folder_path():
    return os.path.join(get_base_folder_path(), "extracted_data")


def get_manually_categorized_tx_folder_path():
    return os.path.join(get_base_folder_path(), "manually_categorized_data")


def get_raw_filenames(mode=OP_MODE):
    files_by_mode = {
        OperatingMode.CHASE_CREDIT: ["mirek_2018_raw.txt", "soph_2018_raw.txt"],
        OperatingMode.CHASE_CHECKING: ["mirek_2018_checking_raw.csv", "soph_2018_checking_raw.csv"],
        OperatingMode.SCHWAB_CHECKING: ["mirek_2018_schwab_checking_raw.csv"],
        OperatingMode.SCHWAB_BROKERAGE: ["mirek_2018_schwab_brokerage_raw.csv"],
    }
    return files_by_mode[mode]


def get_extracted_tx_filepath(raw_filename, mode=OP_MODE):
    raw_suffix = "raw.txt" if mode == OperatingMode.CHASE_CREDIT else "raw.csv"
    if raw_suffix not in raw_filename:
        raise Exception("Bad raw filename: '{}'".format(raw_filename))

    tx_filename = raw_filename.replace(raw_suffix, "tx.tsv")
    return os.path.join(get_extracted_tx_folder_path(), tx_filename)


# FILE READING / WRITING

def optionally_create_dir(dir_path):
    if not os.path.exists(dir_path):
        print "Folder at '{}' doesn't exist, creating it".format(dir_path)
        os.makedirs(dir_path)


def load_from_file(filepath):
    if not os.path.exists(filepath):
        print "No file at {}, ignoring".format(filepath)
        return []

    print "Loading lines from {}".format(filepath)
    with open(filepath) as f_read:
        lines = f_read.read().splitlines()
        print "Loaded {} lines".format(len(lines))
        return lines


def write_to_file(lines, filepath):
    with open(filepath, "w") as f:
        for line in lines:
            f.write(line + "\n")
    print "\nWrote {} lines to:\n{}".format(len(lines), filepath)


# TX-FORMAT SPECIFIC STUFF

def run_extraction_loop(raw_data_folder_path, convert_to_tx_format_fn):
    """ The main loop run by the "extraction" scripts. It's behavior is controlled by OP_MODE """
    optionally_create_dir(get_extracted_tx_folder_path())

    for raw_filename in get_raw_filenames():
        raw_filepath = os.path.join(raw_data_folder_path, raw_filename)
        print "Running for '{}'".format(raw_filepath)

        raw_lines_with_header = load_from_file(raw_filepath)
        converted_tx_lines = convert_to_tx_format_fn(raw_lines_with_header)
        filtered_tx_lines = filter_tx_lines(converted_tx_lines)

        extracted_filepath = get_extracted_tx_filepath(raw_filename)
        write_to_file(filtered_tx_lines, extracted_filepath)


def filter_tx_lines(tx_lines):
    """ Remove tx outside of our desired date interval. Return filtered list """
    print "Dropping tx outside of [{}, {}]".format(FIRST_TX_DATE.date(), LAST_TX_DATE.date())
    filtered_lines = []
    for line in tx_lines:
        date_str = line.split("\t")[0] # "MM/DD/YYYY"
        date = datetime.datetime.strptime(date_str, '%m/%d/%Y')
        if date >= FIRST_TX_DATE and date <= LAST_TX_DATE:
            filtered_lines.append(line)
        else:
            print "Nuking {}".format(line)

    total_removed = len(tx_lines) - len(filtered_lines)
    print "Removed {} transactions".format(total_removed)
    return filtered_lines

def load_all_tx_lines():
    print "Loading all extracted tx lines"
    lines = []
    for raw_filename in get_raw_filenames():
        filepath_to_read = get_extracted_tx_filepath(raw_filename)
        lines += load_from_file(filepath_to_read)

    if not lines:
        raise Exception("Didn't find any tx lines, something is wrong")

    print "Loaded {} total tx lines".format(len(lines))
    check_tsv_tx_format(lines)
    return lines


# SANITY CHECKS

def check_tsv_tx_format(lines, with_category=False, mode=OP_MODE):
    if mode == OperatingMode.CHASE_CREDIT:
        leading_date_exp = r'^[0-9]{2}/[0-9]{2}' # "DD/MM",
    else:
        leading_date_exp = r'^[0-9]{2}/[0-9]{2}/[0-9]{4}' # "DD/MM/YYYY"

    number_exp = r'[-]{0,1}[0-9,]*\.[0-9]{2}' # "-1,234.56"
    end_of_line_exp = r'\t[A-Z]{1,3}$' if with_category else r'$' # "EDU"
    tsv_tx_expr = leading_date_exp + r'\t.*\t' + number_exp + end_of_line_exp

    for line in lines:
        if not re.match(tsv_tx_expr, line):
            print "Split on tab: {}".format(line.split('\t'))
            raise Exception("Line not in tsv tx format, check number decimal points: [{}]".format(line))

    print "Passed tsv tx format check"


def fix_gdocs_number_formatting(manually_categorized_lines):
    """ Google docs prefixes a zero to amts < 1 dollar, remove it to match the export format"""
    fixed_lines = []
    for line in manually_categorized_lines:
        [date_str, desc, amt_str, category] = line.split('\t')
        if amt_str[0] != "0":
            fixed_lines.append(line)
            continue

        fixed_amt_str = amt_str[1:]
        fixed_line = '\t'.join([date_str, desc, fixed_amt_str, category])
        fixed_lines.append(fixed_line)

    return fixed_lines


def tests():
    # test gdocs format fixing
    good_line = "02/21/2018\tI'M GOOD\t.88\tCNC"
    bad_line = "02/21/2018\tNEED FIXING\t0.99\tCNC"
    expected = ["02/21/2018\tI'M GOOD\t.88\tCNC", "02/21/2018\tNEED FIXING\t.99\tCNC"]
    converted = fix_gdocs_number_formatting([good_line, bad_line])
    if converted != expected:
        raise Exception("TEST FAIL, expected vs actual: \n{}\n{}".format(expected, converted))


# Tests run on import
tests()