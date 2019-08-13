import os
import csv
import configparser

LIST_FIELD = ['code', 'title', 'opt1', 'opt2', 'opt3', 'edit']
LOG_FIELD = ['code', 'title', 'opt1', 'opt2', 'opt3', 'edit', 'time', 'rev', 'error']


def write_csv(file_name, option, field, dict_list):
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


def read_list_csv(file_name):
    lists = read_csv(file_name)
    doc_to_insert = []
    edit_to_insert = []
    order_done = set()
    for i in range(len(lists)):
        order_t = lists[i]['code']
        if order_t[0] == '#' or order_t[0] == '$':  # 편집 지시자
            order = int(order_t[1:])
            if order in order_done:
                if lists[i]['opt1']:  # 선두 아닌 일반
                    edit_to_insert.append(
                        [str(order), lists[i]['opt1'], lists[i]['opt2'], lists[i]['opt3'], lists[i]['edit']])
                else:  # 중복 지시자
                    doc_to_insert.append([lists[i]['code'], lists[i]['title'], ''])
            else:
                order_done.add(order)
                edit_to_insert.append(
                    [str(order), lists[i]['opt1'], lists[i]['opt2'], lists[i]['opt3'], lists[i]['edit']])
                if order_t[0] == '#':  # 지시자 있는 선두
                    doc_to_insert.append([lists[i]['code'], lists[i]['title'], ''])
        else:  # 문서
            doc_to_insert.append([lists[i]['code'], lists[i]['title'], ''])
    return {'doc': doc_to_insert, 'edit': edit_to_insert}


def write_list_csv(file_name, docs, edits):
    to_write = []
    order_done = set()
    for i in range(len(docs)):
        if '#' in docs[i][0]:  # 편집 지시자
            order = int(docs[i][0][1:])
            if order not in order_done:
                for edit in edits[order - 1]:  # 아예 처음
                    to_write.append({'code': docs[i][0], 'title': docs[i][1],
                                     'opt1': edit[1], 'opt2': edit[2], 'opt3': edit[3], 'edit': edit[4]})
                order_done.add(order)
            else:  # 중복
                to_write.append({'code': docs[i][0], 'title': docs[i][1],
                                 'opt1': '', 'opt2': '', 'opt3': '', 'edit': ''})
        else:  # 문서
            to_write.append({'code': docs[i][0], 'title': docs[i][1],
                             'opt1': '', 'opt2': '', 'opt3': '', 'edit': ''})
    if len(edits) > len(order_done):  # 편집 지시자 없는 edit
        for aaa in edits:
            if int(aaa[0][0]) not in order_done:
                for edit in aaa:
                    to_write.append({'code': f'${edit[0]}', 'title': f'💡 편집사항 #{edit[0]} 💡',
                                     'opt1': edit[1], 'opt2': edit[2], 'opt3': edit[3], 'edit': edit[4]})
    write_csv(file_name, 'w', LIST_FIELD, to_write)


def new_setting():
    if not os.path.isfile('config.ini'):  # 최초 생성
        config = configparser.ConfigParser()
        config['login'] = {'UMI': '', 'UA': '', 'ID': '', 'PW': ''}
        config['setting'] = {'DELAY': 3}
        with open('config.ini', 'w', encoding='utf-8') as configfile:
            config.write(configfile)
    if not os.path.isfile('doc_list.csv'):  # 최초 생성
        with open('doc_list.csv', 'w', encoding='utf-8', newline='') as csv_file:
            csv.DictWriter(csv_file, LIST_FIELD).writeheader()
    if not os.path.isfile('edit_log.csv'):  # 최초 생성
        with open('edit_log.csv', 'w', encoding='utf-8', newline='') as csv_file:
            csv.DictWriter(csv_file, LOG_FIELD).writeheader()


def read_setting(file_name):
    config = configparser.ConfigParser()
    config.read(file_name, encoding='utf-8')

    return {'UMI': config['login']['UMI'],
            'UA': config['login']['UA'],
            'ID': config['login']['ID'],
            'PW': config['login']['PW'],
            'DELAY': float(config['setting']['DELAY'])
            }
