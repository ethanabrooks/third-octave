#! /usr/bin/env python3

import argparse
import csv
from pathlib import Path
from typing import List

import math

parser = argparse.ArgumentParser()
parser.add_argument("--input_dir", type=Path, help="where data comes from", default=Path("~/Documents/soundlevelmeterdump").expanduser())
parser.add_argument("--output_dir", type=Path, help="where new files go", default=Path("~/Documents/soundleveldata").expanduser())
parser.add_argument("--no-wait", dest="wait", action="store_false")
parser.add_argument("--project", help="Name of project. Looks for input at input_dir/project and puts output in output_dir/project.")
args = parser.parse_args()

PROJECT_NAME = args.project
if PROJECT_NAME is None:
    PROJECT_NAME = input("Enter project name:")
OUTPUT_DIR = Path(args.output_dir, PROJECT_NAME)
INPUT_DIR = Path(args.input_dir, PROJECT_NAME)


def get_permission():
    yes = ["y", "yes"]
    no = ["n", "no"]
    while True:
        response = input().lower()
        if response in yes:
            return True
        if response in no:
            return False
        print("Please enter", "|".join(yes), "or", "|".join(no))


for directory in [INPUT_DIR, OUTPUT_DIR]:
    existed = directory.exists()
    directory.mkdir(exist_ok=True)
    if not existed:
        print("created", directory.absolute())

if args.wait:
    input(
        f"Press enter when sound level measurements have been placed in {INPUT_DIR.absolute()}",
    )

OUTPUT_THIRD = Path(OUTPUT_DIR, "third_octave.csv")
OUTPUT_OCTAVE = Path(OUTPUT_DIR, "octave.csv")


line_info = [
    (172, "Leq_third", 11),
    (188, "Max_third", 19),
    (173, "Min_third", 17),
]


def preprocess(line):
    return (
        line.replace("\n", "")
        .replace("Hz", "")
        .replace("/ ", ".")
        .replace(" ", "")
        .split(",")
    )


def get_line_number(line):
    try:
        return float(preprocess(line)[0][1:])
    except ValueError:
        return None


def octave_band(third_octave_values):
    def dB_add(a):
        return 10 * math.log10(10**(float(third_octave_values[a + 0]) / 10) +
                             10**(float(third_octave_values[a + 1]) / 10) +
                             10**(float(third_octave_values[a + 2]) / 10))

    assert len(third_octave_values) % 3 == 0
    return [dB_add(n) for n in range(0, len(third_octave_values), 3)]



filename = next(INPUT_DIR.iterdir())
with filename.open(encoding="latin-1") as f:
    for line in f:
        if get_line_number(line) == 174:
            _, *tail = preprocess(line)
            third_octave_band = ["", "", "dBA", *tail]
            break

try:
    print("Third octave band:", third_octave_band)
except NameError:
    print("Line 174 not found in", filename, "for definition of third octave band")
    exit()

with OUTPUT_THIRD.open("w", newline="") as third_csv, OUTPUT_OCTAVE.open(
    "w", newline=""
) as octave_csv:
    third_writer = csv.writer(third_csv)
    octave_writer = csv.writer(octave_csv)

    octave_header = third_octave_band[:3]
    octave_header += [
        third_octave_band[i] for i in range(4, len(third_octave_band), 3)
    ]


    for third_octave_line, category, dBA_line in line_info:
        print("Generating data for", category)
        third_writer.writerow(third_octave_band)
        octave_writer.writerow(octave_header)

        for path in INPUT_DIR.iterdir():
            print("Generating data from", path.name)
            with path.open(encoding="latin-1") as slmdl:

                for line in slmdl:
                    line_number = get_line_number(line)

                    if line_number == third_octave_line:
                        _, *third_octave_values = preprocess(line)
                    if line_number == dBA_line:
                        _, dBA, *_ = preprocess(line.replace("Hz", ""))

                third_octave_row = [path.name, category, dBA, *third_octave_values]
                third_writer.writerow(third_octave_row)
                octave_row = [
                    path.name,
                    category,
                    dBA,
                    *octave_band(third_octave_values),
                ]

                octave_writer.writerow(octave_row)

print("Files written to", OUTPUT_DIR.absolute())
