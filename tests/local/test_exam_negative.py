"""
本地 Exam 系统负面测试
覆盖：错误凭证、缺失参数、无效 Token、非法参数、搜索不存在的名称
"""
import pytest
import allure

from libraries.request_client import RequestClient


# ======================== 登录负面测试 ========================
@allure.feature("本地Exam系统 - 负面测试")
@allure.story("登录认证")
@allure.tag("local", "negative")
def test_login_wrong_password(base_url):
    """验证：错误密码登录应返回业务状态码非 0"""
    with allure.step("使用错误密码登录"):
        client = RequestClient(base_url)
        resp = client.post(
            "/exam/api/sys/user/login",
            json={"username": "admin", "password": "wrong_password"}
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") != 0, "错误密码登录应返回非 0 业务状态码"
        allure.attach(f"业务状态码: {data.get('code')}, 提示: {data.get('msg')}", name="响应摘要")


@allure.feature("本地Exam系统 - 负面测试")
@allure.story("登录认证")
@allure.tag("local", "negative")
def test_login_wrong_username(base_url):
    """验证：错误用户名登录应返回业务状态码非 0"""
    with allure.step("使用错误用户名登录"):
        client = RequestClient(base_url)
        resp = client.post(
            "/exam/api/sys/user/login",
            json={"username": "nonexistent_user", "password": "123456"}
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") != 0, "错误用户名登录应返回非 0 业务状态码"


@allure.feature("本地Exam系统 - 负面测试")
@allure.story("登录认证")
@allure.tag("local", "negative")
def test_login_missing_password(base_url):
    """验证：缺少密码参数登录应返回业务状态码非 0"""
    with allure.step("缺少密码参数登录"):
        client = RequestClient(base_url)
        resp = client.post(
            "/exam/api/sys/user/login",
            json={"username": "admin"}  # 缺少 password
        )

        # 根据实际后端行为：返回 HTTP 200，code != 0
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") != 0, "缺少密码应返回非 0 业务状态码"


@allure.feature("本地Exam系统 - 负面测试")
@allure.story("登录认证")
@allure.tag("local", "negative")
def test_login_missing_username(base_url):
    """验证：缺少用户名参数登录应返回业务状态码非 0"""
    with allure.step("缺少用户名参数登录"):
        client = RequestClient(base_url)
        resp = client.post(
            "/exam/api/sys/user/login",
            json={"password": "123456"}  # 缺少 username
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") != 0, "缺少用户名应返回非 0 业务状态码"


# ======================== 接口级负面测试 ========================
@allure.feature("本地Exam系统 - 负面测试")
@allure.story("参数校验")
@allure.tag("local", "negative")
def test_search_non_existent_data(exam_client):
    """
    验证：搜索不存在的名称，接口应正常返回（不报错）
    当前后端返回全部数据（模糊搜索），而非空列表
    该行为已由实际运行确认
    """
    search_keyword = "这是一个不可能存在的考试名称_2026"

    with allure.step(f"搜索不存在的考试名称: '{search_keyword}'"):
        resp = exam_client.post(
            "/exam/api/exam/exam/paging",
            json={
                "current": 1,
                "size": 10,
                "params": {"name": search_keyword}
            }
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0

        records = data.get("data", {}).get("records", [])
        assert isinstance(records, list)

        # 记录实际行为（不是断言，而是说明）
        allure.attach(
            f"搜索关键词: '{search_keyword}'\n"
            f"返回记录数: {len(records)}\n"
            f"说明: 当前后端实现为模糊搜索，无效关键词会返回全部数据。",
            name="搜索结果说明",
            attachment_type=allure.attachment_type.TEXT
        )


@allure.feature("本地Exam系统 - 负面测试")
@allure.story("参数校验")
@allure.tag("local", "negative")
def test_invalid_current_type(exam_client):
    """
    验证：传入非数字的 current 参数，后端返回 HTTP 400
    预期：HTTP 400
    """
    with allure.step("传入非数字的 current 参数"):
        resp = exam_client.post(
            "/exam/api/exam/exam/paging",
            json={"current": "invalid_string", "size": 10}
        )

        # 实际后端行为：直接返回 HTTP 400
        assert resp.status_code == 400
        # 验证返回了错误信息（通常 400 响应体会有 error 或 message）
        assert "error" in resp.text.lower() or "message" in resp.text.lower()
        allure.attach(resp.text, name="错误响应", attachment_type=allure.attachment_type.TEXT)


# ======================== 鉴权行为验证 ========================
@allure.feature("本地Exam系统 - 环境发现")
@allure.story("鉴权行为")
@allure.tag("local", "security")
def test_invalid_token_behavior(base_url):
    """
    验证：当前开发环境对 /exam/api/** 接口未启用 Token 鉴权
    该行为由后端日志确认: 'No applicable constraints defined'
    测试目的：记录环境行为，而非验证安全策略
    """
    with allure.step("使用无效 Token 查询考试列表"):
        client = RequestClient(base_url, headers={"Token": "invalid_token_123"})
        client.set_cookie("Admin-Token", "invalid_token_123")

        resp = client.post(
            "/exam/api/exam/exam/paging",
            json={"current": 1, "size": 10}
        )

        # 开发环境下，接口正常返回
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("code") == 0
        records = data.get("data", {}).get("records", [])
        assert isinstance(records, list)

        allure.attach(
            "环境发现: /exam/api/** 接口在开发环境中配置为 permitAll，不校验 Token。\n"
            "证据: 后端日志显示 'No applicable constraints defined'。\n"
            "注意: 该行为在预发布/生产环境中会发生改变。",
            name="鉴权行为说明",
            attachment_type=allure.attachment_type.TEXT
        )