#!/usr/bin/env python3

import json
import os
import csv
import argparse
from jinja2 import Environment, PackageLoader, select_autoescape


def add_to_dict(_dict, key, value):
    if (key in _dict):
        _dict[key].append(value)
    else:
        _dict[key] = [value]


def list_of_dicts_to_dict_of_lists(list_dict):
    dict_list = {}
    nested_dicts = []
    for i in range(len(list_dict)):
        for key, value in list_dict[i].items():
            add_to_dict(dict_list, key, value)
            if isinstance(value, dict):
                nested_dicts.append(key)
    nested_dicts = set(nested_dicts)
    for k in nested_dicts:
        dict_list[k] = list_of_dicts_to_dict_of_lists(dict_list[k])

    return dict_list


def create_dict_from_json_files(files, skipped_keys=[]):
    file_list = []
    main_dict = {}
    print(f'processing files: {files}')
    for f in files:
        file = open(f, "r")
        file_data = file.read()
        file.close()
        d = json.loads(file_data)
        file_list.append(d)
    main_dict = list_of_dicts_to_dict_of_lists(file_list)
    for key in skipped_keys:
        main_dict.pop(key, None)
    return main_dict


def get_folder_names_from_file_paths(files):
    folders = []
    for f in files:
        folders.append(os.path.basename(os.path.dirname(f)))
    return folders


def dict_to_array_of_arrays(_dict):
    main_array = []
    for key in _dict:
        t = [key]
        t.extend(_dict[key])
        main_array.append(t)
    return main_array


def scan_for_files(dirs, file_name):
    sources = [d + '/' + file_name for d in dirs]
    files = []
    for source in sources:
        if os.path.isfile(source):
            files.append(source)
    return files


def create_csv_table_from_dict(_dict, header, po):
    table = dict_to_array_of_arrays(_dict)
    with open(po, 'w+', newline='') as output_file:
        writer = csv.writer(output_file)
        writer.writerow(header)
        writer.writerows(table)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--dirs', nargs='+',
                        help='List of folders to search in')
    parser.add_argument('--out-dir', help="Path to output folder")
    parser.add_argument('--templates-dir',
                        help='Path to folder with templates')
    parser.add_argument('--exclude', nargs='*', help='File extensions\
to be excluded from template folder', default=[])
    args = parser.parse_args()

    env = Environment(
        loader=PackageLoader('table_maker', args.templates_dir),
        autoescape=select_autoescape(args.exclude)
    )

    config_file = open('table_creation_config.json')
    run_config = json.load(config_file)
    config_file.close()
    for config in run_config['tables']:
        files = scan_for_files(args.dirs, config['file_names'])
        if 'skip' in config:
            main = create_dict_from_json_files(files, config['skip'])
        else:
            main = create_dict_from_json_files(files)
        
        folder_names = get_folder_names_from_file_paths(files)
        header = config['corner'] + folder_names
        if 'header' in config:
            header = config['header']
        
        csv_data = {}
        if 'keys' in config:
            for i in config['keys']:
                temp = main
                for j in i:
                    temp = temp[j]
                csv_data.update(temp)
        else:
            csv_data = main

        if 'mult_value' in config:
            for key in csv_data.keys():
                if key not in config["exclude_mult"]:
                    for i in range(len(csv_data[key])):
                        csv_data[key][i] *= config['mult_value']
                        csv_data[key][i] = round(csv_data[key][i],2)
        
        output = args.out_dir + '/' + config['output_file_csv']
        create_csv_table_from_dict(csv_data, header, output)
        
        if 'template_name' in config:
            template = env.get_template(config['template_name'])
            config['template_dict'].update(main)
            with open(args.out_dir + '/' + config['output_file_rst'], 'w+') as out:
                out.write(template.render(config['template_dict']))


if __name__ == '__main__':
    main()
