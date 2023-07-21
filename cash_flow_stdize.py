import pandas as pd
import handle_csv
from handle_csv import utility
from os.path import join, dirname


def comb_and_field_standardize(raw_cf_folder_dir, field_map_dir):
    # 抓取 每个流水表的 文件路径。
    filesdir = utility.get_filesdir_under_a_folder(raw_cf_folder_dir, '.csv', '.xlsx', '.xls')

    for raw_cf_dir in filesdir:
        # 如流水原文件，是excel格式，则处理转换为csv格式，并返回转换得文件的路径。如非excel格式，返回原路径。
        convert_cf_directory = utility.convert_excel_to_csv(raw_cf_dir)

        # 加载单个流水CSV文件。
        raw_cf_csv = handle_csv.CashFlowHandler(convert_cf_directory)

        # 加载原始流水表段标准化的映射表。
        raw_cf_csv.do_field_standardize(field_map_dir)

        # 将结果写入csv文件。
        raw_cf_csv.write_csvfile(directory=raw_cf_dir, lines=raw_cf_csv.field_std_lines, combine=True, crefloder=True)

    return raw_cf_csv.writen_directory


def data_standardize(directory):
    def datetime_data_standardize(dataframe):
        """1.汇总<交易日期时间>、<交易日期>、<交易时间>字段的不完整时间信息，重填补全<交易日期时间>。后删除<交易日期>、<交易时间>字段。
        2.<交易日期时间>字段，字符串日期化。"""
        df = dataframe.copy()
        total_rows = len(df.index)
        datetime = list(df["交易日期时间"])
        date = list(df["交易日期"].astype(str))
        time = list(df["交易时间"].astype(str))
        datetime_clean = []
        bad_lines = []

        for i in range(total_rows):
            if not pd.isnull(datetime[i]):
                _datetime = datetime[i]
            else:
                _date = date[i] if not date[i] == 'nan' else ''
                _time = time[i] if not time[i] == 'nan' else ''
                _time = (6 - len(_time)) * '0' + _time
                _datetime = _date + ' ' + _time
            # 日期格式明显不对的(不以2开头），是badlines。目前仅适用于去掉交行的表尾行。
            if not utility.is_date(_datetime):
                bad_lines.append(i)
            else:
                datetime_clean.append(_datetime)
        df = df[~df.index.isin(bad_lines)]
        df.loc[:, "交易日期时间"] = datetime_clean
        df.loc[:, "交易日期时间"] = pd.to_datetime(df["交易日期时间"])
        df.drop(["交易日期", "交易时间"], axis=1, inplace=True)

        return df

    def amount_to_numeric(dataframe):
        df = dataframe.copy()
        # 1.<借方发生额>、<贷方发生额>、<收支额正负值>、<收支额绝对值>、<余额>字段，字符串数字化。
        df.loc[:, "借方发生额"] = pd.to_numeric(df["借方发生额"])
        df.loc[:, "贷方发生额"] = pd.to_numeric(df["贷方发生额"])
        df.loc[:, "收支额正负值"] = pd.to_numeric(df["收支额正负值"])
        df.loc[:, "收支额绝对值"] = pd.to_numeric(df["收支额绝对值"])
        df.loc[:, "余额"] = pd.to_numeric(df["余额"])

        return df

    def amount_data_standardize(dataframe):
        """1.<借方发生额>、<贷方发生额>、<收支额正负值>、<收支额绝对值>、<余额>字段，字符串数字化。
        2.汇总<收支方向>、<借方发生额>、<贷方发生额>、<收支额正负值>、<收支额绝对值>字段的不完整时间信息，重填补全各字段。"""
        df = dataframe.copy()
        total_rows = len(df.index)
        # # 1.<借方发生额>、<贷方发生额>、<收支额正负值>、<收支额绝对值>、<余额>字段，字符串数字化。
        df.loc[:, "借方发生额"] = pd.to_numeric(df["借方发生额"], errors='coerce')
        df.loc[:, "贷方发生额"] = pd.to_numeric(df["贷方发生额"], errors='coerce')
        df.loc[:, "收支额正负值"] = pd.to_numeric(df["收支额正负值"], errors='coerce')
        df.loc[:, "收支额绝对值"] = pd.to_numeric(df["收支额绝对值"], errors='coerce')
        df.loc[:, "余额"] = pd.to_numeric(df["余额"], errors='coerce')

        # 2.汇总<收支方向>、<借方发生额>、<贷方发生额>、<收支额正负值>、<收支额绝对值>字段的不完整时间信息，重填补全各字段。
        sign = list(df["收支方向"])
        debit = list(df["借方发生额"])
        credit = list(df["贷方发生额"])
        net_amount = list(df["收支额正负值"])
        abs_amount = list(df["收支额绝对值"])
        sign_clean = []
        debit_clean = []
        credit_clean = []
        net_amount_clean = []

        for i in range(total_rows):
            if not pd.isnull(sign[i]):
                if sign[i] in ['来账','收入']:
                    _sign = '贷'
                elif sign[i] in ['往账','支出']:
                    _sign = '借'
                else:
                    _sign = sign[i]
            else:
                if (not pd.isnull(debit[i])) and (debit[i] != 0):
                    _sign = '借'
                elif (not pd.isnull(credit[i])) and (credit[i] != 0):
                    _sign = '贷'
                elif net_amount[i] < 0:
                    _sign = '借'
                else:
                    _sign = '贷'
            sign_clean.append(_sign)
        for i in range(total_rows):
            if not pd.isnull(net_amount[i]):
                _net_amount = net_amount[i]
            else:
                if (not pd.isnull(debit[i])) and (debit[i] != 0):
                    _net_amount = - debit[i]
                elif (not pd.isnull(credit[i])) and (credit[i] != 0):
                    _net_amount = credit[i]
                elif not pd.isnull(abs_amount[i]):
                    _net_amount = (-1 if sign_clean[i] == '借' else 1) * abs_amount[i]
                # 支付宝流水出现过借、贷方都为0的，为开户第1笔流水。
                elif (debit[i] == 0) and credit[i] == 0:
                    _net_amount = 0
                else:
                    print (df.iloc[[i-1]])
                    raise ValueError(f"第{i}行，net_amount无法按逻辑计算得到，请检查！")
            net_amount_clean.append(_net_amount)
        for i in range(total_rows):
            if (not pd.isnull(debit[i])) or (not pd.isnull(credit[i])):
                _debit = debit[i] if (not pd.isnull(debit[i])) else 0
                _credit = credit[i] if (not pd.isnull(credit[i])) else 0
            else:
                _debit = - net_amount_clean[i] if sign_clean[i] == '借' else 0
                _credit = net_amount_clean[i] if sign_clean[i] == '贷' else 0
            debit_clean.append(_debit)
            credit_clean.append(_credit)
        abs_amount_clean = [abs(i) for i in net_amount_clean]
        df.loc[:, "收支方向"] = sign_clean
        df.loc[:, "借方发生额"] = debit_clean
        df.loc[:, "贷方发生额"] = credit_clean
        df.loc[:, "收支额正负值"] = net_amount_clean
        df.loc[:, "收支额绝对值"] = abs_amount_clean

        return df

    def counterpart_data_standardize(dataframe):
        """1.汇总<付款人名称>、<付款人账号>、<收款人账号>、<收款人名称>，补全<对方账号>、<对方账户名称>字段。
        后删除<付款人名称>、<付款人账号>、<收款人账号>、<收款人名称>字段。"""
        df = dataframe.copy()
        total_rows = len(df.index)
        payer = list(df["付款人名称"])
        payer_acc = list(df["付款人账号"])
        payee = list(df["收款人名称"])
        payee_acc = list(df["收款人账号"])
        counterpart = list(df["对方账户名称"])
        counterpart_acc = list(df["对方账号"])
        sign = list(df["收支方向"])
        counterpart_clean = []
        counterpart_acc_clean = []

        for i in range(total_rows):
            if not pd.isnull(payer[i]) and sign[i] == '贷':
                _counterpart = payer[i]
                _counterpart_acc = payer_acc[i]
            elif not pd.isnull(payee[i]) and sign[i] == '借':
                _counterpart = payee[i]
                _counterpart_acc = payee_acc[i]
            else:
                _counterpart = counterpart[i]
                _counterpart_acc = counterpart_acc[i]
            counterpart_clean.append(_counterpart)
            counterpart_acc_clean.append(_counterpart_acc)

        df.loc[:, "对方账户名称"] = counterpart_clean
        df.loc[:, "对方账号"] = counterpart_acc_clean
        df.drop(["付款人名称", "付款人账号", "收款人账号", "收款人名称"], axis=1, inplace=True)

        return df

    def create_sn(dataframe):
        """1.将<交易时间日期>字段转换为yyyymmdd格式的字符串，字段<yyyymmdd>。
        基于<本方账号>、<yyyymmdd>分组，求每行的组内累计序号，字段<cumcount>。
        以<本方账号>_<yyyymmdd>_<cumcount>的格式，生成字段<sn>。并挪至首列。
        后删除<yyyymmdd>、<cumcount>字段。"""
        df = dataframe.copy()
        df['本方账号'] = df['本方账号'].astype(str)
        df['yyyymmdd'] = df["交易日期时间"].dt.strftime('%Y%m%d')
        df['cumcount'] = df.groupby(['本方账号', 'yyyymmdd']).cumcount() + 1
        df['cumcount'] = df['cumcount'].astype(str)

        df['sn'] = df[['本方账号', 'yyyymmdd', 'cumcount']].agg("_".join, axis=1)
        temp_cols = df.columns.tolist()
        new_cols = temp_cols[-1:] + temp_cols[:-1]
        df = df[new_cols]

        df.drop(["yyyymmdd", "cumcount"], axis=1, inplace=True)

        return df

    def sort_within_each_acc(dataframe):
        """各账号的流水，有正向顺序的（月初->月末），也有逆向顺序的（月末—>月初）。
        1.本函数判定各账号是否正序。判定条件：第2行发生额+第1行余额-第2行余额，是否为0。
        2.本函数依据判定结果，重新排序各账号流水的顺序。"""
        df = dataframe.copy()
        df_sorted = pd.DataFrame()
        acc_set = df['本方账号'].unique()
        for acc in acc_set:
            ascending = True
            df_acc = df.loc[df['本方账号'] == acc].copy()
            if df_acc.shape[0] > 1:
                bal_1st_line = df_acc.iloc[0].loc['余额']
                bal_2nd_line = df_acc.iloc[1].loc['余额']
                net_amount_2nd_line = df_acc.iloc[1].loc['收支额正负值']
                diff_abs = abs(bal_1st_line + net_amount_2nd_line - bal_2nd_line)
                if diff_abs < 0.001:
                    pass
                else:
                    ascending = False
            else:
                pass

            df_acc.sort_index(ascending=ascending, inplace=True)
            df_acc.reset_index(drop=True, inplace=True)
            df_sorted = pd.concat([df_sorted.copy(), df_acc], axis=0)

        return df_sorted

    def fix_debit_negative(dataframe):
        df = dataframe.copy()
        acc_set = df['本方账号'].unique()
        for acc in acc_set:
            debit = df.loc[df['本方账号'] == acc, "借方发生额"]
            debit = pd.to_numeric(debit, errors='coerce')
            try: 
                if max(debit) <= 0:
                    df.loc[df['本方账号'] == acc, "借方发生额"] = -debit
                else:
                    pass
            except TypeError:
                print("acc:", acc)
                print("debit", debit)
                def typeof(x):
                    return type(x)
                debit_type = debit.apply(typeof)
                print("debit", debit_type)
                raise
        return df

    def sub_main(_directory):
        # 前步骤已得到字段统一的流水文件。用pandas读取该文件。
        df = pd.read_csv(_directory, dtype={"本方账号": str, "对方账号": str, "付款人账号": str, "收款人账号": str, "流水号": str, })
        # 执行数值标准化，分如下步骤。步骤顺序不可改动，后步骤默认使用前步骤的清理结果。
        # 数值标准化_第一步：日期时间。
        df = datetime_data_standardize(df)
        #df = amount_to_numeric(df)
        # 数值标准化_第二步：借方发生额恒为负的账号，改为正。
        df = fix_debit_negative(df)
        # 数值标准化_第三步：收支方向、收支金额。
        df = amount_data_standardize(df)
        # 数值标准化_第四步：对方名称、对方账号。
        df = counterpart_data_standardize(df)
        # 数值标准化_第五步：对倒序的账号的流水按正序重排。
        df = sort_within_each_acc(df)
        # 创建流水sn，格式<本方账号_yyyymmdd_组内累计序号>。
        df = create_sn(df)
        # 清理任务结束。将清理后的结果，写入csv文件。
        output_dir = join(dirname(_directory),'output_cleaned.csv')
        df.to_csv(output_dir, mode='w', index=False, encoding='utf-8-sig')
        print("字段数值计算和数值格式统一后的合并银行流水：", output_dir)

    sub_main(directory)


def main():
    while True:
        raw_cf_folder_dir = input("请录入流水所在文件夹的路径：")
        if raw_cf_folder_dir != "":
            break
    while True:
        field_map_dir = input("请录入流水字段映射表的路径：")
        if field_map_dir != "":
            break
    field_std_cf_dir = comb_and_field_standardize(raw_cf_folder_dir, field_map_dir)
    data_standardize(field_std_cf_dir)


if __name__ == "__main__":
    main()
