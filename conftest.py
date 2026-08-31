import pytest
import logging
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# ------------------ 日志配置（保留原有） ------------------
os.makedirs("logs", exist_ok=True)

@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    logging.basicConfig(
        filename="logs/test.log",
        filemode="w",
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO
    )
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.info("✅ Logging initialized")

@pytest.fixture(scope="session")
def logger():
    return logging.getLogger("pytest_api_framework")

# ------------------ 多环境支持 ------------------
def pytest_addoption(parser):
    """添加命令行参数 --env，用于切换测试环境"""
    parser.addoption(
        "--env",
        action="store",
        default="public",   # 默认公网
        choices=["public", "local"],
        help="选择测试环境: public (公网GoRest) 或 local (本地Exam系统)"
    )

@pytest.fixture(scope="session")
def env(request):
    """返回当前环境名称"""
    return request.config.getoption("--env")

@pytest.fixture(scope="session")
def base_url(env):
    """根据 --env 参数返回对应的 BASE_URL"""
    if env == "public":
        # 从 pytest.ini 的 env 中读取（就是你原先的 BASE_URL）
        return os.getenv("BASE_URL", "https://gorest.co.in")
    else:  # local
        # 从 pytest.ini 的 env 中读取本地地址
        return os.getenv("BASE_URL_LOCAL", "http://localhost:8101")

@pytest.fixture(scope="session")
def auth_token(env):
    """根据环境返回 Token（公网用，本地可留空）"""
    if env == "public":
        # 从 pytest.ini 的 env 中读取你的真实 Token
        return os.getenv("AUTH_TOKEN")
    else:
        # 本地环境可能不需要 Token，或者登录后动态获取
        return ""

@pytest.fixture(scope="session")
def headers(env, auth_token):
    """返回请求头（公网带 Authorization，本地可能为空或后续动态设置）"""
    if env == "public":
        return {"Authorization": auth_token}
    else:
        # 本地系统可能不需要 Authorization 头，或者需要特殊的 token
        # 如果本地需要，可以从环境变量读取
        local_token = os.getenv("LOCAL_AUTH_TOKEN", "")
        if local_token:
            return {"Authorization": f"Bearer {local_token}"}
        return {}   # 空头，登录测试会单独处理

# ------------------ 原有 fixture（保持不变） ------------------
@pytest.fixture(scope="session")
def end_point():
    """仅用于公网用户 CRUD 测试的端点"""
    return "/public/v2/users/"

@pytest.fixture(scope="function")
def db_client(env):
    """仅当环境为 local 时才提供数据库连接，否则返回 None"""
    if env != "local":
        return None   # 公网环境直接返回 None，测试函数需要判断
    # 如果 env == "local"，则建立数据库连接（需要你之前写的 DBClient）
    # 这里假设你已经实现了 libraries.db_util.DBClient
    try:
        from libraries.db_util import DBClient
        return DBClient()
    except ImportError:
        pytest.skip("数据库模块未安装，跳过数据库校验")