import json
from . import csv_field_parse
from . import utility


class CsvFieldHandler(csv_field_parse.CsvFieldParse):
    def __init__(self, directory, encoding='utf-8-sig') -> None:
        super().__init__(directory, encoding)

        # 以下data_attributes，在初始化时先创建，在do_field_standardize()赋值。
        self.field_map_directory = None
        self.abbreviation = None
        self.full_name = None
        self.field_map = None
        self.field_std_dict = None
        self.field_std_lines = None

        # 以下data_attributes，在初始化时先创建，在do_field_unpivot()赋值。
        self.unpivot_conf_directory = None
        self.unpivot_conf = None
        self.unpivot_fields = None
        self.index_fields = None
        self.unpivoted_lines = None

    @utility.timer_func
    def do_field_unpivot(self, unpivot_conf_directory) -> None:
        self.unpivot_conf_directory = unpivot_conf_directory
        self.unpivot_conf, self.index_fields, self.unpivot_fields = self._load_unpivot_conf()
        self.unpivoted_lines = self._get_unpivoted_lines()

    @utility.timer_func
    def do_field_standardize(self, field_map_directory) -> None:
        self.field_map_directory = field_map_directory
        self.abbreviation, self.full_name, self.field_map = self._load_field_map()
        self.field_std_dict = self._get_field_std_dict()
        self.field_std_dict = self.remove_letters(self.field_std_dict.copy(), "\n\t,")
        self.field_std_lines = self._get_field_std_lines()

    def _load_field_map(self) -> tuple:
        """ Load field maps, determine the abbreviation and fullname of the applicable map for the instance.

        :param self.field_map_directory
        :return abbreviation
        :return full_name
        :return field_map
        """
        with open(self.field_map_directory, mode='r', encoding='utf-8') as f:
            field_map = json.load(f)
        # 加载字段映射表-简称集合。确定文件名中包含的哪个简称，以作为本文件的简称。
        abbreviation_set = set(field_map[0].keys())
        abbreviation = self._determine_abbreviation(abbreviation_set)
        # 根据本文件的简称，加载适用的字段映射规则。
        full_name = field_map[0][abbreviation]
        field_map = field_map[1][full_name]
        print(f"已加载<字段映射表>\n已解析<本表对象的全名>为：'{full_name}'，\n已解析<本表对象的字段映射规则>：", field_map)
        return abbreviation, full_name, field_map
        # 加载适用的字段映射规则后, 即可做字段标准化。

    def _determine_abbreviation(self, abbreviation_set) -> str:
        """ Determine the abbreviation of the instance, for further selection of applicable map.

        :param abbreviation_set
        :param self.filename
        :return self.abbreviation
        """
        abbreviation = None
        for i in abbreviation_set:
            if i in self.filename:
                abbreviation = i
                print(f"已解析<本表对象的简称>为：'{abbreviation}'")
                return abbreviation
        if abbreviation is None:
            abbreviation = input(f"未从文件名'{self.filename}'中解析到<本表对象的简称>，请录入：")
        return abbreviation

    def _get_field_std_dict(self) -> dict:
        """Extract wanted columns from head and body, according to the map.
        
        :return field_std_dict
        """
        field_std_dict = dict()
        _body_data_lens = (self.end_line_index - self.start_line_index - 1)
        # 表头
        for k, v in self.field_map["head"].items():
            if v in self.head_tail_dict:
                field_std_dict[k] = [self.head_tail_dict[v]] * _body_data_lens
            elif v == "None":
                field_std_dict[k] = [None] * _body_data_lens
            else:
                raise Exception(f"发生了错误！标准字段名'{k}'对应的原表字段名'{v}'未找到。请更新字段映射表。")
        # 表体
        for k, v in self.field_map["body"].items():
            if type(v) == list:
                arrays = [self.body_dict.get(_v, '') for _v in v if _v in self.body_dict]
                field_std_dict[k] = list(map(''.join, zip(*arrays)))
            elif v in self.body_dict:
                field_std_dict[k] = self.body_dict[v]
            elif v == "None" or v == "":
                field_std_dict[k] = [None] * _body_data_lens
            elif v[0] == "$":
                field_std_dict[k] = [getattr(self, v[1:])] * _body_data_lens
            else:
                raise Exception(f"发生了错误！标准字段名'{k}'对应的原表字段名'{v}'未找到。请更新字段映射表。")
        return field_std_dict

    def _get_field_std_lines(self) -> list:
        """Convert self.field_std_dict (dictionaries) to self.field_std_lines (list of lines).
        
        :return field_std_lines
        """
        # 以标准化字段的lines，写入self.field_std_lines。
        field_std_lines = [list(self.field_std_dict.keys())]
        values = [list(i) for i in list(zip(*list(self.field_std_dict.values())))]
        field_std_lines += [i for i in values]
        print("已生成<字段标准化的文本行列表>，存于self.field_std_lines，待写入csv文件。")
        return field_std_lines

    def _load_unpivot_conf(self) -> tuple:
        with open(self.unpivot_conf_directory, mode='r', encoding='utf-8') as f:
            unpivot_conf = json.load(f)
        # 加载逆透视字段和索引字段。
        index_fields = unpivot_conf["index_fields"]
        unpivot_fields = unpivot_conf["unpivot_fields"]
        return unpivot_conf, index_fields, unpivot_fields

    def _get_unpivoted_lines(self) -> list:
        unpivoted_lines = []
        first_row = self.index_fields + ["Attribute", "Value"]
        unpivoted_lines.append(first_row)
        index_cols = [self.body_dict[index_field] for index_field in self.index_fields]
        for unpivot_field in self.unpivot_fields:
            unpivot_col = self.body_dict[unpivot_field]
            unpivot_name_col = [unpivot_field] * len(index_cols[0])
            comb_cols = index_cols + [unpivot_name_col, unpivot_col]
            zipped = list(zip(*comb_cols))
            zipped = [[u for u in i] for i in zipped.copy()]
            unpivoted_lines += zipped
        return unpivoted_lines
