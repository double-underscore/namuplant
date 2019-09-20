import os
import csv
import configparser

LIST_FIELD = ['code', 'title', 'opt1', 'opt2', 'opt3', 'opt4', 'edit']
LOG_FIELD = ['code', 'title', 'opt1', 'opt2', 'opt3', 'opt4', 'edit', 'time', 'rev', 'error']

DOC_F = ['code', 'title', 'error', 'time', 'rev', 'index']
EDIT_F = ['index', 'opt1', 'opt2', 'opt3', 'opt4', 'edit']


def write_csv(file_name, option, field, dict_list):
    if field == 'list':
        field = LIST_FIELD
    elif field == 'log':
        field = LOG_FIELD
    with open(file_name, option, encoding='utf-8', newline='') as csv_file:
        if option == 'w':
            csv.DictWriter(csv_file, field).writeheader()
        writer = csv.DictWriter(csv_file, field)
        for dict_line in dict_list:
            writer.writerow(dict_line)


def read_csv(file_name):
    with open(file_name, 'r', encoding='utf-8', newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        return [dict(row) for row in reader]


# def read_list_csv(file_name):
#     doc_to_insert = []
#     edit_to_insert = []
#     order_done = set()
#     for row in read_csv(file_name):
#         order_t = row['code']
#         if order_t[0] == '#' or order_t[0] == '$':  # 편집 지시자
#             order = int(order_t[1:])
#             if order in order_done:
#                 if row['opt1']:  # 선두 아닌 일반
#                     edit_to_insert.append(
#                         [str(order), row['opt1'], row['opt2'], row['opt3'], row['opt4'], row['edit']])
#                 else:  # 중복 지시자
#                     doc_to_insert.append([row['code'], row['title'], ''])
#             else:
#                 order_done.add(order)
#                 edit_to_insert.append(
#                     [str(order), row['opt1'], row['opt2'], row['opt3'], row['opt4'], row['edit']])
#                 if order_t[0] == '#':  # 지시자 있는 선두
#                     doc_to_insert.append([row['code'], row['title'], ''])
#         else:  # 문서
#             doc_to_insert.append([row['code'], row['title'], ''])
#     return doc_to_insert, edit_to_insert
#
#
# def write_list_csv(file_name, docs, edits):
#     to_write = []
#     order_done = set()
#     for row in docs:
#         if '#' in row[0]:  # 편집 지시자
#             order = int(row[0][1:])
#             if order not in order_done:
#                 for edit in edits[order - 1]:  # 아예 처음
#                     to_write.append({'code': row[0], 'title': row[1],
#                                      'opt1': edit[1], 'opt2': edit[2], 'opt3': edit[3], 'opt4': edit[4], 'edit': edit[5]})
#                 order_done.add(order)
#             else:  # 중복
#                 to_write.append({'code': row[0], 'title': row[1],
#                                  'opt1': '', 'opt2': '', 'opt3': '', 'opt4': '', 'edit': ''})
#         else:  # 문서
#             to_write.append({'code': row[0], 'title': row[1],
#                              'opt1': '', 'opt2': '', 'opt3': '', 'opt4': '', 'edit': ''})
#     if len(edits) > len(order_done):  # 편집 지시자 없는 edit
#         for aaa in edits:  # todo 지시자 숫자 에러
#             if int(aaa[0][0]) not in order_done:
#                 for edit in aaa:
#                     to_write.append({'code': f'${edit[0]}', 'title': f'💡 편집사항 #{edit[0]} 💡',
#                                      'opt1': edit[1], 'opt2': edit[2], 'opt3': edit[3],  'opt4': edit[4], 'edit': edit[5]})
#     write_csv(file_name, 'w', 'list', to_write)


def new_setting():
    if not os.path.isfile('config.ini'):  # 최초 생성
        config = configparser.ConfigParser()
        config['login'] = {'UMI': '', 'UA': '', 'ID': '', 'PW': ''}
        config['setting'] = {'DELAY': 3}
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


def write_csv_(file_name, option, field):
    if field == 'doc':
        field = DOC_F
    elif field == 'edit':
        field = EDIT_F
    with open(file_name, option, encoding='utf-8', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, field)
        if option == 'w':
            writer.writeheader()
        while True:
            to_write = (yield)  # dict
            writer.writerow(to_write)


def read_csv_(file_name):
    with open(file_name, 'r', encoding='utf-8', newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            yield dict(row)
