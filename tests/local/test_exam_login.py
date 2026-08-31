import pytest
import requests
import allure
import json

@allure.feature("本地Exam系统")
@allure.story("用户认证")
@allure.tag("local")
def test_exam_admin_login(base_url):
    """
    验证本地考试系统的管理员登录功能。
    对应后端接口：POST /exam/api/sys/user/login
    """
    # 登录数据（从 sys_log 表可知 admin/123456 是有效的）
    login_data = {
        "username": "admin",
        "password": "123456"
    }

    with allure.step("发送登录请求"):
        # 注意：根据截图，完整 URL 是 base_url + /exam/api/sys/user/login
        login_url = f"{base_url}/exam/api/sys/user/login"
        response = requests.post(login_url, json=login_data, timeout=5)
        
        # 附加响应到 Allure
        allure.attach(
            json.dumps(response.json(), indent=2, ensure_ascii=False),
            name="Login Response",
            attachment_type=allure.attachment_type.JSON
        )

    with allure.step("验证登录成功"):
        assert response.status_code == 200, f"登录失败，状态码：{response.status_code}"
        resp_data = response.json()
        # 根据你的实际响应结构调整断言
        # 常见响应可能包含 code、msg、data 等字段，我们假设成功时 code=0 或有 token
        # 由于没看到具体响应，先做基础断言：存在 'token' 或 'user' 字段
        # 如果你知道响应格式，可以改得更精确
        assert "token" in resp_data or "user" in resp_data or "code" in resp_data, \
            "登录响应未包含预期字段"
        # 如果返回了 token，可以打印或保存供后续用例使用（可选）
        if "token" in resp_data:
            allure.attach(f"Token: {resp_data['token']}", name="Extracted Token")