"""
本地 Exam 系统核心接口冒烟测试
覆盖：考试列表、试卷列表、规则列表、题库列表、试题列表
验证：HTTP 200 + code 0 + 分页结构 + 核心字段
"""
import allure
import time
import json


# ======================== 通用校验函数 ========================
def assert_api_response(resp):
    """
    第一层：所有接口的基础响应校验
    Exam 系统统一返回格式：
    {
        "code": 0,
        "msg": "操作成功！",
        "data": { ... }
    }
    """
    assert resp.status_code == 200, f"HTTP状态码异常: {resp.status_code}"

    data = resp.json()
    assert data.get("code") == 0, f"业务状态码异常: {data.get('msg', '')}"
    return data


def assert_pagination_structure(data):
    """
    第二层：分页接口的结构校验
    所有列表接口都有 data.current / data.pages / data.records
    """
    page_data = data.get("data")
    assert page_data is not None, "缺少 data 字段"

    assert "current" in page_data, "缺少 current 字段"
    assert "pages" in page_data, "缺少 pages 字段"
    assert "records" in page_data, "缺少 records 字段"

    records = page_data["records"]
    assert isinstance(records, list), "records 应为数组"

    return records, page_data


def assert_exam_record_business(records):
    """
    第三层：考试记录的业务规则校验
    选取最有价值的业务规则：得分 <= 总分
    """
    for record in records:
        user_score = record.get("userScore", 0)
        total_score = record.get("totalScore", 0)
        assert user_score <= total_score, \
            f"得分 {user_score} > 总分 {total_score}"


def assert_question_business(records):
    """
    第三层：试题列表的业务规则校验
    验证核心字段 + 题型范围
    """
    for question in records:
        # 核心字段存在
        assert "id" in question, "缺少 id"
        assert "content" in question, "缺少 content"
        assert "quType" in question, "缺少 quType"

        # 字段类型
        assert isinstance(question["id"], str), "id 应为字符串"
        assert isinstance(question["content"], str), "content 应为字符串"

        # 题型范围：1-单选, 2-多选, 3-判断, 4-简答
        assert question["quType"] in [1, 2, 3, 4], \
            f"quType 值异常: {question['quType']}，应为 1/2/3/4"


def build_payload(params=None):
    """构造分页请求体（简单工具函数）"""
    return {
        "current": 1,
        "size": 10,
        "params": params or {},
        "t": int(time.time() * 1000)
    }


# ======================== 测试用例 ========================
@allure.feature("本地Exam系统")
@allure.story("核心接口冒烟测试")
@allure.tag("local", "smoke")
def test_exam_core_api_smoke(exam_client):
    """
    登录后对 5 个核心列表接口进行冒烟测试
    - HTTP 状态码
    - 业务状态码
    - 分页结构
    - 核心业务字段
    """
    allure.attach(
        "本次测试覆盖：考试列表、试卷列表、规则列表、题库列表、试题列表",
        name="测试范围",
        attachment_type=allure.attachment_type.TEXT
    )

    # ---------- 1. 考试列表 ----------
    with allure.step("查询考试列表"):
        resp = exam_client.post(
            "/exam/api/exam/exam/paging",
            json=build_payload({"name": ""})
        )

        data = assert_api_response(resp)
        records, _ = assert_pagination_structure(data)

        allure.attach(
            f"📊 记录数: {len(records)}",
            name="结果摘要",
            attachment_type=allure.attachment_type.TEXT
        )

    # ---------- 2. 试卷列表（考试记录） ----------
    with allure.step("查询试卷列表"):
        resp = exam_client.post(
            "/exam/api/paper/paper/paging",
            json=build_payload({"title": ""})
        )

        data = assert_api_response(resp)
        records, _ = assert_pagination_structure(data)

        if len(records) > 0:
            assert_exam_record_business(records)

        allure.attach(
            f"📊 记录数: {len(records)}",
            name="结果摘要",
            attachment_type=allure.attachment_type.TEXT
        )

    # ---------- 3. 规则列表 ----------
    with allure.step("查询试卷规则"):
        resp = exam_client.post(
            "/exam/api/paper/rule/paging",
            json=build_payload({"title": ""})
        )

        data = assert_api_response(resp)
        records, _ = assert_pagination_structure(data)

        allure.attach(
            f"📊 记录数: {len(records)}",
            name="结果摘要",
            attachment_type=allure.attachment_type.TEXT
        )

    # ---------- 4. 题库列表 ----------
    with allure.step("查询题库列表"):
        resp = exam_client.post(
            "/exam/api/qu/repo/paging",
            json=build_payload({"title": ""})
        )

        data = assert_api_response(resp)
        records, _ = assert_pagination_structure(data)

        allure.attach(
            f"📊 记录数: {len(records)}",
            name="结果摘要",
            attachment_type=allure.attachment_type.TEXT
        )

    # ---------- 5. 试题列表 ----------
    with allure.step("查询试题列表"):
        resp = exam_client.post(
            "/exam/api/qu/qu/paging",
            json=build_payload({
                "content": "",
                "quType": "",
                "repoIds": []
            })
        )

        data = assert_api_response(resp)
        records, _ = assert_pagination_structure(data)

        if len(records) > 0:
            assert_question_business(records)

        allure.attach(
            f"📊 记录数: {len(records)}",
            name="结果摘要",
            attachment_type=allure.attachment_type.TEXT
        )

    # ---------- 最终结果 ----------
    allure.attach(
        "✅ 核心接口冒烟测试通过",
        name="执行结果",
        attachment_type=allure.attachment_type.TEXT
    )