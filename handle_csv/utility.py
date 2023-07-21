import csv
from email.policy import default
import pandas as pd
from os.path import isfile, join, split, splitext, isdir, dirname
from os import mkdir, listdir
import math
from dateutil.parser import parse
from time import time
from typing import Union


def get_last_folder_dir(directory: str, crefolder: bool, cname: str) -> str:
    """Return the last upper folder, and optionally create a new folder under it and return the new one."""
    last_folder_directory = directory if isdir(
        directory) else dirname(directory)
    if crefolder is True:
        last_folder_directory = join(last_folder_directory, cname)
        try:
            mkdir(last_folder_directory)
        except OSError:
            pass
    else:
        pass
    return last_folder_directory


def open_csvfile(directory, encoding='utf-8-sig') -> list:
    """Open csv file, return a list which consist of lines."""
    default_encodings = [encoding, 'utf-8-sig', 'gbk', 'gb18030']
    for encode in default_encodings:
        try:
            with open(directory, mode='r', encoding=encode, newline='') as csvfile:
                reader = csv.reader(csvfile)
                csvfile_lines = [row for row in reader]
            break
        except UnicodeDecodeError:
            continue
    return csvfile_lines


def convert_excel_to_csv(directory, crefloder=True) -> str:
    """Convert excel file to csv file."""
    import xlrd
    excel_extentions = ['.xls', '.xlsx']
    if directory[directory.rfind('.'):] not in excel_extentions:
        return directory
    last_folder_directory = get_last_folder_dir(
        directory, crefolder=crefloder, cname='converted_csv_from_excel')
    file_name = list(split(directory))[1]
    write_file_name = file_name[:file_name.rfind('.')] + '.csv'
    write_file_directory = join(last_folder_directory, write_file_name)
    try:
        read_file = pd.read_excel(directory, header=None)
    except xlrd.compdoc.CompDocError:
        wb = xlrd.open_workbook(directory, ignore_workbook_corruption=True)
        read_file = pd.read_excel(wb, header=None)
    except ValueError:
        print("未能成功打开Excel文件：", directory)
        raise
    read_file.to_csv(write_file_directory, index=False, header=None)
    return write_file_directory


def write_csvfile(directory, csvfile_lines, filename=None, combine=False, crefloder=True, encoding='utf-8') -> str:
    """Write the handled csv_file, to origin_filename_done.csv."""
    # 如filename未输入，则默认写入文件名为：/output.csv；否则：/文件名.csv。
    write_file_name = 'output.csv' if filename is None else (
        splitext(split(directory)[1])[0]+'.csv')
    # 如参数crefolder为True，则在最后一级文件夹下，新建文件夹output。并返回(新建文件夹后)最后一级文件夹名。
    last_folder_directory = get_last_folder_dir(
        directory, crefolder=crefloder, cname='output')
    write_file_directory = join(last_folder_directory, write_file_name)
    # 如为拼接模式，且文件存在时(即已有首次写入)，后续的写入：1)删去首行(字段行)，2)添入已存在文件。
    if combine:
        write_mode = 'a'
        if isfile(write_file_directory):
            csvfile_lines = csvfile_lines.copy()[1:]
    else:
        write_mode = 'w'
    with open(write_file_directory, mode=write_mode, encoding=encoding, newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(csvfile_lines)
    print(f"写入CSV完成，文件路径为：{write_file_directory}")
    return write_file_directory


def partition_list_even(a_list: list, interval: int) -> list:
    """
    Partition evenly a list into smaller ones.
    :param a_list: list, list to be partitioned
    :param interval: int, number of units in each even piece
    """
    lens = len(a_list)
    share = math.ceil(lens/interval)
    a_list_partitioned = [
        a_list[interval * i: interval * (i+1)] for i in range(share)]
    return a_list_partitioned


def remove_blankstr_from_a_line(line, blankstr=' ') -> list:
    line_tailored = [i for i in line.copy() if i not in blankstr]
    return line_tailored


def remove_letters(str1, str2) -> str:
    # 也可以用str.replace+循环实现。
    if type(str1) is str:
        s = set(str2)
        return "".join([char for char in str1 if char not in s])
    else:
        return str1


def get_filesdir_under_a_folder(folder_dir: str, *extensions: str) -> list:
    """
    Return all file directories, as a list, with given extensions and under a given folder.
    :param folder_dir: str
    :param extentions: str, wanted file extensions
    """
    if not isdir(folder_dir):
        raise OSError(f'It is not a valid directory: {folder_dir}')
    if extensions == ():
        filesdir = [join(folder_dir, f) for f in listdir(folder_dir)]
    else:
        filesdir = [join(folder_dir, f) for f in listdir(
            folder_dir) if splitext(f)[1] in list(extensions)]
    return filesdir


def filter_filesdir_with_extensions(
    a_folder_or_files_list: Union[str, list[str]],
    *extensions: str,
    ) -> list:
    """
    Return all file directories, as a list, with given extensions, a given folder or a list of file directories.
    :param folder_dir: str
    :param extentions: str, wanted file extensions
    """
    filesdir = []
    # 如输入1个文件夹路径，则抓取文件夹下每个恰当后缀文件的路径。
    if isinstance(a_folder_or_files_list, str):
        if isdir(a_folder_or_files_list):
            filesdir = get_filesdir_under_a_folder(a_folder_or_files_list, *extensions)
    # 如输入为文件路径的List，则过滤去除非文件和非恰当后缀文件。
    elif isinstance(a_folder_or_files_list, list):
        filesdir = [filedir for filedir in a_folder_or_files_list if isfile(filedir) and filedir.endswith(extensions)]
    return filesdir


def is_date(string: str, fuzzy=False) -> bool:
    """
    Return whether the string can be interpreted as a date.
    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try:
        parse(string, fuzzy=fuzzy)
        return True
    except ValueError:
        return False


def timer_func(func):
    """This function shows the execution time of the function object passed"""
    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        print(f'\tFunction {func.__name__!r} executed in {(t2-t1):.1f}s')
        return result
    return wrap_func


def pre_dividing_line(func):
    """Print a line of '************' before any prints of the wrapped function."""
    def wrap_func(*args, **kwargs):
        print('*'*50)
        result = func(*args, **kwargs)
        return result
    return wrap_func
