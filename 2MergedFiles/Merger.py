import os
import glob
import csv

my_dir = os.getcwd()

file_list = glob.glob(my_dir.__str__() + "\\*.csv")  # Include slash or it will search in the wrong directory!!
print(*file_list, sep='\n')
fieldnames = []
# noinspection SpellCheckingInspection
for filename in file_list:
    with open(filename, "r", encoding='utf8', newline="") as f_in:
        reader = csv.reader(f_in)
        headers = next(reader)
fieldnames = headers

undetected_fields = ['Course_Delivery_Mode', 'FREE_TAFE', 'Fees', 'Course Delivery Mode', 'FREE TAFE']
for i in undetected_fields:
    if i not in fieldnames:
        fieldnames.append(i)

with open("output.csv", "w", encoding='utf8', newline="") as f_out:
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()  # write header based on `fieldnames`
    for filename in file_list:
        with open(filename, 'r', encoding='utf8', newline='') as f_in:
            reader = csv.DictReader(f_in)
            for line in reader:
                writer.writerow(line)
