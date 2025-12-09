# author=@mengmeng
# time：2025/12/3 09：54：48
# describe：

from openpyxl import load_workbook
import os
from pathlib import Path

# 兼容多系统的路径拼接
excel_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "testcases", "autotest_case.xlsx")
def read_excel(file_path:str , sheet_name: str = "Sheet1") -> list[dict]:
    """读取Excel文件，返回用例数据列表（第一行作为表头）"""
    wb = load_workbook(file_path)
    ws = wb[sheet_name]
    headers = [cell.value for cell in ws[1]]  # 第一行是表头
    cases = []
    for row in ws.iter_rows(min_row=2, values_only=True):  # 从第二行开始是数据
        case = dict(zip(headers, row))
        cases.append(case)
    return cases

if __name__ == '__main__':
    print(read_excel(excel_path))