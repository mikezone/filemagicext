# -*- coding: utf-8 -*-
import filemagicext
import os

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
    from collections import defaultdict
    count_dict = defaultdict(int)

    if file_info.is_word():
        count_dict['word_count'] += 1
    elif file_info.is_excel():
        count_dict['excel_count'] += 1
    elif file_info.is_ppt():
        count_dict['ppt_count'] += 1
    elif file_info.is_pdf():
        count_dict['pdf_count'] += 1
    elif file_info.is_rtf():
        count_dict['rtf_count'] += 1
    elif file_info.is_html():
        count_dict['html_count'] += 1
    elif file_info.is_script():
        count_dict['script_count'] += 1
    elif file_info.is_other_text():
        count_dict['othertext_count'] += 1
    elif file_info.is_linux_executable():
        count_dict['linux_executable_count'] += 1
    elif file_info.is_pe():
        count_dict['pe_count'] += 1
    elif file_info.is_7_zip():
        count_dict['7zip_count'] += 1
    elif file_info.is_rar():
        count_dict['rar_count'] += 1
    elif file_info.is_tar():
        count_dict['tar_count'] += 1
    elif file_info.is_other_zip():
        count_dict['otherzip_count'] += 1
    else:
        count_dict['others_count'] += 1

    from collections import Counter
    # print(Counter(count_dict))
    print(dict(count_dict))