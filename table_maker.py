#!/usr/bin/env python3

import glob
import json
import os
import csv
import argparse
from tabulate import tabulate


def add_to_dict(_dict, key, value):
    if (key in _dict):
        _dict[key].append(value)
    else:
        _dict[key] = [value]


def create_dict_from_json_files(files):
    main_dict = {}
    folders = []
    print(f'processing files: {files}')
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


def create_csv_table_from_jsons(dirs, source, dest):
    sources = [d + '/' + source for d in dirs]
    header, content = create_dict_from_json_files(sources)
    table = dict_to_array_of_arrays(content)
    header.insert(0, '')
    with open(dest, 'w', newline='') as output_file:
        writer = csv.writer(output_file)
        writer.writerow(header)
        writer.writerows(table)


def create_rst_table_from_jsons(dirs, source, dest):
    title = dest.split('.')
    title = title[0]
    title = title.replace('_', ' ').capitalize()

    sources = [d + '/' + source for d in dirs]
    header, content = create_dict_from_json_files(sources)
    table = dict_to_array_of_arrays(content)
    header.insert(0, '')
    with open(dest, 'w') as output_file:
        output_file.write(title+'\n')
        output_file.write('*'*len(title)+'\n')
        output_file.write(tabulate(table, header, 'rst', numalign="right"))


def create_platform_rst_from_jsons(dirs, source):
    title = {}
    title[0] = "Platform"
    title[1] = "Used tools"
    title[2] = "Toolchains:"
    title[3] = "Other tools:"

    sources = [d + '/' + source for d in dirs]
    cores, content = create_dict_from_json_files(sources)
    sha1s = dict_to_array_of_arrays(content)[0]
    header = ["Core", "Core sha1"]
    table = []
    for i in range(len(cores)):
        table.append([cores[i], sha1s[i+1]])
    platform_dict = {}
    for key in content.keys():
        if key == 'CPU_sha1':
            continue
        platform_dict[key] = set(content[key])

    toolchain_to_arch = {
        "riscv64": "RISC-V",
        "lm32": "LM32",
        "or1k": "OpenRISC",
        "powerpc64le": "OpenPOWER"
    }

    with open('platform.rst', 'w') as output_file:
        output_file.write(title[0]+'\n')
        output_file.write('*'*len(title[0])+'\n')
        output_file.write(tabulate(table, header, 'rst')+'\n\n')
        output_file.write(title[1]+'\n')
        output_file.write('*'*len(title[1])+'\n')

        output_file.write(title[2]+'\n')
        output_file.write('#'*len(title[2])+'\n')
        for i in platform_dict["toolchain"]:
            i = i.split("Copyright")[0].replace("\n", " ")
            t = i.split("-")[0]
            output_file.write(f':{toolchain_to_arch[t]}:\n')
            output_file.write(f'\t{i}\n\n')
        output_file.write("\n")

        output_file.write(title[3]+'\n')
        output_file.write('#'*len(title[3])+'\n')

        for key in platform_dict.keys():
            if key == "toolchain":
                continue
            else:
                output_file.write(f':{key}:\n')
                for i in platform_dict[key]:
                    i = i.split("Copyright")[0].replace("\n", " ")
                    t = i.split("-")[0]
                    output_file.write(f'\t{i}\n\n')


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('dirs', nargs='+', help='List of folders to search in')
    args = parser.parse_args()

    create_csv_table_from_jsons(args.dirs, 'result.json', 'relative_results.csv')
    create_csv_table_from_jsons(args.dirs, 'result_abs.json', 'absolute_results.csv')
    create_csv_table_from_jsons(args.dirs, 'platform.json', 'platform.csv')
    create_rst_table_from_jsons(args.dirs, 'result.json', 'relative_results.rst')
    create_rst_table_from_jsons(args.dirs, 'result_abs.json', 'absolute_results.rst')
    create_platform_rst_from_jsons(args.dirs, 'platform.json')


if __name__ == '__main__':
    main()
