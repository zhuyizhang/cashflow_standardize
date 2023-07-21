from os.path import split
import json
from . import utility


class CsvFileLines:
    @utility.pre_dividing_line
    def __init__(self, directory, encoding='utf-8-sig'):
        """Open a CsvFile. Store its lines, filename, directory for further use.

        :param directory: str, directory of CsvFile to load in
        :param encoding: str, encoding of CsvFile to load in
        """
        self.directory = directory
        self.lines = utility.open_csvfile(directory, encoding=encoding)
        self.filename = split(directory)[1][:-4]
        self.writen_directory = None
        print(f'已载入csv文件<文件路径>为： {directory} ')

    def write_csvfile(self, directory=None, filename=None, lines=None, combine=False, crefloder=True, encoding='utf-8'):
        if directory is None:
            directory = self.directory
        if lines is None:
            lines = self.lines
        self.writen_directory = utility.write_csvfile(
            directory, csvfile_lines=lines, filename=filename, combine=combine, crefloder=crefloder, encoding=encoding)

    def choose_columns(self, column_index: list):
        """
        Choose columns that you want to keep.
        :param column_index: list, column indexes that you want to keep
        """
        transposed = list(zip(*self.lines))
        transposed_tailored = [transposed[i] for i in column_index]
        self.lines = list(zip(*transposed_tailored))

    def partition_csvfile(self, interval):
        """
        Partition evenly the file and write each piece down.
        :param interval: number of lines you want each piece has
        """
        lines_partitioned = utility.partition_list_even(self.lines, interval)
        for i in range(len(lines_partitioned)):
            directory = self.directory[:-4] + f'_part{i + 1}' + self.directory[-4:]
            filename = self.directory[:-4] + f'_part{i + 1}'
            self.write_csvfile(directory, lines=lines_partitioned[i], filename=filename)
