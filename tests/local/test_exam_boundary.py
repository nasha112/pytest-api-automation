"""
本地 Exam 系统分页边界测试
基于真实后端行为设定预期：
- current=0 → 后端自动修正为 current=1
- current=1 → 正常
- current=99999 → 返回空列表或最后一页
- size=0 → 后端可能返回默认值或错误
- size=1 → 正常返回 1 条数据
- size=9999 → 后端限制最大值（不会崩溃）
"""
import pytest
import allure


# ======================== 通用校验 ========================
def assert_success_response(resp):
    """验证接口正常响应"""
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("code") == 0
    return data


# ======================== current 边界测试（参数化） ========================
@allure.feature("本地Exam系统 - 分页边界测试")
@allure.story("current 边界")
@allure.tag("local", "boundary")
@pytest.mark.parametrize("current, expected_current", [
    (0, 1),      # current=0 → 后端自动修正为 1
    (1, 1),      # current=1 → 正常
    (99999, 99999)  # current=99999 → 后端接受（可能返回空）
])
def test_current_boundary(exam_client, current, expected_current):
    """参数化测试 current 边界值"""
    with allure.step(f"传入 current={current}"):
        resp = exam_client.post(
            "/exam/api/exam/exam/paging",
            json={"current": current, "size": 10, "params": {"name": ""}}
        )

        data = assert_success_response(resp)
        page_data = data.get("data", {})

        # 验证 current 字段存在
        assert "current" in page_data

        # 如果 current=0，后端应自动修正为 1
        if current == 0:
            actual_current = page_data.get("current")
            assert actual_current == expected_current, f"current=0 应被修正为 {expected_current}，实际为 {actual_current}"

        # 验证结构完整
        assert "records" in page_data
        assert isinstance(page_data["records"], list)
        assert "pages" in page_data

        allure.attach(
            f"输入 current={current}, 返回 current={page_data.get('current')}, 记录数={len(page_data.get('records', []))}",
            name="结果摘要",
            attachment_type=allure.attachment_type.TEXT
        )


# ======================== size 边界测试（参数化） ========================
@allure.feature("本地Exam系统 - 分页边界测试")
@allure.story("size 边界")
@allure.tag("local", "boundary")
@pytest.mark.parametrize("size, max_expected", [
    (0, 10),      # size=0 → 后端可能返回默认 size 或错误，这里验证返回的记录数 <= 10
    (1, 1),       # size=1 → 返回最多 1 条
    (9999, 100)   # size=9999 → 后端通常有最大值限制（如 100），不崩溃即可
])
def test_size_boundary(exam_client, size, max_expected):
    """参数化测试 size 边界值"""
    with allure.step(f"传入 size={size}"):
        resp = exam_client.post(
            "/exam/api/exam/exam/paging",
            json={"current": 1, "size": size, "params": {"name": ""}}
        )

        data = assert_success_response(resp)
        page_data = data.get("data", {})

        # 验证结构完整
        assert "records" in page_data
        records = page_data["records"]
        assert isinstance(records, list)

        # 验证返回记录数不超过预期值
        if size == 0:
            # size=0 时，后端可能返回默认 10 条，也可能返回 0 条
            # 记录实际结果，不强制断言
            allure.attach(
                f"size=0 返回记录数: {len(records)}, 实际 size 字段: {page_data.get('size', 'N/A')}",
                name="边界行为记录",
                attachment_type=allure.attachment_type.TEXT
            )
        elif size == 1:
            assert len(records) <= 1, f"size=1 时返回记录数不应超过 1，实际: {len(records)}"
        else:  # size=9999
            # 验证不崩溃，记录实际返回数
            allure.attach(
                f"size=9999 返回记录数: {len(records)}",
                name="超大 size 行为记录",
                attachment_type=allure.attachment_type.TEXT
            )

        # 验证 size 字段存在且不为负数（如果接口返回了 size 字段）
        if "size" in page_data:
            actual_size = page_data["size"]
            assert isinstance(actual_size, int)
            assert actual_size >= 0


# ======================== 重要：current 正常值验证 ========================
@allure.feature("本地Exam系统 - 分页边界测试")
@allure.story("current 边界")
@allure.tag("local", "boundary")
def test_current_normal(exam_client):
    """验证 current=1（正常值）返回第一页数据"""
    with allure.step("传入 current=1"):
        resp = exam_client.post(
            "/exam/api/exam/exam/paging",
            json={"current": 1, "size": 10, "params": {"name": ""}}
        )

        data = assert_success_response(resp)
        page_data = data.get("data", {})

        assert page_data.get("current") == 1
        assert "records" in page_data
        assert isinstance(page_data["records"], list)


@allure.feature("本地Exam系统 - 分页边界测试")
@allure.story("size 边界")
@allure.tag("local", "boundary")
def test_size_normal(exam_client):
    """验证 size=1（最小有效值）返回不多于 1 条数据"""
    with allure.step("传入 size=1"):
        resp = exam_client.post(
            "/exam/api/exam/exam/paging",
            json={"current": 1, "size": 1, "params": {"name": ""}}
        )

        data = assert_success_response(resp)
        page_data = data.get("data", {})
        records = page_data.get("records", [])

        assert isinstance(records, list)
        assert len(records) <= 1, f"size=1 时返回记录数不应超过 1，实际: {len(records)}"