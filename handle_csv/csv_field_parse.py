from . import csv_file_lines
from . import utility
import re


class CsvFieldParse(csv_file_lines.CsvFileLines):
    """Determine and parse head, body, tail of a csv file."""
    
    not_null_field = None

    @utility.timer_func
    def __init__(self, directory, encoding='utf-8-sig') -> None:
        super().__init__(directory, encoding)

        # 以下data_attribute，在初始化时完成赋值。
        self.start_line_index = self.get_start_line_index()
        self.fields = self.lines[self.start_line_index]
        self.end_line_index = self.get_end_line_index()
        print(f"已获取<表体首行>,为第 {self.start_line_index} 行；已获取<表体尾行>为第 {self.end_line_index} 行")
        self.body_dict = self.get_body_dict()
        self.head_tail_dict = self.get_head_tail_dict()

    def get_start_line_index(self) -> int:
        """Return the index of the first line of the file body."""
        # 取前100行的非空值的个数（默认表头不可能超过100行），形成列表lens_list。
        lens_list = [len(utility.remove_blankstr_from_a_line(line)) for line in self.lines[:100]]
        # 个数列表中，第一条值为最大值的，就是表体首行（即字段行）。
        if min(lens_list) < max(lens_list):
            start_line_index = lens_list.index(max(lens_list))
        # 个数列表中，如元素均相等，则默认第1行为表体首行。
        else:
            start_line_index = 0
        return start_line_index

    def get_end_line_index(self) -> int:
        """Return the index of the last line of the file body.

        :param key_field_name: str, a field which class commonly has and has no extra cells below the end line.
        """
        # 返回：表体尾行。
        # 逻辑一：字段行（表体首行）后的行，如有其元素（列）数小于字段行（表体首行）的，定位其为表体尾行。
        lens_list = [len(line) for line in self.lines[self.start_line_index:]]
        # 注解：当某行列数小于字段数，且列数小于等于10，标记-1以便后续判定为表体尾行。
        lens_list = [-1 if ((i - len(self.fields)) < 0 and i <= 10) else 0 for i in lens_list.copy()]
        try:
            end_line_index = lens_list.index(-1) + self.start_line_index
            return end_line_index
        except ValueError:
            pass
        # 逻辑二：如Csv是由Excel转换得来，Csv每行元素数都相等。则需定位关键列，首个值为空的行，定位其为表体尾行。
        if self.not_null_field is None:
            not_null_field = self.fields[0]
        else:
            not_null_field = self.not_null_field
        not_null_column = []
        for i, v in enumerate(self.fields):
            if not_null_field in v:
                body_lines = self.lines[self.start_line_index:]
                not_null_column = [line[i] for line in body_lines]
                break
            else:
                continue
        # 对关键字段，找空值。找得到空值，取空值行号；找不到空值，取末行号。
        try:
            end_line_index = self.start_line_index + not_null_column.index('')
        except ValueError:
            end_line_index = self.start_line_index + len(not_null_column)
        return end_line_index

    def get_body_dict(self) -> dict:
        """Return a dictionary of file body, with self.fields being keys and lists of field values being values."""
        lines_tailored = self.lines[self.start_line_index:self.end_line_index]
        # 注解：转置包含不等长向量的矩阵，如需要保留最长向量的维度，需用itertools.zip_longest。
        from itertools import zip_longest
        # 注解：为什么包含字段行转置填充、再转回、再去字段行转置？为了严格确保field_values列数与field_keys列数相等。
        fields_values = list(zip_longest(*lines_tailored[0:], fillvalue=''))
        fields_values = list(zip(*fields_values.copy()))
        fields_values = list(zip(*fields_values.copy()[1:]))
        fields_keys = [i.strip() for i in self.fields]
        body_dict = {fields_keys[i]: list(fields_values[i]) for i in range(len(fields_keys))}
        return body_dict

    def get_head_tail_dict(self) -> dict:
        """Return a dictionary of 'head' and 'tail', with fields being keys and values being values."""
        lines_tailored = self.lines[:self.start_line_index] + self.lines[self.end_line_index:]
        head_tail_dict = dict()
        for line in lines_tailored:
            line_tailored = utility.remove_blankstr_from_a_line(line)
            line_tailored = [re.split(':|：',i) for i in line_tailored.copy()]
            line_tailored = [u for i in line_tailored.copy() for u in i if u != ""]
            for i in range(int(len(line_tailored) / 2)):
                k = line_tailored[2 * i].strip()
                v = line_tailored[2 * i + 1]
                head_tail_dict[k] = v
        return head_tail_dict

    @staticmethod
    def remove_letters(dict_to_clean, str2, field_list: list = None) -> dict:
        """Remove unwanted character (rather than word) from each unit of self.field_std_dict."""
        if field_list is None:
            field_list = dict_to_clean.keys()
        for field in field_list:
            to_remove = dict_to_clean[field]
            removed = [utility.remove_letters(i, str2) for i in to_remove]
            dict_to_clean[field] = removed
        return dict_to_clean
