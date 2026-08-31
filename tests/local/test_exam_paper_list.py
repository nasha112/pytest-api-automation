import pytest
import requests
import allure
import json
import time

@allure.feature("本地Exam系统 - 试卷列表")
@allure.story("查看可参加的考试")
@allure.tag("local", "smoke")
def test_admin_login_and_get_exam_list(base_url):
    # 登录
    login_url = f"{base_url}/exam/api/sys/user/login"
    login_resp = requests.post(login_url, json={"username": "admin", "password": "123456"})
    assert login_resp.status_code == 200
    token = login_resp.json().get("data", {}).get("token") or login_resp.json().get("token")
    assert token

    session = requests.Session()
    session.headers.update({"Token": token})
    session.cookies.set("Admin-Token", token)

    # 查询试卷列表（可参加的考试）
    list_url = f"{base_url}/exam/api/exam/exam/paging"
    payload = {
        "current": 1,
        "size": 10,
        "params": {"name": ""},
        "t": int(time.time() * 1000)
    }

    with allure.step("查询可参加的考试列表"):
        resp = session.post(list_url, json=payload)
        allure.attach(json.dumps(resp.json(), indent=2), name="Response")
        assert resp.status_code == 200

        records = resp.json().get("data", {}).get("records", [])
        assert len(records) > 0, "试卷列表为空"

        titles = [r.get("title") for r in records]
        # 验证列表中存在“新人入职智力测试题”（来源于你的初始数据）
        assert "新人入职智力测试题" in str(titles)