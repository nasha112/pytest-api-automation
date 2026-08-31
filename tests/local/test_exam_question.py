import pytest
import requests
import allure
import json
import time

@allure.feature("本地Exam系统 - 试题管理")
@allure.story("登录后查询试题列表")
@allure.tag("local", "smoke")
def test_admin_login_and_get_question_list(base_url):
    login_url = f"{base_url}/exam/api/sys/user/login"
    login_resp = requests.post(login_url, json={"username": "admin", "password": "123456"})
    assert login_resp.status_code == 200
    token = login_resp.json().get("data", {}).get("token") or login_resp.json().get("token")
    assert token

    session = requests.Session()
    session.headers.update({"Token": token})
    session.cookies.set("Admin-Token", token)

    # 试题分页接口（你的代码中的路径）
    list_url = f"{base_url}/exam/api/qu/qu/paging"
    payload = {
        "current": 1,
        "size": 10,
        "params": {
            "content": "",
            "quType": "",
            "repoIds": []
        },
        "t": int(time.time() * 1000)
    }
    with allure.step("查询试题列表"):
        resp = session.post(list_url, json=payload)
        allure.attach(json.dumps(resp.json(), indent=2), name="Response")
        assert resp.status_code == 200
        records = resp.json().get("data", {}).get("records", [])
        assert len(records) > 0, "试题列表为空"
        contents = " ".join([r.get("content", "") for r in records])
        assert "五个答案" in contents or "冯·诺伊曼" in contents