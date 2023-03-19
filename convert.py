import copy
import json
import os
import sys
import shutil
import csv
from statistics import *

def build_test_to_ident_map(all_tests_file, out_dir):
    acc = 1
    test_to_ident = {}
    with open(all_tests_file, "r") as f:
        for line in f:
            tstName = line.strip()
            test_to_ident[tstName] = "t" + str(acc)
            acc += 1

    with open(os.path.join(out_dir, "tests-ident-map.csv"), "w") as f:
        for tst in test_to_ident:
            f.write(test_to_ident[tst] + "," + tst + "\n")

    return test_to_ident

def convert_requirements_file(original_file, out_dir, test_to_ident):
    test_to_requirements = {}
    with open(original_file, "r") as f:
        for line in f:
            line_split = line.strip().split(",")
            tst = line_split[0]
            test_to_requirements[tst] = line_split[1:]

    with open(os.path.join(out_dir, "cov.info"), "w") as f:
        for tst in test_to_requirements:
            f.write(test_to_ident[tst] + ":" + " ".join(test_to_requirements[tst]) + "\n")

def convert_violations_file(original_file, out_dir, test_to_ident):
    violation_to_ident_map = {}
    test_to_violations = {}
    acc = 1
    with open(original_file, "r") as f:
        next(f)
        for line in f:
            line_split = line.strip().split(",")
            tst = line_split[0]
            test_to_violations[tst] = ["v0"] # give a default violation to prevent no formula being given when there are no violations
            for violation in line_split[1:]:
                if violation == "":
                    continue
                if not violation in violation_to_ident_map:
                    violation_to_ident_map[violation] = "v" + str(acc)
                    acc += 1
                violation_id = violation_to_ident_map[violation]
                test_to_violations[tst].append(violation_id)

    with open(os.path.join(out_dir, "fault.info"), "w") as f:
        for tst in test_to_violations:
            f.write(test_to_ident[tst] + ":" + " ".join(test_to_violations[tst]) + "\n")

    with open(os.path.join(out_dir, "violations-to-ident.csv"), "w") as f:
        f.write("violation,id")
        for violation in violation_to_ident_map:
            f.write(violation + "," + violation_to_ident_map[violation] + "\n")

def convert_times_file(original_times, out_dir, test_to_ident):
    test_to_time = {}
    with open(original_times, "r") as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            tst = row["test"]
            time = row["time(ns)"]
            if tst in test_to_ident: # if this is an actual test
                test_to_time[test_to_ident[tst]] = time

    with open(os.path.join(out_dir, "rtime.info"), "w") as f:
        for tst in test_to_time:
            f.write(tst + ":" + test_to_time[tst] + "\n")

def main(all_tests_file, original_mapping, original_violations, original_times, out_dir):
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    test_to_ident = build_test_to_ident_map(all_tests_file, out_dir)
    convert_requirements_file(original_mapping, out_dir, test_to_ident)
    convert_violations_file(original_violations, out_dir, test_to_ident)
    convert_times_file(original_times, out_dir, test_to_ident)

if __name__ == '__main__':
    if len(sys.argv) != 6:
        print("Usage: " + sys.argv[0] + " all-tests-file original-mapping original-violations original-times out-dir")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
