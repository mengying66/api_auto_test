# 需求文档

## 简介

将现有的 pytest + allure 测试框架从硬编码的登录接口测试改造为通用的 Excel 驱动接口测试引擎。
改造后，测试人员只需维护 Excel 文件即可驱动任意 HTTP 接口的测试，无需修改 Python 代码。
Excel 表头即为接口参数定义，框架自动识别保留列（`case_id`、`title`、`method`、`url`、`headers`、`params`、`body`、`type`、`run_status`、`is_run` 等控制字段）与断言列（`expected_` 前缀），
并支持自定义请求头注入、GET/POST 参数分离传递、登录态自动携带 token、多字段断言、多 Sheet 多接口等能力。

> **列定义说明（对应 Excel 列顺序）：**
> A: `case_id`，B: `title`，C: `method`（如 post/GET），D: `url`（如 `/api/user/list?current=1&pageSize=20`），E: `headers`（JSON 字符串），F: `params`（GET 查询参数或 POST 表单参数，JSON 字符串），G: `body`（POST 请求体，JSON 字符串），H: `type`（如 json），I: `run_status`（TRUE 表示需携带登录 token，FALSE 表示不需要），J: `expected_code`（期望响应码，如 200、500），K: `expected_msg`（期望响应消息，如 成功、密码错误）

---

## 词汇表

- **Engine**：通用 Excel 驱动接口测试引擎，即本次改造的核心模块
- **ExcelReader**：负责读取 Excel 文件并解析用例数据的组件（对应 `utils/read_file.py`）
- **RequestHandler**：负责发送 HTTP 请求的组件（对应 `common/request_handler.py`）
- **AssertHandler**：负责执行多字段断言的组件（对应 `common/assert_handler.py`）
- **TestCase**：从 Excel 单行数据解析出的一条测试用例，包含请求控制字段和期望值
- **Reserved_Column**：Excel 中具有特殊含义的控制列，包括 `case_id`、`title`、`method`、`url`、`headers`、`params`、`body`、`type`、`run_status`、`is_run`，以及所有以 `expected_` 为前缀的列
- **headers**：Excel 控制列，值为 JSON 字符串，定义本条用例的自定义请求头，如 `{"Content-Type": "application/json"}`
- **params**：Excel 控制列，值为 JSON 字符串，定义 GET 请求的 URL 查询参数，如 `{"username": "xx"}`
- **body**：Excel 控制列，值为 JSON 字符串，定义 POST 请求的请求体，如 `{"username": "xx", "password": "xx"}`
- **type**：Excel 控制列，指定请求体编码方式，当前取值为 `json`，保留扩展性（未来可支持 `form` 等）
- **run_status**：Excel 控制列（列 I），值为 `TRUE` 或 `FALSE`，为 `TRUE` 时框架需在请求头中自动携带登录 token；为 `FALSE` 时不携带
- **is_run**：Excel 可选控制列，值为 `TRUE` 或 `FALSE`，为 `FALSE` 时跳过该用例（不填则默认执行）
- **expected_field**：Excel 中以 `expected_` 为前缀的列，用于定义断言字段及期望值，如 `expected_code`、`expected_msg`
- **login_token**：由 `conftest.py` 中 `login_token` fixture 提供的会话级登录令牌，格式为 Bearer Token

---

## 需求

### 需求 1：Excel 列约定与用例解析

**用户故事：** 作为测试工程师，我希望通过 Excel 表头定义接口参数，使得框架能自动识别请求控制字段与期望值，而无需修改代码。

#### 验收标准

1. THE ExcelReader SHALL 将 Excel 第一行作为列名，从第二行起每行解析为一个 TestCase 字典。
2. WHEN Excel 中存在 `is_run` 列且某行该列值不为 `TRUE` 时，THE ExcelReader SHALL 跳过该行，不将其加入用例列表。
3. THE ExcelReader SHALL 将所有以 `expected_` 为前缀的列识别为 expected_field，并从 TestCase 字典中单独提取为断言期望值映射。
4. WHEN Excel 中 `headers` 列的值为非空 JSON 字符串时，THE ExcelReader SHALL 将其解析为字典，作为本条用例的自定义请求头。
5. WHEN Excel 中 `params` 列的值为非空 JSON 字符串时，THE ExcelReader SHALL 将其解析为字典，作为本条用例的 URL 查询参数。
6. WHEN Excel 中 `body` 列的值为非空 JSON 字符串时，THE ExcelReader SHALL 将其解析为字典，作为本条用例的请求体。
7. THE ExcelReader SHALL 读取 `type` 列的值作为请求体编码方式，当前支持 `json`，并保留对未来扩展值的兼容性。
8. THE ExcelReader SHALL 读取 `run_status` 列的值，将 `TRUE`（大小写不敏感）解析为布尔值 `True`，其余值解析为 `False`。
9. IF Excel 文件路径不存在，THEN THE ExcelReader SHALL 抛出包含文件路径信息的 `FileNotFoundError`。
10. IF Excel 中 `headers`、`params` 或 `body` 列的值为非空但无法解析为合法 JSON，THEN THE ExcelReader SHALL 抛出包含行号和列名的 `ValueError`。
11. IF Excel 中必填 Reserved_Column（`method`、`url`）的值为空，THEN THE ExcelReader SHALL 抛出包含行号和列名的 `ValueError`。

---

### 需求 2：通用 HTTP 请求发送

**用户故事：** 作为测试工程师，我希望框架能根据 Excel 中定义的 method、url、headers、params/body、type、run_status 自动发送对应的 HTTP 请求，支持任意接口，而无需为每个接口编写独立的测试代码。

#### 验收标准

1. WHEN TestCase 的 `method` 为 `GET`，THE RequestHandler SHALL 将 `params` 字典以 URL 查询参数方式发送请求。
2. WHEN TestCase 的 `method` 为 `POST` 且 `type` 为 `json`，THE RequestHandler SHALL 将 `body` 字典以 JSON 请求体方式发送请求。
3. WHEN TestCase 的 `headers` 字典非空，THE RequestHandler SHALL 将其合并到本次请求的请求头中发送。
4. WHEN TestCase 的 `run_status` 为 `True`，THE RequestHandler SHALL 在请求头中自动添加 `Authorization: Bearer {login_token}`，其中 `login_token` 来自 `conftest.py` 的 `login_token` fixture。
5. WHEN TestCase 的 `run_status` 为 `True` 且 `headers` 中已包含 `Authorization` 字段，THE RequestHandler SHALL 优先使用 `headers` 中的值，不覆盖。
6. THE RequestHandler SHALL 使用 `config/config.yaml` 中配置的 `base_url` 拼接 TestCase 中的 `url` 字段构成完整请求地址。
7. IF TestCase 的 `method` 值不在 `[GET, POST, PUT, DELETE, PATCH]` 范围内，THEN THE RequestHandler SHALL 抛出包含实际值的 `ValueError`。
8. IF 请求发生网络异常或超时，THEN THE RequestHandler SHALL 记录错误日志并重新抛出异常，使对应测试用例标记为失败。

---

### 需求 3：多字段断言

**用户故事：** 作为测试工程师，我希望在 Excel 中通过 `expected_` 前缀列定义多个断言字段，框架自动对响应 JSON 中对应字段进行比对，并在失败时给出清晰的错误信息。

#### 验收标准

1. WHEN 响应状态码不为 200，THE AssertHandler SHALL 断言失败并输出实际状态码。
2. WHEN TestCase 包含一个或多个 expected_field，THE AssertHandler SHALL 对每个 expected_field 从响应 JSON 中提取同名字段（去掉 `expected_` 前缀）并与期望值进行比对。
3. WHEN 某个 expected_field 的实际值与期望值不一致，THE AssertHandler SHALL 输出包含字段名、期望值、实际值的断言失败信息。
4. IF 响应体无法解析为 JSON，THEN THE AssertHandler SHALL 断言失败并附加原始响应文本。
5. IF expected_field 对应的字段在响应 JSON 中不存在，THEN THE AssertHandler SHALL 断言失败并说明缺失的字段名。
6. THE AssertHandler SHALL 支持期望值的类型自动转换：当 Excel 中期望值为数字字符串时，SHALL 与响应中的数字类型进行等值比较。

---

### 需求 4：通用测试驱动入口

**用户故事：** 作为测试工程师，我希望有一个通用的 pytest 测试类，能够通过参数化自动加载任意 Excel 文件中的用例并执行，替代现有的硬编码测试类。

#### 验收标准

1. THE Engine SHALL 提供一个通用 pytest 测试函数，通过 `@pytest.mark.parametrize` 将 ExcelReader 解析出的所有 TestCase 作为参数注入。
2. WHEN 执行测试时，THE Engine SHALL 使用 `allure.dynamic.title` 将每条用例的 `case_id` 和 `title` 设置为 Allure 报告中的用例标题。
3. THE Engine SHALL 在 Allure 报告中以步骤形式记录：请求参数、完整请求 URL、响应状态码、响应体。
4. THE Engine SHALL 支持通过命令行参数 `--excel` 指定 Excel 文件路径，默认值为 `testcases/autotest_case.xlsx`。
5. THE Engine SHALL 支持通过命令行参数 `--sheet` 指定 Sheet 名称，默认值为 `Sheet1`。
6. WHERE 多个 Sheet 需要测试，THE Engine SHALL 支持在同一 Excel 文件中通过不同 Sheet 组织不同接口的用例，每个 Sheet 独立驱动一组测试。

---

### 需求 5：Excel 文件格式规范（解析器与格式化器）

**用户故事：** 作为测试工程师，我希望有明确的 Excel 列名规范文档和格式校验，确保用例文件格式正确，并能通过工具验证 Excel 文件是否符合规范。

#### 验收标准

1. THE Engine SHALL 定义并文档化 Excel 列名规范：Reserved_Column 包括 `case_id`、`title`、`method`、`url`、`headers`、`params`、`body`、`type`、`run_status`、`is_run`，expected_field 以 `expected_` 为前缀（如 `expected_code`、`expected_msg`）。
2. WHEN 对 Excel 文件执行格式校验，THE ExcelReader SHALL 检查是否包含所有必填 Reserved_Column（`method`、`url`），并在缺失时返回包含缺失列名的错误信息。
3. THE ExcelReader SHALL 忽略 `params`、`body`、`headers` 中值为 `None` 或空字符串的字段，不将其加入请求参数。
4. FOR ALL 符合规范的 Excel 用例文件，ExcelReader 解析后再由格式化工具重新生成等效 Excel，再次解析所得 TestCase 列表 SHALL 与原始解析结果等价（往返属性）。

---

### 需求 6：日志与报告集成

**用户故事：** 作为测试工程师，我希望每次测试执行都有完整的日志记录和 Allure 报告，方便定位失败原因。

#### 验收标准

1. THE Engine SHALL 在每条用例执行时，通过现有 `log_handler` 记录请求方法、完整 URL、请求参数、响应状态码和响应体。
2. WHEN 断言失败时，THE Engine SHALL 在 Allure 报告中附加请求参数（JSON 格式）和响应内容（JSON 格式）作为附件。
3. WHILE 测试套件执行中，THE Engine SHALL 保证单条用例的失败不影响其他用例的执行。
