import argparse
import csv
import os

import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('input_dir', help='where data comes from')
parser.add_argument('output_dir', help='where new files go')
args = parser.parse_args()

OUTPUT_THIRD = os.path.join(args.output_dir, 'third_octave.csv')
OUTPUT_OCTAVE = os.path.join(args.output_dir, 'octave.csv')

line_info = [
    (172, "Leq_third", 11),
    (188, "Max_third", 19),
    (173, "Min_third", 17),
]


def preprocess(line):
    return line.replace("\n", "").replace('Hz', '').replace("/ ", ".").replace(
        " ", "").split(",")


def get_line_number(line):
    try:
        return float(preprocess(line)[0][1:])
    except ValueError:
        return None


def octave_band(third_octave_values):
    def dB_add(a):
        return 10 * np.log10(10**(float(third_octave_values[a + 0]) / 10) +
                             10**(float(third_octave_values[a + 1]) / 10) +
                             10**(float(third_octave_values[a + 2]) / 10))

    assert len(third_octave_values) % 3 == 0
    return [dB_add(n) for n in range(0, len(third_octave_values), 3)]

filename = os.listdir(args.input_dir)[0]
with open(os.path.join(args.input_dir, filename), encoding="latin-1") as f:
    for line in f:
        if get_line_number(line) == 174:
            third_octave_band = ['', '', "dBA"] + preprocess(line)[1:]
            break

try:
    print('Third octave band:', third_octave_band)
except NameError:
    print('Line 174 not found in', filename,
          'for definition of third octave band')
    exit()

with open(OUTPUT_THIRD, "w", newline="") as third_csv,\
        open(OUTPUT_OCTAVE, "w", newline="") as octave_csv:
    third_writer = csv.writer(third_csv)
    octave_writer = csv.writer(octave_csv)

    octave_header = third_octave_band[:3]
    octave_header += [
        third_octave_band[i] for i in range(4, len(third_octave_band), 3)
    ]

    for third_octave_line, category, dBA_line in line_info:
        print('Generating data for', category)
        third_writer.writerow(third_octave_band)
        octave_writer.writerow(octave_header)

        for file_name in os.listdir(args.input_dir):
            print('Generating data from', file_name)
            path = os.path.join(args.input_dir, file_name)
            with open(path, encoding="latin-1") as slmdl:

                for line in slmdl:
                    line_number = get_line_number(line)

                    if line_number == third_octave_line:
                        third_octave_values = preprocess(line)[1:]
                    if line_number == dBA_line:

                        dBA = preprocess(line.replace('Hz', ''))[1]

                third_octave_row = [file_name, category, dBA
                                    ] + third_octave_values
                third_writer.writerow(third_octave_row)
                octave_row = [file_name, category, dBA] + \
                    octave_band(third_octave_values)

                octave_writer.writerow(octave_row)

print('Files written to', os.path.realpath(args.output_dir))
