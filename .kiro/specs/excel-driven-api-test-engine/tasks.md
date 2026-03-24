# 实现计划：Excel 驱动接口测试引擎

## 概述

将现有 pytest + allure 框架改造为通用 Excel 驱动接口测试引擎。
按模块逐步实现：ExcelReader 增强 → AssertHandler 重构 → conftest 扩展 → 通用测试入口 → 单元测试 → 属性测试。

## 任务列表

- [x] 1. 增强 ExcelReader（utils/read_file.py）
  - [x] 1.1 将现有 `read_excel` 函数重构为 `ExcelReader` 类
    - 定义类常量 `RESERVED_COLUMNS`、`JSON_COLUMNS`、`REQUIRED_COLUMNS`
    - 实现 `__init__(self, file_path: str, sheet_name: str = "Sheet1") -> None`
    - 文件不存在时抛出 `FileNotFoundError("Excel 文件不存在: {file_path}")`
    - Sheet 不存在时抛出 `KeyError("Sheet '{sheet_name}' 不存在，可用 Sheet: {sheets}")`
    - _需求: 1.1, 1.9, 5.1_

  - [x] 1.2 实现 `_validate_headers` 方法
    - 检查是否包含所有必填列（`method`、`url`），缺失时抛出 `ValueError("Excel 缺少必填列: {missing_cols}")`
    - _需求: 1.11, 5.2_

  - [x] 1.3 实现 `_parse_json_field` 方法
    - `None` 或空字符串返回 `None`，不抛异常
    - 非空但无法解析为合法 JSON 时抛出 `ValueError("第{row}行 {col} 列 JSON 解析失败: {value}")`
    - _需求: 1.4, 1.5, 1.6, 1.10, 5.3_

  - [x] 1.4 实现 `_parse_run_status` 方法
    - 大小写不敏感，仅 `"TRUE"` 返回 `True`，其余（含 `None`、空字符串、`"FALSE"`）返回 `False`
    - _需求: 1.8_

  - [x] 1.5 实现 `load_cases` 方法
    - 第一行作为列名，从第二行起逐行解析为 TestCase 字典
    - `is_run` 列值不为 `TRUE`（大小写不敏感）时跳过该行
    - `expected_` 前缀列统一收集到 `expected` 子字典（去掉前缀作为 key）
    - `method`、`url` 为空时抛出 `ValueError("第{row}行 {col} 列不能为空")`
    - 调用 `_parse_json_field` 处理 `headers`/`params`/`body`
    - 调用 `_parse_run_status` 处理 `run_status`
    - _需求: 1.1, 1.2, 1.3, 1.7_

- [x] 2. 重构 AssertHandler（common/assert_handler.py）
  - [x] 2.1 实现 `_coerce_value` 静态方法
    - 期望值为数字字符串时，尝试转为 `int` 或 `float` 再与实际值比对
    - _需求: 3.6_

  - [x] 2.2 实现 `assert_response` 静态方法
    - 响应状态码不为 200 时断言失败，输出实际状态码（需求 3.1）
    - 响应体无法解析为 JSON 时调用 `pytest.fail`，附加原始响应文本（需求 3.4）
    - 遍历 `expected` 字典：`code` 字段与 `response.status_code` 比对，其余字段从 `response.json()` 取值
    - 期望字段不存在于响应 JSON 时调用 `pytest.fail`，说明缺失字段名（需求 3.5）
    - 字段值不匹配时调用 `pytest.fail`，输出字段名、期望值、实际值（需求 3.3）
    - _需求: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 3. 扩展 conftest.py
  - [x] 3.1 新增 `pytest_addoption` 注册命令行参数
    - `--excel`：默认值 `testcases/autotest_case.xlsx`
    - `--sheet`：默认值 `Sheet1`
    - 不破坏现有 `login_token` fixture
    - _需求: 4.4, 4.5_

  - [x] 3.2 新增 `excel_cases` session 级 fixture
    - 从 `--excel` / `--sheet` 参数读取路径和 Sheet 名
    - 调用 `ExcelReader(excel_path, sheet_name).load_cases()` 返回用例列表
    - _需求: 4.1, 4.6_

- [x] 4. 新增通用测试驱动入口（testcases/test_excel_engine.py）
  - [x] 4.1 实现 `pytest_generate_tests` 动态参数化
    - 从 `excel_cases` fixture 读取用例列表，注入到 `test_api_case` 函数
    - _需求: 4.1_

  - [x] 4.2 实现 `test_api_case` 测试函数
    - 使用 `allure.dynamic.title` 设置用例标题为 `{case_id} - {title}`（需求 4.2）
    - 按设计文档中的请求构造规则合并 headers、注入 token、分离 params/body/json（需求 2.1~2.6）
    - 调用 `RequestHandler.send_request` 发送请求
    - 以 allure step 记录：请求参数、完整 URL、响应状态码、响应体（需求 4.3, 6.1）
    - 调用 `AssertHandler.assert_response` 执行多字段断言
    - 断言失败时在 Allure 报告中附加请求参数和响应内容（需求 6.2）
    - 单条用例失败不影响其他用例（需求 6.3）
    - _需求: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 4.1, 4.2, 4.3, 6.1, 6.2, 6.3_

- [x] 5. 检查点 —— 确保核心流程可运行
  - 确保所有模块可正常导入，运行 `pytest testcases/test_excel_engine.py --collect-only` 无报错，如有问题请提出。

- [x] 6. 编写单元测试（tests/unit/）
  - [x] 6.1 创建 `tests/__init__.py`、`tests/unit/__init__.py`

  - [x] 6.2 编写 `tests/unit/test_excel_reader.py`
    - 测试正常用例解析（含 `is_run` 过滤、`expected_` 识别、JSON 字段解析）
    - 测试文件不存在抛出 `FileNotFoundError`
    - 测试 Sheet 不存在抛出 `KeyError`
    - 测试非法 JSON 抛出 `ValueError`（含行号和列名）
    - 测试必填列为空抛出 `ValueError`
    - 测试缺少必填列抛出 `ValueError`
    - 测试 `None`/空字符串字段返回 `None`
    - _需求: 1.1~1.11, 5.2, 5.3_

  - [ ]* 6.3 编写 `tests/unit/test_assert_handler.py`
    - 测试状态码不为 200 时断言失败
    - 测试多字段断言通过和失败场景
    - 测试响应体非 JSON 时的错误处理
    - 测试期望字段不存在于响应时的错误处理
    - 测试数字字符串类型自动转换
    - _需求: 3.1~3.6_

  - [ ]* 6.4 编写 `tests/unit/test_request_builder.py`
    - 测试 `run_status=True` 时自动注入 Authorization header
    - 测试 `headers` 中已有 Authorization 时不被覆盖
    - 测试 GET 请求使用 `params`，POST+json 使用 `json` 参数
    - 测试非法 HTTP 方法抛出 `ValueError`
    - 测试网络异常被重新抛出（mock `requests.Session.request`）
    - _需求: 2.1~2.8_

- [x] 7. 编写属性测试（tests/property/）
  - [x] 7.1 创建 `tests/property/__init__.py`

  - [x]* 7.2 编写 `tests/property/test_excel_reader_props.py`
    - **Property 1: JSON 列往返解析** — 验证需求 1.4, 1.5, 1.6
    - **Property 2: is_run 过滤** — 验证需求 1.2
    - **Property 3: expected_ 前缀列自动识别** — 验证需求 1.3
    - **Property 4: run_status 布尔解析** — 验证需求 1.8
    - **Property 5: 文件不存在时抛出 FileNotFoundError** — 验证需求 1.9
    - **Property 6: 非法 JSON 字段抛出 ValueError** — 验证需求 1.10
    - **Property 7: 必填列为空时抛出 ValueError** — 验证需求 1.11
    - **Property 14: 空值字段忽略** — 验证需求 5.3
    - **Property 15: Excel 往返等价性** — 验证需求 5.4
    - **Property 16: 多 Sheet 独立解析** — 验证需求 4.6

  - [x]* 7.3 编写 `tests/property/test_assert_handler_props.py`
    - **Property 11: 多字段断言正确性** — 验证需求 3.2, 3.6
    - **Property 12: 断言失败信息完整性** — 验证需求 3.3
    - **Property 13: 缺失字段断言失败** — 验证需求 3.5

  - [x]* 7.4 编写 `tests/property/test_request_builder_props.py`
    - **Property 8: token 注入与优先级** — 验证需求 2.4, 2.5
    - **Property 9: URL 拼接** — 验证需求 2.6
    - **Property 10: 非法 HTTP 方法抛出 ValueError** — 验证需求 2.7

- [x] 8. 最终检查点 —— 确保所有测试通过
  - 确保所有测试通过，如有问题请提出。

## 备注

- 标有 `*` 的子任务为可选项，可跳过以加快 MVP 交付
- 每个任务均引用了具体需求条款，确保可追溯性
- 属性测试使用 `hypothesis` 库，每个属性最少运行 100 次随机输入
- 运行单元测试：`pytest tests/unit/ -v`
- 运行属性测试：`pytest tests/property/ -v --hypothesis-seed=0`
- 运行集成测试：`pytest testcases/test_excel_engine.py --excel=testcases/autotest_case.xlsx --sheet=Sheet1 -v --alluredir=reports/allure-results`
