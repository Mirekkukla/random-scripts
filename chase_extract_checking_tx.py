# chase pdf are wonky-formatted so we can't extract tx amouts - just dates and descriptions
# we'll process a csv export, but that only include 5 trailing month
# beyond that, we'll extract dates and descriptions from the pdfs, but have to enter the transaction amounts manually


import re
import os
import chase_utils as utils

RAW_DATA_FOLDER_PATH = os.path.join(utils.get_base_folder_path(), "raw_data")

def main():
    utils.optionally_create_dir(utils.get_extracted_tx_folder_path())

    # visually sanity check the raw data: grep -n "Payment Due Date" soph_2018_raw.txt
    # you should see 1-2 dates for each month (depending on statement format)
    for raw_filename in utils.get_raw_filenames():
        raw_filepath = os.path.join(RAW_DATA_FOLDER_PATH, raw_filename)
        print "Running for '{}'".format(raw_filepath)

        raw_matches = extract_tx_lines(raw_filepath)
        matches = filter_leading_tx_lines(raw_matches)
        print "\n".join(matches)

        tab_delimited_matches = convert_to_tsv(matches)

        extracted_filename = utils.get_extracted_tx_filename(raw_filename)
        extracted_filepath = os.path.join(utils.get_extracted_tx_folder_path(), extracted_filename)
        write_to_file(tab_delimited_matches, extracted_filepath)


def get_raw_filepaths(): # move to raw?
    filenames = ["mirek_2018_raw.txt", "soph_2018_raw.txt"]
    return [os.path.join(RAW_DATA_FOLDER_PATH, name) for name in filenames]

def extract_tx_lines(file_to_read):
    lines = None
    with open(file_to_read, "r") as f_read:
        lines = f_read.read().splitlines()

    matches = []
    for line in lines:
        exp = r'^[0-9]{2}/[0-9]{2}.*\ [-]{0,1}[0-9,]*\.[0-9]{2}$'
        if re.match(exp, line):
            matches.append(line)
            continue

    return matches


def filter_leading_tx_lines(lines):
    """
    HACK: we want to ignore all tx <= 2/15 (2018), but the tx data
    starts on 12/08 (2018). Since tx rows don't have a date, we'll need
    to do some hackery to remove the leading stuff

    This logic depends on the given lines being chronological
    Returns the "filtered" list of tx lines
    """
    print "Removing leading tx prior to 2/15/18"
    for i, line in enumerate(lines):

        # more hackery: the "payment" line comes before the 12/15/18 txs
        if "AUTOMATIC PAYMENT" in line:
            continue

        date_str = line.split(" ")[0] # "MM/DD"
        if date_str >= "02/15" and date_str <= "12/00":
            print "Removed {} tx\n".format(i)
            return lines[i:]
        print "Nuking " + line

    print "Nothing to filter\n"
    return []


def convert_to_tsv(matches):
    clean_lines = []
    for line in matches:
        split_on_space = line.split(" ")
        date = split_on_space[0]
        desc = " ".join(split_on_space[1:-1])
        amt = split_on_space[-1]

        clean_line = "{}\t{}\t{}".format(date, desc, amt)
        clean_lines.append(clean_line)

    return clean_lines


def write_to_file(matches, file_to_write):
    with open(file_to_write, "w") as f_write:
        for tx_line in matches:
            f_write.write(tx_line + "\n")

    print "Wrote {} tx to '{}'".format(len(matches), file_to_write)


if __name__ == '__main__':
    if utils.OP_MODE != utils.OperatingMode.CHASE_CHECKING:
        raise Exception("Can only run in chase checking mode")
    main()