# api_auto_test

基于 pytest + allure 的通用 Excel 驱动接口测试框架。测试人员只需维护 Excel 文件即可驱动任意 HTTP 接口测试，无需修改 Python 代码。

## 项目结构

```
api_auto_test/
├── common/
│   ├── assert_handler.py     # 多字段动态断言
│   ├── log_handler.py        # 日志封装
│   └── request_handler.py    # HTTP 请求封装
├── config/
│   ├── config.yaml           # 多环境 base_url 配置
│   └── env.py                # Config 类
├── testcases/
│   ├── autotest_case.xlsx    # Excel 用例文件（示例）
│   └── test_excel_engine.py  # 通用测试驱动入口
├── tests/
│   ├── unit/                 # 单元测试
│   └── property/             # 属性测试（hypothesis）
├── utils/
│   └── read_file.py          # ExcelReader
├── conftest.py               # fixtures & 命令行参数
├── requirements.txt
└── run.py                    # 一键运行入口
```

## Excel 用例格式

| 列 | 字段名 | 说明 |
|---|---|---|
| A | case_id | 用例编号 |
| B | title | 用例标题 |
| C | method | HTTP 方法（GET/POST/...） |
| D | url | 接口路径（如 `/api/login`） |
| E | headers | 请求头 JSON 字符串 |
| F | params | GET 查询参数 JSON 字符串 |
| G | body | POST 请求体 JSON 字符串 |
| H | type | 编码方式（`json`） |
| I | run_status | `TRUE` 执行，`FALSE` 跳过 |
| J+ | expected_xxx | 断言期望值（支持多列） |

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
# 使用默认 Excel 文件
pytest testcases/test_excel_engine.py -v

# 指定 Excel 文件和 Sheet
pytest testcases/test_excel_engine.py --excel=testcases/autotest_case.xlsx --sheet=Sheet1 -v

# 生成 Allure 报告
pytest testcases/test_excel_engine.py -v --alluredir=reports/allure-results
allure serve reports/allure-results
```

### 运行单元测试

```bash
pytest tests/unit/ -v
```

### 运行属性测试

```bash
pytest tests/property/ -v --hypothesis-seed=0
```

## 多环境切换

修改 `config/config.yaml` 中的环境配置，在 `config/env.py` 的 `Config.__init__` 中指定 `env` 参数（如 `test_web`、`pro_web`）。
