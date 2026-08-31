# 🚀 API Test Automation Framework (Pytest + Allure + 多环境支持)

基于 **Python + Pytest + Requests** 构建的 REST API 自动化测试框架，集成 **Allure 报告**，支持**多环境切换（公网/本地）**，覆盖**用户管理、考试系统登录、考试查询、试卷管理、规则管理、题库管理、试题管理**等多个业务模块。

---

## 📑 目录
- [项目亮点](#-项目亮点)
- [技术栈](#-技术栈)
- [快速开始](#-快速开始)
- [项目结构](#-项目结构)
- [环境切换](#-环境切换)
- [测试覆盖模块](#-测试覆盖模块)
- [运行测试](#-运行测试)
- [Allure 报告](#-allure-报告)
- [Jenkins 集成](#-jenkins-集成)
- [截图预览](#-截图预览)

---

## ✅ 项目亮点

- **多环境支持**：通过 `--env` 参数一键切换 **公网（GoRest）** 和 **本地（Exam 系统）** 环境。
- **数据驱动测试**：用户管理数据来自 Excel，新增数据无需修改代码。
- **接口 Schema 校验**：使用 `jsonschema` 验证响应结构，确保接口契约不变。
- **Allure 报告**：详细的测试步骤、请求/响应附件、分类统计。
- **业务链路串联**：`test_exam_flow.py` 模拟真实用户操作链路（登录 → 查询各模块）。
- **模块化设计**：每个测试文件只负责一个功能，易于维护和扩展。
- **Jenkins 集成**：支持 CI/CD 流水线，自动运行测试并发布报告。

---

## 🛠 技术栈

| 组件 | 技术 |
| :--- | :--- |
| 语言 | Python 3.13 |
| 测试框架 | Pytest 8.x |
| HTTP 客户端 | Requests |
| 数据驱动 | openpyxl (Excel) |
| Schema 校验 | jsonschema |
| 报告 | Allure + JUnit XML |
| CI/CD | Jenkins Pipeline |
| 环境管理 | pytest-env |

---

## ⚡ 快速开始

### 1️⃣ 克隆项目
```bash
git clone https://github.com/你的用户名/pytest-api-automation-framework.git
cd pytest-api-automation-framework
```

### 2️⃣ 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
```

### 3️⃣ 安装依赖
```bash
pip install -r requirements.txt
```

### 4️⃣ 配置环境变量（`pytest.ini`）
```ini
[pytest]
env =
    BASE_URL=https://gorest.co.in
    AUTH_TOKEN=Bearer your_token_here
    BASE_URL_LOCAL=http://localhost:8101
```

### 5️⃣ 运行测试
```bash
# 运行公网用户管理测试
pytest -v --env=public tests/test_users.py

# 运行本地考试系统所有测试
pytest -v --env=local tests/local/

# 运行本地业务链路串联用例
pytest -v --env=local tests/local/test_exam_flow.py

# 排除 flow 用例，运行其他独立模块
pytest -v --env=local tests/local/ -k "not flow"
```

### 6️⃣ 生成 Allure 报告
```bash
# 运行测试并生成 Allure 结果
pytest -v --env=local tests/local/ --alluredir=reports/allure-results

# 查看报告
allure serve reports/allure-results
```

---

## 📂 项目结构

```
project-root/
├── conftest.py                 # Pytest 全局配置、Fixture、多环境支持
├── pytest.ini                  # Pytest 配置（环境变量、标记、插件）
├── requirements.txt            # Python 依赖
├── README.md                   # 项目文档
│
├── tests/
│   ├── test_users.py           # 公网用户管理 CRUD 测试（Excel 数据驱动）
│   ├── test_users_negative.py  # 公网负面用例（无效 Token、重复邮箱等）
│   │
│   └── local/                  # 本地 Exam 系统测试（业务模块）
│       ├── test_exam_login.py          # 登录认证
│       ├── test_exam_flow.py           # 业务链路串联（登录 → 各模块查询）
│       ├── test_exam_paper_list.py     # 试卷列表（可参加的考试）
│       ├── test_exam_record.py         # 考试记录（已参加的试卷）
│       ├── test_exam_paper_rule.py     # 试卷规则管理
│       ├── test_exam_qa_repo.py        # 题库管理
│       └── test_exam_question.py       # 试题管理
│
├── libraries/
│   └── util.py                  # 工具函数（读取 Excel、加载 Schema）
│
├── schemas/
│   └── success_user_schema.json # 用户接口响应 Schema 定义
│
├── reports/
│   └── allure-results/          # Allure 原始数据（自动生成）
│
├── docs/                        # 文档截图（自行添加）
│   ├── allure_overview.png
│   ├── allure_suites.png
│   ├── allure_trends.png
│   └── Stage_view.png
│
└── user_data.xlsx               # 公网用户管理测试数据
```

---

## 🌍 环境切换

框架支持通过 `--env` 参数切换测试环境，无需修改代码。

| 环境 | 命令 | 对应后端 |
| :--- | :--- | :--- |
| 公网 | `--env=public` | `https://gorest.co.in`（用户管理 API） |
| 本地 | `--env=local` | `http://localhost:8101`（Exam 考试系统） |

**示例：**
```bash
# 公网环境
pytest --env=public tests/test_users.py

# 本地环境
pytest --env=local tests/local/
```

---

## 🧪 测试覆盖模块

### 公网环境（GoRest）
| 测试文件 | 功能描述 |
| :--- | :--- |
| `test_users.py` | 用户 CRUD 操作（创建 → 查询 → 删除），数据驱动 |
| `test_users_negative.py` | 负面测试（无效 Token、缺失字段、重复邮箱） |

### 本地环境（Exam 考试系统）
| 测试文件 | 功能描述 | 接口路径 |
| :--- | :--- | :--- |
| `test_exam_login.py` | 管理员登录认证 | `/exam/api/sys/user/login` |
| `test_exam_paper_list.py` | 查询可参加的考试列表 | `/exam/api/exam/exam/paging` |
| `test_exam_record.py` | 查询已参加的考试记录 | `/exam/api/paper/paper/paging` |
| `test_exam_paper_rule.py` | 查询试卷规则列表 | `/exam/api/paper/rule/paging` |
| `test_exam_qa_repo.py` | 查询题库列表 | `/exam/api/qu/repo/paging` |
| `test_exam_question.py` | 查询试题列表 | `/exam/api/qu/qu/paging` |
| `test_exam_flow.py` | **业务链路串联**：登录 → 依次查询所有模块 | 聚合上述接口 |

---

## 🏃 运行测试

### 运行全部测试
```bash
# 公网 + 本地全部运行（需分别指定环境）
pytest --env=public tests/test_users.py tests/test_users_negative.py
pytest --env=local tests/local/
```

### 运行指定模块
```bash
# 只跑登录
pytest --env=local tests/local/test_exam_login.py

# 只跑试卷列表
pytest --env=local tests/local/test_exam_paper_list.py

# 只跑业务链路
pytest --env=local tests/local/test_exam_flow.py
```

### 排除特定用例
```bash
# 排除 flow 串联用例
pytest --env=local tests/local/ -k "not flow"
```

---

## 📊 Allure 报告

### 生成报告
```bash
# 运行测试并保存结果
pytest --env=local tests/local/ --alluredir=reports/allure-results

# 启动 Allure 服务（浏览器自动打开）
allure serve reports/allure-results
```

### 报告内容
- **概览**：测试总数、通过率、执行时间
- **分类**：按 Feature / Story / Tag 分组
- **步骤**：每个用例的详细执行步骤
- **附件**：请求/响应 JSON 自动附加，便于排错
- **趋势图**：历史执行趋势（需多次运行）

### 生成静态 HTML
```bash
allure generate reports/allure-results -o allure-report --clean
# 打开 allure-report/index.html 即可查看
```

---

## 🔧 Jenkins 集成

### Pipeline 配置
项目根目录包含 `Jenkinsfile`，支持声明式 Pipeline。

**关键 Stage：**
1. Checkout 代码
2. 创建虚拟环境并安装依赖
3. 执行测试（含 Allure 结果收集）
4. 归档 JUnit XML 结果
5. 生成并发布 Allure 报告

### 运行方式
```bash
pytest --env=public tests/test_users.py --alluredir=reports/allure-results --junitxml=reports/junit-results.xml
```

---

## 📷 截图预览

> 以下图片位置留空，请自行添加截图。

### Allure 报告 - 概览


### Allure 报告 - 测试套件


### Allure 报告 - 趋势图


### Jenkins Pipeline 执行


### 本地测试执行结果


---

## 📝 后续扩展方向

- **数据库校验**：已封装 `DBClient`，可在本地环境开启，验证数据落库。
- **Mock 外部依赖**：使用 `requests-mock` 或 WireMock 模拟第三方服务（如支付、短信）。
- **并发执行**：使用 `pytest-xdist` 加速测试执行。
- **邮件通知**：Jenkins 构建后发送测试报告邮件。
- **定时触发**：配置 Jenkins 定时任务，每日凌晨执行冒烟测试。

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

---

## 👤 作者

- **你的名字** - [GitHub](https://github.com/你的用户名)

---
