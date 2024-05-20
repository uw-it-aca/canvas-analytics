# Copyright 2024 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import csv
import argparse

"""
This script compares the data in the RAD and CMPs files. Ensuring that
that data is generated for the same set of students and that the per-course
compass data combines to match the RAD data.
"""

RAD_FILE = None
CMPS_FILE = None
SHOW_MISMATCH = False


def get_csv_from_path(file_path):
    with open(file_path, "r") as file:
        return list(csv.DictReader(file))


def combine_cmps_courses(cmps_data):
    combined_courses = {}
    for row in cmps_data:
        uw_netid = row['uw_netid']
        if uw_netid not in combined_courses:
            combined_courses[uw_netid] = {
                'activity': get_float(row['activity']),
                'assignments': get_float(row['assignments']),
                'grades': get_float(row['grades'])
            }
        else:
            combined_courses[uw_netid]['activity'] += (
                get_float(row['activity']))
            combined_courses[uw_netid]['assignments'] += (
                get_float(row['assignments']))
            combined_courses[uw_netid]['grades'] += (
                get_float(row['grades']))
    return combined_courses


def parse_rad_data(rad_data):
    return {row['uw_netid']: {'activity': get_float(row['activity']),
                              'assignments': get_float(row['assignments']),
                              'grades': get_float(row['grades'])}
            for row in rad_data}


def get_float(value):
    try:
        return float(value)
    except ValueError:
        return 0.0


def check_mismatch(parsed_data, cmps_data, uw_netid):
    error_text = ""
    for key in ['activity', 'assignments', 'grades']:
        if parsed_data[uw_netid][key] != cmps_data[key]:
            error_text += (f"\n{key} mismatch {parsed_data[uw_netid][key]} "
                           f"{cmps_data[key]}")
    return error_text


def find_duplicates(data, key):
    seen = set()
    duplicates = set(x[key] for x in data if
                     x[key] in seen or seen.add(x[key]))
    return duplicates


def compare_netids(rad_data, combined_cmps):
    # Compare Counts
    print("rad student count", len(rad_data))
    print("cmps student count", len(combined_cmps))

    # find dupes in rad_data
    dupe_rad_netids = find_duplicates(rad_data, 'uw_netid')
    print("dupe rad  netids", len(dupe_rad_netids), list(dupe_rad_netids))

    # Netids missing from RAD
    rad_netids = []
    not_found = []
    for row in rad_data:
        uw_netid = row['uw_netid']
        rad_netids.append(uw_netid)
        if uw_netid not in combined_cmps:
            not_found.append(uw_netid)
    print("rad not in cmps", len(not_found), not_found)

    # Netids missing from CMPs
    not_found2 = [item for item in combined_cmps.keys()
                  if item not in rad_netids]
    print("cmps not in rad", len(not_found2), not_found2)


def compare_stats(parsed_rad_data, combined_cmps):
    valid = 0
    errors = []

    for uw_netid in parsed_rad_data.keys():

        cmps_stats = combined_cmps.get(uw_netid)
        if cmps_stats:
            error_text = check_mismatch(parsed_rad_data, cmps_stats, uw_netid)
            if error_text:
                errors.append(f"Mismatch {uw_netid} (rad value, "
                              f"compass value) {error_text}")
            else:
                valid += 1
        else:
            print("No CMPs data for {}".format(uw_netid))
    print("Valid students", valid)
    print("Errors", len(errors))
    if SHOW_MISMATCH:
        for error in errors:
            print(error)


def run_tests():
    combined_cmps = combine_cmps_courses(get_csv_from_path(CMPS_FILE))
    rad_data = get_csv_from_path(RAD_FILE)
    parsed_rad_data = parse_rad_data(rad_data)

    compare_netids(rad_data, combined_cmps)
    compare_stats(parsed_rad_data, combined_cmps)


""" 
Usage: 
python compare_rad_compass_files.py <rad_file> <cmps_file> [--show_mismatch]
"""
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compare RAD and CMPs files')
    parser.add_argument('rad_file',
                        type=str, help='RAD file path')
    parser.add_argument('cmps_file',
                        type=str, help='CMPs file path')
    parser.add_argument("--show_mismatch",
                        action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    RAD_FILE = args.rad_file
    CMPS_FILE = args.cmps_file
    SHOW_MISMATCH = args.show_mismatch

    run_tests()
