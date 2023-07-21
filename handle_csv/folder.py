from . import utility


class Folder:
    def __init__(self, directory: str):
        self.directory = directory
        self.extensions = ['.csv', '.xlsx', '.xls']
        self.filesdir = []
        self.csvsdir = []
        self.get_filesdir()
        self.convert_excel_to_csv()

    def get_filesdir(self, *extensions):
        # 如果初始化时被动使用该方法，或主动使用该方法但未指定扩展名的，默认希望的扩展名为csv和excel。
        # 如果主动使用该方法，且指定扩展名的（比如png/jpg/py...），则覆盖掉默认的扩展名。
        # 如指定扩展名没加'.'，则补加。
        if len(extensions) != 0:
            self.extensions = [self.add_dot_for_extension(i) for i in extensions]
        self.filesdir = utility.get_filesdir_under_a_folder(self.directory, *self.extensions)
        print(f"已获取文件夹下<扩展名>为'{self.extensions}'的文件路径，共计{len(self.filesdir)}个，存储与'self.filesdir'。")

    def convert_excel_to_csv(self):
        self.csvsdir = []
        for i in self.filesdir:
            csvdir = utility.convert_excel_to_csv(directory=i)
            self.csvsdir.append(csvdir)
        print(f"已将文件夹下excel格式的文件，转换为csv文件。转换后全部的csv文件路径，共计{len(self.csvsdir)}个，存储与'self.csvsdir'。")

    @ staticmethod
    def add_dot_for_extension(extension: str) -> str:
        if extension[0] != '.':
            extension = '.' + extension
        return extension
