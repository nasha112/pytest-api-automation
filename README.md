# Pytest API Automation Framework

基于 **Python + Pytest + Requests** 构建的 REST API 自动化测试框架。

项目以 **GoRest 用户管理 API** 和 **本地 Exam 考试管理系统 API** 为测试对象，覆盖接口正向、负向、边界场景，并结合 Pytest Fixture、参数化、Excel 数据驱动、JSON Schema、Allure 等实现接口自动化测试。

---

## 1. 项目简介

本项目主要用于实践和展示 API 自动化测试的完整流程：

- 接口请求封装
- 测试环境切换
- Token / Cookie 管理
- Pytest Fixture 管理测试依赖
- 参数化测试
- Excel 数据驱动
- JSON Schema 响应校验
- 正向 / 负向 / 边界测试
- Allure 测试报告
- GitHub Actions 持续集成

项目目前包含两个测试对象：

| 测试对象 | 环境 | 主要测试内容 |
|---|---|---|
| GoRest | Public | 用户创建、查询、删除、异常参数、鉴权等 |
| Exam 考试管理系统 | Local | 登录、考试、试卷、规则、题库、试题等核心接口 |

---

## 2. 技术栈

| 技术 | 用途 |
|---|---|
| Python 3.13 | 测试开发语言 |
| Pytest | 测试框架 |
| Requests | HTTP 接口请求 |
| Pytest Fixture | 测试环境、Token、Client 管理 |
| pytest.parametrize | 参数化测试 |
| openpyxl | Excel 测试数据读取 |
| JSON Schema | API 响应结构校验 |
| Allure | 测试报告 |
| pytest-env | Pytest 环境变量配置 |
| Git / GitHub | 版本管理 |
| GitHub Actions | CI 持续集成 |

---

## 3. 项目结构

```text
pytest-api-automation-framework/
│
├── .github/
│   └── workflows/
│       └── pytest.yml
│
├── libraries/
│   ├── request_client.py
│
├── schemas/
│   ├── error_schema.json
│   ├── success_user_schema.json
│   └── user_schema.json
│
├── tests/
│   ├── test_users.py
│   ├── test_users_negative.py
│   ├── user_data.json
│   ├── user_data.xlsx
│   │
│   └── local/
│       ├── test_exam_login.py
│       ├── test_exam_core_api_smoke.py
│       ├── test_exam_negative.py
│       └── test_exam_boundary.py
│
├── conftest.py
├── pytest.ini
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 4. 核心设计

### 4.1 RequestClient 封装

通过 `requests.Session()` 对 HTTP 请求进行统一封装：

```python
client.get()
client.post()
client.put()
client.delete()
```

统一处理：

- Base URL
- Request Headers
- Cookie
- HTTP Method
- URL 拼接
- 基础请求日志

测试用例不需要重复编写 Requests 底层请求代码。

例如：

```python
response = exam_client.post(
    "/exam/api/exam/exam/paging",
    json={
        "current": 1,
        "size": 10,
        "params": {}
    }
)
```

---

### 4.2 Pytest Fixture

通过 `conftest.py` 统一管理测试环境和认证信息。

支持：

```bash
pytest --env=public
```

和：

```bash
pytest --env=local
```

其中：

- `public`：GoRest 公网接口
- `local`：本地 Exam 考试管理系统

Fixture 主要负责：

```text
--env
   ↓
base_url
   ↓
Token
   ↓
RequestClient
   ↓
测试用例
```

本地 Exam 环境使用登录接口获取 Token，并在整个测试 session 中复用。

---

## 5. 测试覆盖

### 5.1 GoRest 用户管理

#### 正向测试

实现用户完整生命周期测试：

```text
Create User
     ↓
Get User
     ↓
Delete User
```

同时使用 Excel 进行测试数据参数化。

示例：

```python
@pytest.mark.parametrize(
    "name,email,gender,status",
    user_data
)
def test_can_create_user(...):
    ...
```

---

### 5.2 GoRest 负向测试

目前覆盖：

- 无效 Token
- 缺少必填字段
- 重复邮箱

并结合 JSON Schema 对异常响应进行结构校验。

---

### 5.3 Exam 登录测试

验证本地考试管理系统管理员登录：

```text
POST /exam/api/sys/user/login
```

主要验证：

- HTTP 状态码
- 登录响应
- Token 等关键字段

---

### 5.4 Exam 核心接口冒烟测试

核心接口冒烟测试覆盖：

- 考试列表
- 试卷列表
- 规则列表
- 题库列表
- 试题列表

主要进行三层校验：

```text
第一层：HTTP 状态码
        ↓
第二层：业务状态码
        ↓
第三层：响应结构 / 核心业务字段
```

例如分页接口会验证：

```text
data
current
pages
records
```

试题数据进一步验证：

```text
id
content
quType
```

以及题型范围。

---

### 5.5 Exam 负向测试

覆盖典型异常场景，例如：

- 错误用户名
- 错误密码
- 缺少用户名
- 缺少密码
- 非法参数类型
- Token / 鉴权行为验证

负向测试根据接口实际返回结果进行明确断言。

---

### 5.6 Exam 边界测试

针对分页参数进行边界测试，包括：

```text
current = 0
current = 1
current = 99999

size = 0
size = 1
size = 9999
```

重点验证：

- 接口是否正常处理边界输入
- HTTP / 业务状态是否符合预期
- 分页数据结构是否正确
- 返回记录数量是否符合分页参数

---

## 6. JSON Schema 校验

对于 GoRest 用户接口，使用 JSON Schema 对响应结构进行验证。

例如：

```python
validate(
    instance=response_json,
    schema=success_schema
)
```

相比只验证 HTTP 状态码，可以进一步验证：

- 必填字段
- 字段类型
- JSON 数据结构
- 接口响应格式

---

## 7. Excel 数据驱动

用户创建测试数据维护在：

```text
tests/user_data.xlsx
```

通过 `openpyxl` 读取测试数据，再结合 Pytest 参数化执行。

数据驱动流程：

```text
Excel
  ↓
openpyxl
  ↓
read_excel_data()
  ↓
pytest.parametrize
  ↓
测试用例
```

这样可以将测试数据与测试代码分离。

---

## 8. Allure 测试报告

项目使用 `allure-pytest` 生成测试结果。

执行：

```bash
pytest
```

测试结果默认保存到：

```text
reports/allure-results/
```

使用 Allure 查看：

```bash
allure serve reports/allure-results
```

测试用例中使用：

- Feature
- Story
- Severity
- Tag
- Step
- Attachment

对测试结果进行分类和展示。

---

## 9. 环境配置

项目使用 `pytest.ini` + `pytest-env` 管理测试环境配置。

示例：

```ini
[pytest]
addopts = --alluredir=reports/allure-results

env =
    BASE_URL=https://gorest.co.in
    BASE_URL_LOCAL=http://localhost:8101
```

> `AUTH_TOKEN` 等敏感信息不应提交到公开 Git 仓库，建议通过系统环境变量或 GitHub Secrets 提供。

---

## 10. 安装依赖

建议使用 Python 虚拟环境。

创建虚拟环境：

```bash
python -m venv .venv
```

Windows：

```bash
.venv\Scripts\activate
```

安装项目依赖：

```bash
pip install -r requirements.txt
```

---

## 11. 运行测试

### 11.1 运行 GoRest 测试

```bash
pytest -v tests/test_users.py
```

运行负向测试：

```bash
pytest -v tests/test_users_negative.py
```

---

### 11.2 运行 Exam 测试

确保本地 Exam 系统已经启动，并监听：

```text
http://localhost:8101
```

运行全部 Exam 测试：

```bash
pytest -v --env=local tests/local/
```

只运行核心冒烟测试：

```bash
pytest -v --env=local tests/local/test_exam_core_api_smoke.py
```

运行负向测试：

```bash
pytest -v --env=local tests/local/test_exam_negative.py
```

运行边界测试：

```bash
pytest -v --env=local tests/local/test_exam_boundary.py
```

---

## 12. CI / GitHub Actions

项目配置了 GitHub Actions 工作流：

```text
.github/workflows/pytest.yml
```

用于自动执行测试并保存 Allure 测试结果。

CI 流程：

```text
Push / Pull Request
        ↓
Checkout
        ↓
Setup Python
        ↓
Install dependencies
        ↓
Run Pytest
        ↓
Generate Allure Results
        ↓
Upload Artifact
```

> 本地 Exam 测试依赖本地运行的考试管理系统，因此 CI 环境默认不应直接访问 `localhost:8101`。公网 GoRest 测试更适合作为 GitHub Actions 中的自动化测试对象。

---

## 13. 测试执行示例

本地执行：

```bash
pytest -v --env=local tests/local/
```

示例结果：

```text
======================== test session starts ========================

collected tests ...

PASSED tests/local/test_exam_login.py
PASSED tests/local/test_exam_core_api_smoke.py
PASSED tests/local/test_exam_negative.py
PASSED tests/local/test_exam_boundary.py

========================= tests passed ==============================
```

---

## 14. 项目亮点

### ① 请求层封装

使用 `requests.Session()` 封装统一的 HTTP Client，减少测试用例中的重复请求代码。

### ② Fixture 管理测试依赖

通过 Pytest Fixture 管理：

- 测试环境
- Base URL
- Token
- Headers
- Cookie
- API Client

### ③ 多环境测试

通过：

```bash
--env=public
```

和：

```bash
--env=local
```

切换不同测试环境。

### ④ 数据驱动测试

使用：

```text
openpyxl + pytest.parametrize
```

实现 Excel 数据驱动。

### ⑤ Schema 校验

使用 JSON Schema 验证 API Response 数据结构。

### ⑥ 多类型测试场景

覆盖：

```text
正向测试
负向测试
边界测试
冒烟测试
```

### ⑦ Allure 报告

通过 Allure 对测试用例、步骤和接口响应进行可视化展示。

### ⑧ CI

使用 GitHub Actions 自动执行可在 CI 环境运行的 API 测试。

---

## 15. 当前项目定位

这是一个以 **API 自动化测试** 为核心的练习项目，重点展示：

```text
Python
  ↓
Requests
  ↓
Pytest
  ↓
Fixture
  ↓
参数化 / 数据驱动
  ↓
Schema 校验
  ↓
Allure
  ↓
CI
```

重点关注接口自动化测试的工程化实践，而不是单纯编写大量测试用例。

---

## 16. 后续可扩展方向

后续可以根据实际项目需求继续扩展：

- 数据库校验
- Mock 测试
- pytest-xdist 并行测试
- 定时执行
- 测试结果通知
- 更完整的 CI/CD 流程

以上功能目前作为后续扩展方向，不代表当前版本已经实现。