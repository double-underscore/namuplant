import os
import csv
import configparser

DOC_F = ['code', 'title', 'rev', 'time', 'index', 'error']
EDIT_F = ['index', 'opt1', 'opt2', 'opt3', 'opt4', 'edit']


def new_setting():
    if not os.path.isfile('config.ini'):  # 최초 생성
        config = configparser.ConfigParser()
        config['login'] = {'UMI': '', 'UA': '', 'ID': '', 'PW': ''}
        config['setting'] = {'DELAY': 3.0}
        with open('config.ini', 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    files = (('doc_list.csv', DOC_F), ('doc_log.csv', DOC_F), ('edit_list.csv', EDIT_F), ('edit_log.csv', EDIT_F))
    for name, field in files:
        if not os.path.isfile(name):  # 최초 생성
            with open(name, 'w', encoding='utf-8', newline='') as csv_file:
                csv.DictWriter(csv_file, field).writeheader()


def read_setting(file_name):
    config = configparser.ConfigParser()
    config.read(file_name, encoding='utf-8')

    return {'UMI': config['login']['UMI'],
            'UA': config['login']['UA'],
            'ID': config['login']['ID'],
            'PW': config['login']['PW'],
            'DELAY': float(config['setting']['DELAY'])
            }


def write_csv(file_name, option, field):
    field = {'doc': DOC_F, 'edit': EDIT_F}[field]
    with open(file_name, option, encoding='utf-8', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, field)
        if option == 'w':
            writer.writeheader()
        while True:
            to_write = (yield)  # dict
            writer.writerow(to_write)


def read_csv(file_name):
    with open(file_name, 'r', encoding='utf-8', newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            yield dict(row)
