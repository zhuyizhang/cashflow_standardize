from pickle import FALSE
from . import csv_field_handler
from . import utility
import re


class CashFlowHandler(csv_field_handler.CsvFieldHandler):
    """Handle (incluing field parse and standardize) a csv file of cash flow."""

    not_null_field = '余'

    def __init__(self, directory, encoding='utf-8-sig') -> None:
        super().__init__(directory, encoding)

        # 以下data_attributes，在初始化时先创建，
        self.account_no = None
        self.multiple_acc = False

    @utility.timer_func
    def do_field_standardize(self, field_map_directory) -> None:
        self.field_map_directory = field_map_directory
        self.abbreviation, self.full_name, self.field_map = self._load_field_map()
        self.field_std_dict = self._get_field_std_dict()
        self.account_no, self.multiple_acc = self._get_account_no()
        self.field_std_dict = self._keep_one_acc_col()
        self.field_std_dict = self.remove_letters(self.field_std_dict.copy(), "\n\t`")
        self.field_std_dict = self.remove_letters(self.field_std_dict.copy(), ",",['借方发生额', '贷方发生额', '收支额正负值', '收支额绝对值', '余额'])
        self.field_std_lines = self._get_field_std_lines()

    def _get_account_no(self) -> tuple:
        account_no = None
        multiple_acc = False
        if self.field_map['body']['本方账号'] == 'None':
            if self.field_map['head']['本方账号_表头'] == 'None':
                account_no = input("文件的表头和表体，均未获取到'银行账号'信息，请手动输入：")
            else:
                account_no = self.field_std_dict['本方账号_表头'][0]
        else:
            account_no = self.field_std_dict['本方账号'][0]
            account_set = set(self.field_std_dict['本方账号'])
            if len(account_set) > 1:
                multiple_acc = True
        account_no = utility.remove_letters(account_no, '-[]\t')
        account_no = re.findall(r'\d+',account_no)[0]
        if not multiple_acc:
            print(f'已解析<银行账号>, 为: ', account_no)
        else:
            print(f'已解析<银行账号>, 有多个，为: ', account_set)
        return account_no, multiple_acc

    def _keep_one_acc_col(self) -> dict:
        # <本方账单>字段，以self.account_no重新写入（在_get_account_no()已清洗）。但如有多账号，则不，而仅将现有账号列做清洗重写入。
        field_std_dict = self.field_std_dict.copy()
        if not self.multiple_acc:
            field_std_dict['本方账号'] = [self.account_no] * (self.end_line_index - self.start_line_index - 1)
        else:
            field_std_dict['本方账号'] = [utility.remove_letters(i, '-[]\t') for i in self.field_std_dict['本方账号']]
        del field_std_dict['本方账号_表头']
        return field_std_dict
