import datetime
import os
import re

class OperatingMode(object): #pylint: disable=too-few-public-methods
    CHASE_CREDIT = 1
    CHASE_CHECKING = 2

# MODIFY THIS DEPENDING ON WHAT DATA WE'RE PROCESSING
OP_MODE = OperatingMode.CHASE_CHECKING

FIRST_TX_DATE = datetime.datetime(2018, 2, 16) # first day of joblessness
LAST_TX_DATE = datetime.datetime(2019, 1, 8) # last date we have data across all sources

# needs to live here so that there's not a circular dependency between
# "create categorization logic" and "load manual categorizations" files
CATEGORIES = ['A', 'C', 'B', 'E', 'F', 'I', 'H', 'DIG', 'TR', 'MOV', 'HMM', 'S', 'R', 'HLT', 'CNC', 'EDU', 'OT', 'BDY', 'UB']

def get_base_folder_path():
    folder_by_mode = {
        OperatingMode.CHASE_CREDIT: "chase_extract_data",
        OperatingMode.CHASE_CHECKING: "chase_extract_checking_data"
    }
    return os.path.abspath("/Users/mirek/" + folder_by_mode[OP_MODE])

def get_extracted_tx_folder_path():
    return os.path.join(get_base_folder_path(), "extracted_data")

def get_manually_categorized_tx_folder_path():
    return os.path.join(get_base_folder_path(), "manually_categorized_data")

def get_raw_filenames():
    files_by_mode = {
        OperatingMode.CHASE_CREDIT: ["mirek_2018_raw.txt", "soph_2018_raw.txt"],
        OperatingMode.CHASE_CHECKING: ["mirek_2018_checking_raw.csv", "soph_2018_checking_raw.csv"]
    }
    return files_by_mode[OP_MODE]


def get_extracted_tx_filepath(raw_filename):
    raw_suffix_by_mode = {
        OperatingMode.CHASE_CREDIT: "raw.txt",
        OperatingMode.CHASE_CHECKING: "raw.csv"
    }
    raw_suffix = raw_suffix_by_mode[OP_MODE]
    if raw_suffix not in raw_filename:
        raise Exception("Bad raw filename: '{}'".format(raw_filename))

    tx_filename = raw_filename.replace(raw_suffix, "tx.tsv")
    return os.path.join(get_extracted_tx_folder_path(), tx_filename)


# GENERIC FILE STUFF

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

def load_all_tx_lines():
    print "Loading all extracted tx lines"
    lines = []
    for raw_filename in get_raw_filenames():
        filepath_to_read = get_extracted_tx_filepath(raw_filename)
        lines += load_from_file(filepath_to_read)

    if not lines:
        raise Exception("Didn't find any tx lines, something is wrong")

    print "Loaded {} total tx lines\n".format(len(lines))
    check_tsv_tx_format(lines)
    return lines


def check_tsv_tx_format(lines, with_category=False):
    leading_date_exp = r'^[0-9]{2}/[0-9]{2}' # "MM/DD"
    number_exp = r'[-]{0,1}[0-9,]*\.[0-9]{2}' # "-1,234.56"
    end_of_line_exp = r'\t[A-Z]{1,3}$' if with_category else r'$' # "EDU"
    tsv_tx_expr = leading_date_exp + r'\t.*\t' + number_exp + end_of_line_exp

    for line in lines:
        if not re.match(tsv_tx_expr, line):
            print "Split on tab: {}".format(line.split('\t'))
            raise Exception("Line not in tsv tx format: '{}'".format(line))

    print "Passed tsv tx format check"
