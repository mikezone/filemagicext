# -*- coding: utf-8 -*-
import filemagicext
import os

from collections import defaultdict

count_dict = defaultdict(int)

method_key_map = {
    'is_word': 'word_count',
    'is_excel': 'excel_count',
    'is_ppt': 'ppt_count',
    'is_pdf': 'pdf_count',
    'is_rtf': 'rft_count',
    'is_html': 'html_count',
    'is_script': 'script_count',
    'is_other_text': 'othertext_count',
    'is_linux_executable': 'linux_executable_count',
    'is_pe': 'pe_count',
    'is_7_zip': '7zip_count',
    'is_rar': 'rar_count',
    'is_tar': 'tar_count',
    'is_other_zip': 'otherzip_count',
}

def statistic_file_for_dict(file_info, default_dict_):
    for method_name, key in method_key_map.iteritems():
        method = getattr(file_info, method_name)
        if method():
            default_dict_[key] += 1
            return
    else:
        default_dict_['others_count'] += 1
        return


# 'others_count':


dir = os.getcwd() + '/alotfiles'
for i in os.listdir(dir):
    file_path = os.path.join(dir, i)
    if not os.path.isfile(file_path):
        continue
    file_info = filemagicext.from_file(file_path)
    # print(file_path, file_info._base_info)
    # if file_info.is_7_zip():
    # if file_info.is_word():
    #     print(file_path, 'is word')is
    # if file_info.is_word():
    #     count_dict['word_count'] += 1
    # elif file_info.is_excel():
    #     count_dict['excel_count'] += 1
    # elif file_info.is_ppt():
    #     count_dict['ppt_count'] += 1
    # elif file_info.is_pdf():
    #     count_dict['pdf_count'] += 1
    # elif file_info.is_rtf():
    #     count_dict['rtf_count'] += 1
    # elif file_info.is_html():
    #     count_dict['html_count'] += 1
    # elif file_info.is_script():
    #     count_dict['script_count'] += 1
    # elif file_info.is_other_text():
    #     count_dict['othertext_count'] += 1
    # elif file_info.is_linux_executable():
    #     count_dict['linux_executable_count'] += 1
    # elif file_info.is_pe():
    #     count_dict['pe_count'] += 1
    # elif file_info.is_7_zip():
    #     count_dict['7zip_count'] += 1
    # elif file_info.is_rar():
    #     count_dict['rar_count'] += 1
    # elif file_info.is_tar():
    #     count_dict['tar_count'] += 1
    # elif file_info.is_other_zip():
    #     count_dict['otherzip_count'] += 1
    # else:
    #     count_dict['others_count'] += 1
    # print(file_path, file_info._base_info)
    statistic_file_for_dict(file_info, count_dict)

print(dict(count_dict))