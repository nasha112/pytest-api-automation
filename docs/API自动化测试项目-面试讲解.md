# Pytest API 自动化测试框架 —— 面试讲解手册（完整测试流程拆解）

> 本文档基于项目 
>
> `pytest-api-automation-framework-main`
>
>  的真实代码与真实执行痕迹整理，
> 覆盖从
>
> **需求分析 → 测试方案 → 用例设计 → 测试执行 → Bug 跟踪 → 持续集成**
>
> 的完整闭环。
> 每一章都包含 "我在做什么、产出了什么、面试官问起来怎么讲" 三个层次。



***

## 目录



* [一、项目速览（30 秒自我介绍版）](#一项目速览30-秒自我介绍版)

* [二、需求分析阶段](#二需求分析阶段)

* [三、测试方案设计](#三测试方案设计)

* [四、用例设计阶段（面试重点）](#四用例设计阶段面试重点)

* [五、测试执行阶段](#五测试执行阶段)

* [六、Bug 跟踪与缺陷管理（真实复盘）](#六bug-跟踪与缺陷管理真实复盘)

* [七、工程化与持续集成](#七工程化与持续集成)

* [八、项目亮点与 STAR 话术](#八项目亮点与-star-话术)

* [九、面试高频追问 Q\&A](#九面试高频追问-qa)

* [十、当前代码风险与改进建议（务必看）](#十当前代码风险与改进建议务必看)

* [附录：关键代码导读](#附录关键代码导读)



***

## 一、项目速览（30 秒自我介绍版）



| 项目维度   | 内容                                                                                                    |
| ------ | ----------------------------------------------------------------------------------------------------- |
| 项目定位   | 基于 Python + Pytest + Requests 的 REST API 自动化测试框架，重点展示接口自动化的**完整工程化流程**                                |
| 被测对象 1 | GoRest 公网用户管理 API（`https://gorest.co.in`，Bearer Token 鉴权）                                             |
| 被测对象 2 | 本地 "考试管理系统"API（`http://localhost:8101`，管理员登录 + 考试 / 试卷 / 规则 / 题库 / 试题模块）                              |
| 技术栈    | Python 3.13、pytest 8.4.1、requests、jsonschema、openpyxl、allure-pytest、pytest-env、GitHub Actions、Jenkins |
| 测试类型   | 冒烟测试、正向功能测试、负向测试、边界测试、数据驱动测试、响应结构（Schema）校验                                                           |
| 用例规模   | 24 条用例（含参数化实例）：GoRest 7 条 + Exam 17 条；冒烟用例单条覆盖 5 个核心接口                                                |
| 工程化    | 多环境切换（public /local）、请求封装、Fixture 依赖管理、Allure 报告、GitHub Actions + Jenkins 双 CI                        |
| 关键结果   | GoRest 7 用例全过（耗时 129s）；Jenkins 流水线两轮构建全绿；Allure 报告 100% 通过                                            |

**一句话自我介绍（面试开场背熟）**：

> 我这个项目是一个面向接口自动化测试的工程化框架。我以公网 GoRest 用户接口和本地一套考试管理系统接口为被测对象，完整走了一遍从需求分析、用例设计、框架搭建、测试执行到缺陷跟踪和 CI 集成的流程。框架实现了请求层封装、多环境切换、Excel 数据驱动、JSON Schema 响应校验和 Allure 报告，并且接入了 GitHub Actions 和 Jenkins 两条 CI 流水线。整个过程中我真实发现并闭环了 4 类典型问题 —— 包括测试脚本自身缺陷、环境鉴权配置缺失、业务实现与预期不符等。



***

## 二、需求分析阶段

### 2.1 被测对象梳理

需求分析的第一步是**搞清楚被测系统是什么、有哪些接口、怎么鉴权、数据长什么样**。我梳理了两个被测对象：

**对象一：GoRest 公网用户管理 API**



| 项目    | 内容                                                                                                   |
| ----- | ---------------------------------------------------------------------------------------------------- |
| 接口地址  | `https://gorest.co.in`                                                                               |
| 鉴权方式  | HTTP Header `Authorization: Bearer <token>`                                                          |
| 核心接口  | `POST /public/v2/users`（创建用户）、`GET /public/v2/users/{id}`（查询用户）、`DELETE /public/v2/users/{id}`（删除用户） |
| 业务字段  | `name`、`email`、`gender`（male/female）、`status`（active/inactive）                                       |
| 已知状态码 | 201（创建成功）、200（查询成功）、204（删除成功）、401（无效 Token）、422（参数校验失败，如缺少字段 / 重复邮箱）                                 |

**对象二：本地考试管理系统 API**



| 项目     | 内容                                                                                                                                                                                                                                          |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 接口地址   | `http://localhost:8101`                                                                                                                                                                                                                     |
| 业务模块   | 登录、考试（exam）、试卷（paper）、考试规则（rule）、题库（qu/repo）、试题（qu）                                                                                                                                                                                         |
| 核心接口   | `POST /exam/api/sys/user/login`（管理员登录）、`POST /exam/api/exam/exam/paging`（考试列表）、`POST /exam/api/paper/paper/paging`（试卷列表）、`POST /exam/api/paper/rule/paging`（规则列表）、`POST /exam/api/qu/repo/paging`（题库列表）、`POST /exam/api/qu/qu/paging`（试题列表） |
| 统一响应结构 | `{ "code": 0, "msg": "操作成功！", "data": { ... } }`，`code=0` 表示业务成功                                                                                                                                                                            |
| 分页结构   | `data.current`、`data.pages`、`data.records`（数组）                                                                                                                                                                                              |
| 技术栈推断  | 响应字段含 `hitCount`、`optimizeCountSql`、`orders` 等 MyBatis-Plus 特征字段，判断后端是 **Spring Boot + MyBatis-Plus**；`dataSources.xml` 确认数据库为 **MySQL 8（api\_test\_db@**[localhost:3306](https://localhost:3306)**）**                                      |
| 登录凭证   | `admin / 123456`（通过查询数据库 `sys_log` 表反查确认有效，见测试代码注释）                                                                                                                                                                                         |

**面试怎么讲**：

> 做接口测试的第一步不是写代码，而是把被测系统摸透。我对两个系统分别梳理了接口清单、鉴权方式、响应结构和业务字段。对本地考试系统，我通过前端抓包拿到了接口路径，通过响应结构里的 MyBatis-Plus 特征字段判断出它的技术栈，通过数据库表反查确认了测试账号 —— 这样后面设计用例和造数据才有依据。

### 2.2 测试目标与范围界定

需求分析要回答 "**测什么、不测什么、测到什么程度**"：



| 维度    | 本项目的界定                                                  |
| ----- | ------------------------------------------------------- |
| 功能正确性 | 正向流程（创建→查询→删除全生命周期）、核心业务规则（如考试得分 ≤ 总分、试题题型枚举合法）         |
| 健壮性   | 负向输入（错误凭证、缺失字段、非法参数类型）、边界输入（分页 current/size 的 0、极小、极大值） |
| 响应质量  | HTTP 状态码 + 业务状态码 + 响应结构三层校验，并用 JSON Schema 做字段级约束       |
| 稳定性基线 | 对 5 个核心列表接口做冒烟测试，保证主链路可用                                |
| 明确不做  | 性能压测、安全渗透、UI 层测试（本项目专注接口层）                              |

**范围确定的方式**：以接口文档 + 实际抓包 + 数据库为事实来源，先保证 "主链路 + 典型异常 + 边界" 三类覆盖，不追求用例数量。

### 2.3 测试环境与数据准备



| 环境         | 地址                      | 用途          | 前置条件             |
| ---------- | ----------------------- | ----------- | ---------------- |
| public（公网） | `https://gorest.co.in`  | GoRest 用户接口 | 有效 `AUTH_TOKEN`  |
| local（本地）  | `http://localhost:8101` | 考试管理系统      | 本地服务已启动、MySQL 可用 |

**数据准备（面试里很加分的细节）**：



1. **测试账号**：通过查询 `sys_log` 表确认 `admin/123456` 是有效登录账号（不是猜的，是数据库反查的）。

2. **用户测试数据**：维护了 4 组用户数据（`user_data.xlsx` / `user_data.json` 双数据源），字段覆盖 name/email/gender/status，gender 覆盖 male/female。

3. **Token 管理**：公网环境用固定 Token；本地环境在执行时动态登录获取 Token，并在整个测试会话内复用（避免每个用例都登录）。

4. **数据清理策略**：GoRest 用例设计为 "创建→查询→删除" 闭环，用例结束后删除自己创建的数据，保证**可重复执行、不污染环境**。

### 2.4 需求分析产出物



* 接口清单与鉴权方式表（见 2.1）

* 测试范围矩阵（见 2.2）

* 环境与数据准备清单（见 2.3）

* 测试策略：按 "冒烟 → 正向 → 负向 → 边界" 分级设计用例

**面试怎么讲**：

> 需求分析阶段我产出了接口清单、范围矩阵和环境数据清单。我的原则是：每个接口的每个断言都必须有依据，比如登录账号是查数据库确认的、响应结构是从真实响应里总结的，绝不靠猜。



***

## 三、测试方案设计

### 3.1 技术选型及理由



| 技术                       | 选型理由（面试话术）                                                |
| ------------------------ | --------------------------------------------------------- |
| Python                   | 生态成熟、上手快、适合快速搭建测试框架，团队可维护性好                               |
| pytest                   | 天然支持 Fixture、参数化、插件体系，断言简单，收集 / 执行 / 报告都强于 unittest       |
| requests                 | 最主流的 HTTP 客户端，`Session` 能复用连接和 Cookie，适合做请求封装             |
| pytest-env               | 把环境配置（BASE\_URL、AUTH\_TOKEN）注入为环境变量，配置与代码分离               |
| jsonschema               | 对响应做结构级校验，弥补 "只看状态码" 的不足                                  |
| openpyxl                 | 读取 Excel 测试数据，实现数据驱动                                      |
| allure-pytest            | 生成美观可追溯的测试报告，支持 feature/story/severity/step/attachment 分层 |
| GitHub Actions + Jenkins | 分别验证 "云端 CI" 和 "企业级流水线" 两种集成方式                            |

### 3.2 框架分层架构

框架采用**四层结构 + 一条 Fixture 依赖链**：



```
┌─────────────────────────────────────────────────────────────┐

│  用例层 tests/                                              │

│  test\_users.py  test\_users\_negative.py                       │

│  test\_exam\_login.py  test\_exam\_core\_api\_smoke.py             │

│  test\_exam\_negative.py  test\_exam\_boundary.py                │

├─────────────────────────────────────────────────────────────┤

│  数据层 tests/user\_data.xlsx / user\_data.json + schemas/     │

│  Excel 数据驱动、JSON Schema 校验模板                         │

├─────────────────────────────────────────────────────────────┤

│  公共层 conftest.py + libraries/request\_client.py            │

│  环境切换、Token 管理、Fixture 注入、请求封装与日志            │

├─────────────────────────────────────────────────────────────┤

│  配置与工程化 pytest.ini / requirements.txt / CI              │

│  Allure 报告、GitHub Actions、Jenkinsfile                    │

└─────────────────────────────────────────────────────────────┘
```

数据流：



```
pytest --env=public/local

&#x20;     ↓

conftest.py 注册 --env 参数

&#x20;     ↓

base\_url fixture（按环境返回 URL）

&#x20;     ↓

Token fixture（public 取配置 / local 动态登录）

&#x20;     ↓

RequestClient fixture（封装 Session + Header + Cookie）

&#x20;     ↓

测试用例（参数化数据 + 三层断言 + Allure 记录）
```

### 3.3 测试策略与用例分级



| 级别           | 用途        | 执行时机    | 对应文件                                             |
| ------------ | --------- | ------- | ------------------------------------------------ |
| 冒烟（smoke）    | 核心主链路快速验证 | 每次构建必跑  | `test_exam_core_api_smoke.py`                    |
| 正向（positive） | 验证正确功能    | 功能 / 回归 | `test_users.py`、`test_exam_login.py`             |
| 负向（negative） | 验证异常处理    | 功能 / 回归 | `test_users_negative.py`、`test_exam_negative.py` |
| 边界（boundary） | 验证输入边界    | 功能 / 回归 | `test_exam_boundary.py`                          |

**面试怎么讲**：

> 方案设计上我做了两件事：一是分层，把请求封装、数据、用例、报告分开，用例代码只关心业务断言；二是分级，冒烟测试保证主链路，正向 / 负向 / 边界保证质量覆盖。这样 CI 里可以先跑冒烟，失败了快速止损。



***

## 四、用例设计阶段（面试重点）

### 4.1 用到的用例设计方法



| 方法      | 在本项目的应用                                                          |
| ------- | ---------------------------------------------------------------- |
| 等价类划分   | 分页 `current`/`size` 的 "有效值 / 无效值 / 边界值"；登录的 "正确凭证 / 错误凭证 / 缺失字段" |
| 边界值分析   | `current=0/1/99999`、`size=0/1/9999`（小于最小值、最小值、正常值、超大值）           |
| 错误推测    | 无效 Token、重复邮箱、非数字类型参数、搜索不存在数据                                    |
| 场景法     | GoRest 用户 "创建→查询→删除" 完整生命周期场景；Exam 管理员登录后访问 5 个核心接口的主场景          |
| 状态与规则校验 | 试题题型枚举 `quType ∈ [1,2,3,4]`、考试业务规则 `userScore ≤ totalScore`      |

### 4.2 GoRest 用户管理用例设计

#### 4.2.1 正向用例：用户完整生命周期（4 条，Excel 数据驱动）



| 用例编号       | 用例名                                              | 步骤                                       | 断言                                                            |
| ---------- | ------------------------------------------------ | ---------------------------------------- | ------------------------------------------------------------- |
| USR-01\~04 | `test_can_create_user[name-email-gender-status]` | ① POST 创建用户 → ② GET 查询用户 → ③ DELETE 删除用户 | ① 状态码 201 + Schema 校验通过 → ② 状态码 200 + Schema 校验通过 → ③ 状态码 204 |

设计要点：



* **闭环设计**：每个用例创建的数据在用例内删除，保证幂等可重复执行；

* **参数化 ×4**：4 组数据（riju/manoj/sanjib/petli），覆盖 gender 的 male/female；

* **Schema 校验**：创建和查询的响应都必须满足 `success_user_schema.json`（id 为 integer、email 格式合法、gender/status 枚举合法、5 个字段全部必填）；

* **Allure 埋点**：severity=CRITICAL，每个步骤独立记录，请求 / 响应 JSON 作为附件。

#### 4.2.2 负向用例（3 条）



| 用例编号   | 用例名                                | 输入                            | 预期  | 校验方式                                   |
| ------ | ---------------------------------- | ----------------------------- | --- | -------------------------------------- |
| USR-N1 | `test_create_user_invalid_token`   | 错误的 Bearer Token + 合法用户数据     | 401 | 状态码 + error Schema（`{message}`）        |
| USR-N2 | `test_create_user_missing_fields`  | 只传 name，缺 email/gender/status | 422 | 状态码 + error Schema（数组，含 field/message） |
| USR-N3 | `test_create_user_duplicate_email` | 先用某邮箱创建，再重复创建                 | 422 | 状态码 + error Schema（数组）                 |

设计要点：**错误响应的结构也要校验**（对象型 vs 数组型），说明测试不止看状态码。

### 4.3 Exam 登录用例设计



| 用例编号     | 用例名                     | 输入           | 预期                                    |
| -------- | ----------------------- | ------------ | ------------------------------------- |
| LOGIN-P1 | `test_exam_admin_login` | admin/123456 | 200 + 响应含 token 或 code 字段（记录返回 Token） |

负向（见 4.5 的负向测试组）：错误密码、错误用户名、缺密码、缺用户名 → 均预期 **HTTP 200 + 业务 code ≠ 0**（后端用业务码表达登录失败）。

**设计说明**：这是 "HTTP 状态码与业务状态码分离" 的典型场景 —— 登录失败 HTTP 仍是 200，必须断言业务码。

### 4.4 Exam 核心接口冒烟用例（三层断言模型）

单条用例覆盖 5 个核心接口（考试列表、试卷列表、规则列表、题库列表、试题列表），每个接口做**三层校验**：



```
第一层：HTTP 状态码 == 200

&#x20;   ↓

第二层：业务状态码 code == 0（msg 为"操作成功！"）

&#x20;   ↓

第三层：响应结构与业务规则

&#x20;  ├─ 分页结构：data.current / data.pages / data.records(数组) 必须存在

&#x20;  ├─ 考试记录业务规则：userScore <= totalScore（得分不能超过总分）

&#x20;  └─ 试题业务规则：id/content/quType 必填、id 与 content 为字符串、quType ∈ \[1,2,3,4]（1单选/2多选/3判断/4简答）
```

**面试怎么讲**：

> 冒烟用例我做了三层断言：先看 HTTP 状态码，再看业务状态码，最后校验响应结构和业务规则。很多接口 HTTP 200 但业务上已经失败，只看状态码会漏掉问题。第三层我还校验了真实业务规则，比如考试得分不能大于总分、试题题型必须落在枚举范围内。

### 4.5 Exam 分页边界用例设计（等价类 + 边界值）

被测接口：`POST /exam/api/exam/exam/paging`，参数 `current`（页码）、`size`（每页条数）。

**边界值分析**：



| 参数      | 取值    | 设计依据  | 真实后端行为（已实测确认）           |
| ------- | ----- | ----- | ----------------------- |
| current | 0     | 小于最小值 | 后端自动修正为 1               |
| current | 1     | 最小值   | 正常返回第一页                 |
| current | 99999 | 超大值   | 后端接受，返回空列表或最后一页，不崩溃     |
| size    | 0     | 小于最小值 | 后端按默认值处理（实测返回 ≤10 条）    |
| size    | 1     | 最小值   | 返回不超过 1 条               |
| size    | 9999  | 超大值   | 后端有最大值限制（实测 ≤100 条），不崩溃 |

**用例实现**（参数化，共 8 条实例）：



| 用例名                     | 参数化数据                     | 断言重点                                       |
| ----------------------- | ------------------------- | ------------------------------------------ |
| `test_current_boundary` | (0,1)、(1,1)、(99999,99999) | current=0 被修正为 1；结构完整（records 数组、pages 存在） |
| `test_size_boundary`    | (0,10)、(1,1)、(9999,100)   | 返回记录数不超过上限；size 字段为非负整数                    |
| `test_current_normal`   | current=1                 | 返回 current==1，结构完整                         |
| `test_size_normal`      | size=1                    | 返回记录数 ≤ 1                                  |

**设计要点**：边界值来自 "对后端行为先探测、后固化"—— 先手动调接口确认真实行为，再把真实行为写进断言，避免用例写 "想当然" 的预期。

### 4.6 数据驱动设计



* **双数据源**：`user_data.xlsx`（openpyxl 读取）+ `user_data.json`（备用）；

* **流程**：Excel → openpyxl → 读取函数 → `pytest.mark.parametrize` → 用例执行；

* **价值**：测试数据与测试代码分离，加数据不改代码；新用户数据只动 Excel。

### 4.7 用例设计小结



* 用例总数：**24 条**（GoRest 7 + Exam 17），按 "冒烟 / 正向 / 负向 / 边界" 四级分布；

* 覆盖维度：正确性、鉴权、参数校验、边界、业务规则、响应结构；

* 每条用例都有明确的输入、步骤、断言和数据来源，可追溯。

**面试怎么讲**：

> 用例设计我用了等价类、边界值、错误推测和场景法。我的两个设计原则：一是 "闭环 + 幂等"，正向用例自建自删数据；二是 "断言有依据"，所有预期值都来自真实探测和需求确认，不写拍脑袋的断言。



***

## 五、测试执行阶段

### 5.1 执行前准备



1. **安装依赖**：`pip install -r requirements.txt`（pytest、requests、jsonschema、openpyxl、allure-pytest 等）；

2. **启动被测环境**：本地启动考试管理系统（监听 8101）+ MySQL；

3. **配置环境变量**：公网 AUTH\_TOKEN（建议用环境变量 / GitHub Secrets，不写死）；

4. **确认执行目标**：按环境（public/local）和按文件粒度执行。

### 5.2 执行链路（Fixture 如何工作）



```
pytest --env=local tests/local/

&#x20;  ↓

configure\_logging（session 级自动 fixture，写日志）

&#x20;  ↓

env（读取 --env 参数）

&#x20;  ↓

base\_url（local → http://localhost:8101）

&#x20;  ↓

exam\_token（session 级：整个会话只登录一次，所有用例复用 Token）

&#x20;  ↓

exam\_client（RequestClient + Token Header + Admin-Token Cookie）

&#x20;  ↓

测试用例
```

**设计亮点**：`exam_token` 是 session 级 fixture，**一次登录全会话复用**，避免每个用例都走登录流程，大幅降低执行时间和外部依赖。

### 5.3 执行命令与分环境策略



| 场景          | 命令                                                                                                                |
| ----------- | ----------------------------------------------------------------------------------------------------------------- |
| GoRest 正向   | `pytest -v tests/test_users.py`                                                                                   |
| GoRest 负向   | `pytest -v tests/test_users_negative.py`                                                                          |
| Exam 全部     | `pytest -v --env=local tests/local/`                                                                              |
| Exam 冒烟     | `pytest -v --env=local tests/local/test_exam_core_api_smoke.py`                                                   |
| Exam 边界     | `pytest -v --env=local tests/local/test_exam_boundary.py`                                                         |
| 生成报告        | 默认 `--alluredir=reports/allure-results`；`allure serve reports/allure-results` 查看                                  |
| CI（Jenkins） | `pytest --maxfail=1 --disable-warnings -q --alluredir=allure-results --junitxml=allure-results/junit-results.xml` |

**CI 策略说明**：本地 Exam 系统依赖 `localhost:8101`，CI 环境无法访问，所以 CI 以公网 GoRest 测试为主测试对象 —— 这是 "测试环境与 CI 环境隔离" 的工程化取舍。

### 5.4 真实执行结果（有据可查）

**① GoRest 7 用例一次全过（**`results.xml`**，2025-09-11）**



| 用例                                   | 耗时                        |
| ------------------------------------ | ------------------------- |
| test\_can\_create\_user\[riju...]    | 33.8s                     |
| test\_can\_create\_user\[manoj...]   | 36.8s                     |
| test\_can\_create\_user\[sanjib...]  | 18.7s                     |
| test\_can\_create\_user\[petli...]   | 13.5s                     |
| test\_create\_user\_invalid\_token   | 1.9s                      |
| test\_create\_user\_missing\_fields  | 11.2s                     |
| test\_create\_user\_duplicate\_email | 12.7s                     |
| **合计**                               | **129s，7 条全通过，0 失败 0 错误** |

> 观察：创建 / 删除用户耗时明显高于负向用例，公网接口响应慢，说明
>
> **接口自动化执行时间受网络环境影响**
>
> ，这是设计 CI 超时和用例分组时要考虑的。

**② Allure 报告（Jenkins 构建 #12，9/7 18:29–18:31，共 2m22s）**



* Overview：14 条用例记录（pytest /tests 两个包层级各 7 条，同一批 7 个用例的层级展示），100% 通过；

* 用例详情示例：`test_can_create_user[manoj]` 28.8s，步骤拆解为 Create User (POST) 16.5s → Get User (GET) 0.9s → Delete User (DELETE) 11.5s，每个步骤带请求 / 响应附件；

* Graphs：severity 分布 critical 5 /normal 9；耗时分布集中在 10–35s；

* Environment：记录 BASE\_URL、AUTH\_TOKEN 等执行环境信息，报告可复现；

* Executors：标注执行来源为 Jenkins `api-tests-pipeline #12`。

**③ Jenkins 流水线（**`docs/Stage_view.png`**）**



* 构建 #12 全绿：Checkout SCM 1s → Checkout 1s → Setup Python 4s → Run Tests 2min20s → Archive Results 129ms → Allure Report 10s，全程约 2min55s；

* 构建 #11：测试 7 条全过，但 **Allure Report 阶段失败（124ms）**—— 报告生成环节出问题，测试结果本身正常；

* 产物：allure-report.zip（1.02 MiB）、test\_log.log（3.31 KiB）；

* Test Result Trend：#11、#12 两轮均为 7 passed，稳定。

**④ 复验记录（2026-09-17，**`util.py`**&#x20;恢复后实跑）**



* 恢复缺失的 `libraries/util.py` 后，GoRest 7 条用例可正常收集执行，不再报 `ModuleNotFoundError`；

* 两轮实跑中 7 条用例**每条都至少通过过一次**，证明代码逻辑正确；

* 偶发失败全部为访问 gorest.co.in 的**间歇性网络连接重置**（`ConnectionResetError 10054`，连通性探测 5 次中 2 次 200 / 3 次重置）；

* 实测配置的 `AUTH_TOKEN` 仍然有效（受保护接口返回 200），但**建议更换**——Token 已明文提交在仓库中（见第十章风险 2）。

**面试怎么讲**：

> 执行阶段我有三条经验：一是用 Fixture 链管理环境依赖，登录 Token 全会话复用；二是分层跑用例，冒烟先行；三是用 Allure + Jenkins 把执行过程沉淀成可追溯报告。我还在 Jenkins 里真实遇到过 #11 构建 "测试全过但报告阶段失败" 的情况，说明 CI 每个环节都可能挂，不能只看测试结果。

### 5.5 报告解读（Allure 报告怎么讲）



| 报告板块        | 怎么解读                                              |
| ----------- | ------------------------------------------------- |
| Overview    | 总用例数、通过率、执行时长、套件结构 —— 先讲结论 "这次构建质量如何"             |
| Suites      | 按测试类看用例明细，点进单条看步骤耗时和请求 / 响应附件 —— 讲 "问题能定位到具体请求"   |
| Graphs      | severity 分布（critical/normal）、耗时分布 —— 讲 "用例优先级和效率" |
| Environment | BASE\_URL、Token 等环境信息 —— 讲 "报告可复现"                |
| Executors   | 执行来源（Jenkins 流水线编号）—— 讲 "CI 与报告打通"                |

### 5.6 本地执行 vs CI 执行差异



| 维度       | 本地                 | CI                                     |
| -------- | ------------------ | -------------------------------------- |
| 执行对象     | GoRest + Exam 本地系统 | GoRest（公网可访问）                          |
| 环境变量     | pytest.ini/ 本机环境变量 | GitHub Secrets / Actions 内注入           |
| Token 安全 | 本地可明文              | CI 中脱敏为 `Bearer ****` 再写入报告            |
| 失败止损     | 手动分析               | `--maxfail=1` 快速失败 + JUnit/Allure 报告留痕 |



***

## 六、Bug 跟踪与缺陷管理（真实复盘）

> 这一章是面试的
>
> **差异化亮点**
>
> 。下面 4 个案例全部来自项目里真实保留的 Allure 执行记录（
>
> `allure-results/`
>
> 、
>
> `reports/allure-results/`
>
>  中的 failed/broken 结果），不是编的。

### 6.1 缺陷分类框架

接口自动化中发现的问题，我按来源分四类，处理方式完全不同：



| 类型          | 定义        | 处理方式        |
| ----------- | --------- | ----------- |
| 产品 / 后端 Bug | 实现与需求不符   | 提缺陷单，推动开发修复 |
| 用例预期错误      | 测试写错了预期   | 修正用例，沉淀为经验  |
| 测试脚本缺陷      | 脚本本身写错    | 修脚本，避免误报    |
| 环境问题        | 环境 / 配置导致 | 记录环境行为，标注差异 |

### 6.2 缺陷案例复盘

#### 案例 1：测试脚本缺陷 —— `NameError: name 'requests' is not defined`



* **现象**：GoRest 负向用例执行报 `broken`（脚本错误），而非 `failed`（断言失败）。Allure 留痕：`NameError: name 'requests' is not defined`。

* **根因**：早期版本的 `test_users_negative.py` 直接调用 `requests.post(...)` 但没有 `import requests`。

* **处理**：重构用例，不再直接用 `requests`，改为复用框架封装的 `RequestClient`（`bad_client = RequestClient(base_url, headers=bad_headers)`），错误 Token 场景通过新建临时 client 实现。

* **结论**：脚本缺陷会造成**误报**（用例看起来挂了，实际是脚本问题）。所以测试代码也要走代码评审；同时把请求全部收敛到封装层，杜绝用例里裸写 HTTP 细节。

* **面试讲法**：这是我自己踩过的坑 —— 自动化测试的报错要区分 `failed`（断言失败 = 可能发现 Bug）和 `broken`（脚本错误 = 测试自身问题），broken 需要先修测试，不能直接当成产品 Bug 提。

#### 案例 2：环境配置问题 —— 无效 Token 访问接口竟然返回成功



* **现象**：`test_api_invalid_token` 断言 "无效 Token 应返回非 0 业务状态码"，实际返回 `code=0` + 完整数据，断言失败。

* **根因**：当前**开发环境**的 `/exam/api/**` 接口配置为 `permitAll`（后端日志显示 "No applicable constraints defined"），**根本没有启用 Token 鉴权**。这是环境配置问题，不是接口逻辑 Bug。

* **处理**：把用例改造成**行为记录型**——`test_invalid_token_behavior` 只验证接口可正常访问并记录 "开发环境未开启鉴权" 这个事实，同时在报告里标注 "该行为在预发布 / 生产环境会改变，上线前必须补安全测试"。

* **结论**：测试要区分 "预期该拦截却放行" 和 "环境本来就没配"。发现鉴权缺失是个**高价值安全信号**，我把它作为环境风险项记录并提示上线前回归。

* **面试讲法**：我通过这个案例学会了不盲信测试预期 —— 测试失败时先定位是 "产品 Bug" 还是 "环境配置"，避免把环境问题错报成功能 Bug；同时这类发现要升级为安全测试项。

#### 案例 3：用例预期错误 —— 搜索不存在的名称返回了 2 条数据



* **现象**：`test_search_non_existent_data` 断言 "搜索不存在数据应返回空列表"，实际返回 2 条记录。

* **根因**：后端搜索实现是**模糊查询**（关键词无匹配时返回全部数据），与 "搜不到应返回空" 的常规预期不符。严格说这是**产品行为设计问题**（模糊搜索的降级策略），但当前是既定实现。

* **处理**：用例降级为只校验 "接口正常响应 + records 为数组"（不崩溃、结构正确），并在 Allure 附件中记录该行为差异，作为**产品改进建议**沉淀（搜索无匹配时建议返回空列表）。

* **结论**：发现预期与实现不符时，要判断 "这是 Bug 还是设计如此"。本项目按 "设计如此" 处理并记录在案；如果面试官追问，我会说这类问题会提给产品确认，而不是直接改用例掩盖。

* **面试讲法**：这体现了我对断言 "预期来源" 的把控 —— 预期必须来自需求确认或行为探测，并且发现差异时要区分 Bug 与设计并留痕。

#### 案例 4：用例预期错误 —— 非数字 current 返回 HTTP 400 而非业务错误码



* **现象**：`test_invalid_current_type` 早期预期 "HTTP 200 + 业务码非 0"，实际后端直接返回 HTTP 400。

* **根因**：后端对非法类型参数走框架级参数绑定校验，直接 400，不进入业务层。

* **处理**：修正用例预期为 "HTTP 400 + 响应体含 error/message"，与真实行为对齐。

* **结论**：接口对同一类错误可能走不同处理路径（框架层 400 vs 业务层 code≠0），用例预期必须和实现路径对齐。

* **面试讲法**：这个案例说明接口测试要理解 "框架层校验" 和 "业务层校验" 的区别，断言要分层设计。

> **补充观察（体现持续优化）**
>
> ：Allure 历史记录显示边界测试经历过一次重构 —— 早期是 
>
> `test_current_zero`
>
> 、
>
> `test_current_one`
>
> 、
>
> `test_current_large`
>
> 、
>
> `test_size_zero`
>
>  等 7 个独立函数，后来收敛为 
>
> `test_current_boundary`
>
> 、
>
> `test_size_boundary`
>
>  两组参数化用例，代码量减少、覆盖不变。这也是可讲的优化点：
>
> **用参数化消除重复用例**
>
> 。

### 6.3 缺陷生命周期与跟踪闭环



```
用例执行失败

&#x20;  ↓

区分类型：failed（断言失败） vs broken（脚本错误）

&#x20;  ↓

定位根因：产品逻辑 / 用例预期 / 脚本缺陷 / 环境配置（四选一）

&#x20;  ↓

处理：

&#x20; ├─ 产品 Bug → 提缺陷单（复现步骤、请求响应、日志附件）→ 开发修复 → 回归

&#x20; ├─ 预期错误 → 修正用例预期，记录行为差异 → 重跑

&#x20; ├─ 脚本缺陷 → 修复脚本 → 重跑（消除误报）

&#x20; └─ 环境问题 → 记录环境行为，标注环境差异 → 必要时升级为安全/配置跟踪项

&#x20;  ↓

结论沉淀：Allure 附件 + 代码注释（如"该行为已由实际运行确认"）
```

**面试怎么讲**：

> 我的缺陷跟踪是闭环的：失败先分类，再定位根因，然后按类型处理，最后把结论沉淀在报告和代码注释里。整个项目期间我处理了四类典型问题，每类都有真实案例，这让我在面试时能讲清楚 "自动化发现的问题不等于都是产品 Bug"。

### 6.4 测试结论输出

一次完整测试结束后输出的结论包含：



1. **执行概况**：用例总数、通过 / 失败 / 错误数、执行时长；

2. **缺陷清单**：每条缺陷的现象、根因、严重级别、状态；

3. **风险项**：环境配置类问题（如鉴权未开启）、行为差异（如模糊搜索）；

4. **质量结论**：主链路是否可用、是否可发布、遗留风险。



***

## 七、工程化与持续集成

### 7.1 GitHub Actions（`.github/workflows/pytest.yml`）



```
Push / PR 到 main

&#x20;  ↓

Checkout → Setup Python 3.10 → pip install -r requirements.txt

&#x20;  ↓

pytest -v --alluredir=reports/

&#x20;  ↓

写入 environment.properties（AUTH\_TOKEN 脱敏为 "Bearer \*\*\*\*"）+ executor.json

&#x20;  ↓

Upload Artifact（allure-results）

&#x20;  ↓

deploy job：下载产物 → allure generate → GitHub Pages 发布报告
```

**安全细节（面试加分）**：CI 中写入报告的 Token 做了**脱敏**（`Bearer ****`），避免凭据通过报告泄露；真正的 Token 通过 GitHub Secrets 注入。

### 7.2 Jenkins 流水线（Jenkinsfile）



```
Checkout（拉取 main 分支）

&#x20;  ↓

Setup Python（venv + 依赖安装）

&#x20;  ↓

Run Tests（pytest --maxfail=1 -q --alluredir=allure-results --junitxml=...）

&#x20;  ↓

Archive Results（归档 test\_log.log + JUnit 结果）

&#x20;  ↓

Allure Report（Allure 插件生成并发布报告）
```

真实运行（Stage\_view 截图）：构建 #12 全绿，总时长约 2min55s；构建 #11 出现 "测试 7 条全过但 Allure Report 阶段失败"，说明**报告生成环节也要纳入 CI 稳定性监控**。

### 7.3 报告发布链路



* 本地：`allure serve reports/allure-results`；

* Jenkins：Allure 插件内嵌报告（归档 allure-report.zip）；

* GitHub Actions：产物上传 + `peaceiris/actions-gh-pages` 发布到 GitHub Pages。

### 7.4 工程化亮点话术

> 我做了两条 CI：GitHub Actions 负责云端自动化与报告发布，Jenkins 负责企业级流水线（Stage View、JUnit 集成、产物归档）。两条流水线都接入了 Allure，执行过程和结果完全可追溯。CI 里我还处理了 Token 脱敏和本地服务不可达的环境隔离问题。



***

## 八、项目亮点与 STAR 话术



| # | 亮点             | 一句话话术（STAR 结构浓缩）                                                                       |
| - | -------------- | -------------------------------------------------------------------------------------- |
| 1 | 请求层封装          | 我用 `requests.Session` 封装了统一 RequestClient，用例里不再写 URL 拼接和 Header 管理，新增接口只写业务断言，开发效率提升明显 |
| 2 | 多环境切换          | 通过 `pytest --env=public/local` 一条命令切换被测环境，base\_url/Token/Client 全部由 Fixture 自动装配      |
| 3 | Fixture 依赖链    | 用 session 级 Fixture 实现 "整个会话只登录一次、Token 全量复用"，避免每个用例重复登录                               |
| 4 | 数据驱动           | 测试数据放 Excel/JSON，与代码分离，新增数据不改代码；用参数化消除重复用例                                             |
| 5 | JSON Schema 校验 | 响应不再只看状态码，用 Schema 约束字段类型、枚举和必填项，能捕获字段级回归                                              |
| 6 | 三层断言模型         | HTTP 状态码 → 业务状态码 → 结构与业务规则，覆盖 "200 但业务失败" 的盲区                                          |
| 7 | 真实缺陷闭环         | 项目期间真实处理 4 类问题（脚本缺陷 / 环境配置 / 预期错误 ×2），每类都能讲出根因和处理方案                                    |
| 8 | 双 CI           | GitHub Actions（云端自动 + Pages 报告）+ Jenkins（Stage View + JUnit + 产物归档）                    |



***

## 九、面试高频追问 Q\&A

**Q1：为什么选 pytest 而不是 unittest 或 Robot Framework？**

pytest 的 Fixture 机制做环境依赖管理最顺手（session/module/function 级），参数化简洁，插件生态（allure、env、xdist）成熟；unittest 需要写 setUp/tearDown，复用和参数化都笨重；Robot 关键字层太重，Python 团队维护成本高。

**Q2：接口自动化怎么断言？断言什么？**

三层：① HTTP 状态码（请求是否被正确受理）；② 业务状态码（业务是否成功，如 code=0）；③ 响应结构与业务规则（字段是否存在、类型、枚举、业务约束如得分≤总分）。部分场景还用 JSON Schema 做整体结构校验。

**Q3：Token 过期了怎么办？**

本项目本地环境用 session 级 fixture 登录一次拿 Token 全会话复用；如果 Token 有过期机制，可以在 RequestClient 里加响应拦截 —— 检测到 401 时自动重新登录并重放请求。这是后续可扩展点。

**Q4：用例之间有依赖吗？怎么处理？**

我的原则是**用例独立、自闭环**：正向用例自建自删数据；公共前置（登录、环境）放在 fixture 里。这样单条用例可以独立执行、可以乱序、可以并行（配合 xdist）。

**Q5：数据驱动和参数化的区别？**

参数化是 pytest 的机制（`pytest.mark.parametrize`），数据驱动是把测试数据外置到 Excel/JSON 再喂给参数化。本项目是 "外置数据 + 参数化" 的组合，好处是加数据不改代码。

**Q6：怎么保证用例可重复执行（幂等）？**

① 用例结束时清理自己创建的数据（创建→查询→删除闭环）；② 测试数据用唯一标识（时间戳 / 随机后缀可选）；③ 不依赖执行顺序。我当前用固定数据 + 自清理，扩展时可用唯一化处理。

**Q7：接口测试和 UI 测试怎么分工？**

接口测试跑在 CI 里做快速回归，覆盖主链路和异常；UI 测试覆盖用户操作路径和页面表现，频率低。接口发现问题更快、更稳定，UI 侧验证体验。项目定位是接口层，所以主要精力在接口。

**Q8：发现接口 Bug 怎么和开发沟通？**

提供最小复现：接口、方法、请求头、请求体、期望结果、实际结果、响应原文（Allure 附件就是干这个的）。用 "用例 + 响应截图" 说话，沟通效率高。

**Q9：覆盖率怎么评估？**

接口层面按 "接口覆盖率 × 场景覆盖率" 评估：每个接口是否覆盖了正向 / 负向 / 边界场景。本项目 24 条用例覆盖 8 类接口场景；业务规则层面看关键规则是否进入断言（如得分≤总分）。

**Q10：这个项目还能怎么优化？**

① 加数据库校验（MySQL 数据比对，已有 .idea 数据源配置）；② pytest-xdist 并行 + 数据隔离；③ Token 自动续期与请求重放；④ Mock 外部依赖；⑤ 定时任务 + 失败通知（飞书 / 钉钉）；⑥ 测试结果趋势看板。这些 README 里已列为扩展方向。



***

## 十、当前代码风险与改进建议（务必看）

> 我在通读代码时发现了几个
>
> **影响演示的真实问题**
>
> ，面试前必须处理，否则现场跑用例会翻车。

### ✅ 风险 1（已修复）：`libraries/util.py` 曾缺失，GoRest 正向用例无法执行



* **现象**：`tests/test_users.py` 顶部 `from libraries.util import read_excel_data, load_schema`，但项目中 `libraries/util.py`**&#x20;一度不存在**（历史执行记录显示该文件曾经存在，7 条 GoRest 用例全过）。

* **影响**：此前运行 `pytest tests/test_users.py` 会在收集阶段直接报 `ModuleNotFoundError`，正向用例全部跑不起来。

* **处理（2026-09-17）**：已从历史版本找回 `util.py` 恢复到 `libraries/`，实现：


  * `read_excel_data(path)`：openpyxl 读 Excel，跳过表头返回参数化数据；

  * `load_schema(name)`：读取 `schemas/` 下的 JSON Schema 返回 dict。

* **验证结果**：恢复后用例可正常收集执行；两轮实跑中 **7 条用例每条都至少通过过一次**（第 1 轮通过 petli 全生命周期、missing\_fields、duplicate\_email；第 2 轮通过 invalid\_token），证明框架代码逻辑正确。当前偶发失败均为访问 gorest.co.in 的**间歇性网络连接重置**（`ConnectionResetError 10054`），与代码无关；历史 `results.xml` 显示稳定网络下 7/7 全过（129s）。

### ⚠️ 风险 2：AUTH\_TOKEN 明文提交进仓库



* **现象**：`pytest.ini` 中写死了 `AUTH_TOKEN=Bearer 8a410a5a...`（真实 Token），且早期 Allure 报告（`docs/allure_overview.png`）的 Environment 板块也暴露了完整 Token。

* **影响**：仓库公开或泄露后 Token 可被盗用。

* **建议**：Token 改为系统环境变量 / GitHub Secrets 注入；README 里其实已经写了这条规范，说明你知道这个问题，可以顺手落实。

### ⚠️ 风险 3：残留文件



* `.github/workflows/temp.txt`：是 pytest.yml 的乱码副本，建议删除；

* `test_logs.log`：0 字节空文件，建议删除或归入 .gitignore；

* `logs/` 目录未在仓库中（conftest 会写 `logs/test.log`），执行时自动生成即可。

### 改进方向（README 已列，可对面试官说）

数据库校验、Mock、pytest-xdist 并行、定时执行、结果通知（飞书 / 钉钉）、更完整的 CI/CD 流程。



***

## 附录：关键代码导读

### 1. conftest.py —— Fixture 依赖链核心



```
\# ① 注册 --env 参数

def pytest\_addoption(parser):

&#x20;   parser.addoption("--env", action="store", default="public",

&#x20;                    choices=\["public", "local"])

\# ② 按环境返回 base\_url（环境变量优先，pytest.ini 兜底）

@pytest.fixture(scope="session")

def base\_url(env):

&#x20;   if env == "public":

&#x20;       return os.getenv("BASE\_URL", "https://gorest.co.in")

&#x20;   return os.getenv("BASE\_URL\_LOCAL", "http://localhost:8101")

\# ③ 本地环境：整个会话只登录一次，Token 全量复用

@pytest.fixture(scope="session")

def exam\_token(base\_url):

&#x20;   resp = requests.post(f"{base\_url}/exam/api/sys/user/login",

&#x20;                        json={"username": "admin", "password": "123456"}, timeout=5)

&#x20;   assert resp.status\_code == 200

&#x20;   token = (resp.json().get("data", {}).get("token")

&#x20;            or resp.json().get("data", {}).get("accessToken")

&#x20;            or resp.json().get("token"))

&#x20;   assert token

&#x20;   return token

\# ④ 封装客户端：自动带 Token Header + Cookie

@pytest.fixture(scope="session")

def exam\_client(base\_url, exam\_token):

&#x20;   client = RequestClient(base\_url, headers={"Token": exam\_token})

&#x20;   client.set\_cookie("Admin-Token", exam\_token)

&#x20;   return client
```

### 2. libraries/request\_client.py —— 请求封装



```
class RequestClient:

&#x20;   def \_\_init\_\_(self, base\_url, headers=None):

&#x20;       self.base\_url = base\_url.rstrip('/')

&#x20;       self.session = requests.Session()

&#x20;       if headers:

&#x20;           self.session.headers.update(headers)

&#x20;   def build\_url(self, path):

&#x20;       if path.startswith("http"):

&#x20;           return path

&#x20;       return f"{self.base\_url}/{path.lstrip('/')}"

&#x20;   def get(self, path, \*\*kwargs):  return self.session.get(self.build\_url(path), \*\*kwargs)

&#x20;   def post(self, path, \*\*kwargs): return self.session.post(self.build\_url(path), \*\*kwargs)

&#x20;   def put(self, path, \*\*kwargs):  return self.session.put(self.build\_url(path), \*\*kwargs)

&#x20;   def delete(self, path, \*\*kwargs): return self.session.delete(self.build\_url(path), \*\*kwargs)

&#x20;   def set\_header(self, key, value): self.session.headers\[key] = value

&#x20;   def set\_cookie(self, key, value): self.session.cookies.set(key, value)
```

### 3. 三层断言 —— 冒烟测试通用校验



```
def assert\_api\_response(resp):

&#x20;   assert resp.status\_code == 200                       # 第一层：HTTP

&#x20;   data = resp.json()

&#x20;   assert data.get("code") == 0, data.get("msg", "")    # 第二层：业务码

&#x20;   return data

def assert\_pagination\_structure(data):

&#x20;   page\_data = data.get("data")

&#x20;   assert page\_data is not None

&#x20;   assert "current" in page\_data and "pages" in page\_data and "records" in page\_data

&#x20;   assert isinstance(page\_data\["records"], list)        # 第三层：结构

&#x20;   return page\_data\["records"], page\_data
```

### 4. 参数化边界用例



```
@pytest.mark.parametrize("current, expected\_current", \[

&#x20;   (0, 1),        # current=0 → 后端自动修正为 1

&#x20;   (1, 1),        # 正常值

&#x20;   (99999, 99999) # 超大值，后端接受不崩溃

])

def test\_current\_boundary(exam\_client, current, expected\_current):

&#x20;   ...
```

### 5. GoRest 正向用例（生命周期 + Schema）



```
@pytest.mark.parametrize("name,email,gender,status", user\_data)

def test\_can\_create\_user(public\_client, end\_point, name, email, gender, status):

&#x20;   # ① 创建：201 + Schema 校验

&#x20;   post\_response = public\_client.post(end\_point, json={...}, timeout=10)

&#x20;   assert post\_response.status\_code == 201

&#x20;   user\_id = post\_response.json()\["id"]

&#x20;   validate(instance=post\_response.json(), schema=success\_schema)

&#x20;   # ② 查询：200 + Schema 校验

&#x20;   get\_response = public\_client.get(f"{end\_point}{user\_id}", timeout=10)

&#x20;   assert get\_response.status\_code == 200

&#x20;   validate(instance=get\_response.json(), schema=success\_schema)

&#x20;   # ③ 删除：204

&#x20;   delete\_response = public\_client.delete(f"{end\_point}{user\_id}", timeout=10)

&#x20;   assert delete\_response.status\_code == 204
```



***

*本文档全部结论基于项目真实代码与真实执行痕迹（allure-results、reports/allure-results、results.xml、docs 截图、Jenkinsfile、CI 配置）整理，可作为面试讲述的事实依据。*