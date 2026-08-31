import pytest
import requests
import allure
import json
import time

@allure.feature("本地Exam系统 - 考试记录")
@allure.story("查询已参加的考试记录")
@allure.tag("local", "smoke")
def test_admin_login_and_get_paper_records(base_url):
    # 登录
    login_url = f"{base_url}/exam/api/sys/user/login"
    login_resp = requests.post(login_url, json={"username": "admin", "password": "123456"})
    assert login_resp.status_code == 200
    token = login_resp.json().get("data", {}).get("token") or login_resp.json().get("token")
    assert token

    session = requests.Session()
    session.headers.update({"Token": token})
    session.cookies.set("Admin-Token", token)

    # 查询考试记录（已参加的试卷）
    list_url = f"{base_url}/exam/api/paper/paper/paging"
    payload = {
        "current": 1,
        "size": 10,
        "params": {"title": ""},
        "t": int(time.time() * 1000)
    }

    with allure.step("查询已参加的考试记录"):
        resp = session.post(list_url, json=payload)
        allure.attach(json.dumps(resp.json(), indent=2), name="Response")
        assert resp.status_code == 200

        records = resp.json().get("data", {}).get("records", [])
        assert len(records) > 0, "考试记录为空"

        titles = [r.get("title") for r in records]
        # 验证存在“计算机”试卷（来源于你的初始数据）
        assert "计算机" in str(titles)