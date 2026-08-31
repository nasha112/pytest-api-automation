"""
conftest.py - Pytest 全局配置
职责：
1. 注册命令行参数 --env（public / local）
2. 根据环境提供 base_url
3. 为公网环境提供 auth_token fixture
4. 为本地 Exam 环境提供 exam_session fixture（自动登录复用 Token）
5. 日志配置
"""
import pytest
import requests
import logging
import os


# ======================== 日志配置 ========================
@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename="logs/test.log",
        filemode="w",
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO
    )
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.info("✅ Logging initialized")


# ======================== 环境切换 ========================
def pytest_addoption(parser):
    """添加 --env 命令行参数"""
    parser.addoption(
        "--env",
        action="store",
        default="public",
        choices=["public", "local"],
        help="选择测试环境: public (公网 GoRest) / local (本地 Exam)"
    )


@pytest.fixture(scope="session")
def env(request):
    """返回当前环境名称"""
    return request.config.getoption("--env")


@pytest.fixture(scope="session")
def base_url(env):
    """根据环境返回 base_url（从 pytest.ini 的 env 中读取）"""
    if env == "public":
        return os.getenv("BASE_URL", "https://gorest.co.in")
    else:
        return os.getenv("BASE_URL_LOCAL", "http://localhost:8101")


# ======================== 公网环境（GoRest）认证 ========================
@pytest.fixture(scope="session")
def auth_token(env):
    """公网环境返回 Token，本地环境返回 None"""
    if env == "public":
        token = os.getenv("AUTH_TOKEN")
        if not token:
            raise ValueError("公网环境必须设置 AUTH_TOKEN（在 pytest.ini 的 env 中）")
        return token
    return None


@pytest.fixture(scope="session")
def public_headers(auth_token, env):
    """公网环境专用请求头"""
    if env == "public":
        return {"Authorization": auth_token}
    return {}


# ======================== 本地环境（Exam 系统）认证 ========================
@pytest.fixture(scope="session")
def exam_token(base_url):
    """
    本地 Exam 系统登录，获取 Token
    scope=session 表示整个测试会话只登录一次，所有测试复用
    """
    login_url = f"{base_url}/exam/api/sys/user/login"
    login_data = {"username": "admin", "password": "123456"}

    response = requests.post(login_url, json=login_data, timeout=5)
    assert response.status_code == 200, f"登录失败: {response.text}"

    data = response.json()
    # 适配多种可能的返回格式
    token = (
        data.get("data", {}).get("token")
        or data.get("data", {}).get("accessToken")
        or data.get("token")
        or data.get("accessToken")
    )
    assert token, f"响应中未提取到 Token: {data}"

    return token


# @pytest.fixture(scope="session")
# def exam_session(base_url, exam_token):
#     """
#     本地 Exam 系统专用 Session
#     自动携带 Token（Header + Cookie），所有测试共用
#     """
#     session = requests.Session()
#     session.headers.update({"Token": exam_token})
#     session.cookies.set("Admin-Token", exam_token)
#     return session


# ======================== RequestClient 实例 ========================
from libraries.request_client import RequestClient


@pytest.fixture(scope="session")
def public_client(base_url, public_headers):
    """公网环境 RequestClient"""
    return RequestClient(base_url, headers=public_headers)


@pytest.fixture(scope="session")
def exam_client(base_url, exam_token):
    """本地 Exam 环境 RequestClient（自动带 Token）"""
    headers = {"Token": exam_token}
    client = RequestClient(base_url, headers=headers)
    client.set_cookie("Admin-Token", exam_token)
    return client


# ======================== 保留原有 fixture（兼容旧代码） ========================
# 如果 test_users.py 还依赖 headers、end_point 等，保留它们
@pytest.fixture(scope="session")
def headers(public_headers):
    """兼容旧 test_users.py 的 headers fixture"""
    return public_headers


@pytest.fixture(scope="session")
def end_point():
    """公网用户管理接口端点"""
    return "/public/v2/users/"