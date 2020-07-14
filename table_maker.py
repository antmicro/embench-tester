#!/usr/bin/env python3

import glob
import json
import os
import csv
from tabulate import tabulate


def add_to_dict(_dict, key, value):
    if (key in _dict):
        _dict[key].append(value)
    else:
        _dict[key] = [value]


def create_dict_from_json_files(path):
    main_dict = {}
    folders = []
    print(f'looking for files in path:{path}')
    files = glob.glob(path)
    print(f'found: {files}')
    for f in files:
        folders.append(os.path.basename(os.path.dirname(f)))
        file = open(f, "r")
        file_data = file.read()
        file.close()
        d = json.loads(file_data)
        for key in d.keys():
            if (key == 'detailed speed results'):
                for key2 in d[key]:
                    add_to_dict(main_dict, key2, d[key][key2])
            else:
                add_to_dict(main_dict, key, d[key])
    return folders, main_dict


def dict_to_array_of_arrays(_dict):
    main_array = []
    for key in _dict:
        t = [key]
        t.extend(_dict[key])
        main_array.append(t)
    return main_array


def create_csv_table_from_jsons(source, dest):
    header, content = create_dict_from_json_files(source)
    table = dict_to_array_of_arrays(content)
    header.insert(0, '')
    with open(dest, 'w', newline='') as output_file:
        writer = csv.writer(output_file)
        writer.writerow(header)
        writer.writerows(table)


def create_rst_table_from_jsons(source, dest):
    title = dest.split('.')
    title = title[0]
    title = title.replace('_', ' ').capitalize()
    header, content = create_dict_from_json_files(source)
    table = dict_to_array_of_arrays(content)
    header.insert(0, '')
    with open(dest, 'w') as output_file:
        output_file.write(title+'\n')
        output_file.write('*'*len(title)+'\n')
        output_file.write(tabulate(table, header, 'rst', numalign="right"))


def main():
    create_csv_table_from_jsons('./*/result.json', 'relative_results.csv')
    create_csv_table_from_jsons('./*/result_abs.json', 'absolute_results.csv')
    create_csv_table_from_jsons('./*/platform.json', 'platform.csv')
    create_rst_table_from_jsons('./*/result.json', 'relative_results.rst')
    create_rst_table_from_jsons('./*/result_abs.json', 'absolute_results.rst')
    create_rst_table_from_jsons('./*/platform.json', 'platform.rst')


if __name__ == '__main__':
    main()
