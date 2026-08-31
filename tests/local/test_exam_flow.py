import pytest
import requests
import allure
import json
import time

@allure.feature("本地Exam系统 - 完整业务链路")
@allure.story("登录后依次查询所有核心列表")
@allure.tag("local", "smoke")
def test_full_business_flow(base_url):
    # ---------- 1. 登录 ----------
    with allure.step("登录获取Token"):
        login_resp = requests.post(
            f"{base_url}/exam/api/sys/user/login",
            json={"username": "admin", "password": "123456"}
        )
        assert login_resp.status_code == 200
        token = login_resp.json().get("data", {}).get("token") or login_resp.json().get("token")
        assert token
        allure.attach(f"Token: {token}", name="认证凭证")

    session = requests.Session()
    session.headers.update({"Token": token})
    session.cookies.set("Admin-Token", token)

    # ---------- 2. 查询考试列表 ----------
    with allure.step("查询考试列表"):
        resp = session.post(
            f"{base_url}/exam/api/exam/exam/paging",
            json={"current": 1, "size": 10, "params": {"name": ""}, "t": int(time.time()*1000)}
        )
        assert resp.status_code == 200
        records = resp.json().get("data", {}).get("records", [])
        assert len(records) > 0
        allure.attach(f"考试记录数: {len(records)}", name="考试列表统计")

    # ---------- 3. 查询考试记录（试卷） ----------
    with allure.step("查询考试记录（试卷列表）"):
        resp = session.post(
            f"{base_url}/exam/api/paper/paper/paging",
            json={"current": 1, "size": 10, "params": {"title": ""}, "t": int(time.time()*1000)}
        )
        assert resp.status_code == 200
        records = resp.json().get("data", {}).get("records", [])
        assert len(records) > 0
        allure.attach(f"试卷记录数: {len(records)}", name="试卷列表统计")

    # ---------- 4. 查询规则列表 ----------
    with allure.step("查询试卷规则列表"):
        resp = session.post(
            f"{base_url}/exam/api/paper/rule/paging",
            json={"current": 1, "size": 10, "params": {"title": ""}, "t": int(time.time()*1000)}
        )
        assert resp.status_code == 200
        records = resp.json().get("data", {}).get("records", [])
        assert len(records) > 0
        allure.attach(f"规则记录数: {len(records)}", name="规则列表统计")

    # ---------- 5. 查询题库列表（使用你的代码路径 /exam/api/qu/repo/paging）----------
    with allure.step("查询题库列表"):
        resp = session.post(
            f"{base_url}/exam/api/qu/repo/paging",
            json={"current": 1, "size": 10, "params": {"title": ""}, "t": int(time.time()*1000)}
        )
        assert resp.status_code == 200
        records = resp.json().get("data", {}).get("records", [])
        assert len(records) > 0
        allure.attach(f"题库记录数: {len(records)}", name="题库列表统计")

    # ---------- 6. 查询试题列表（使用你的代码路径 /exam/api/qu/qu/paging）----------
    with allure.step("查询试题列表"):
        resp = session.post(
            f"{base_url}/exam/api/qu/qu/paging",
            json={
                "current": 1,
                "size": 10,
                "params": {"content": "", "quType": "", "repoIds": []},
                "t": int(time.time()*1000)
            }
        )
        assert resp.status_code == 200
        records = resp.json().get("data", {}).get("records", [])
        assert len(records) > 0
        allure.attach(f"试题记录数: {len(records)}", name="试题列表统计")

    # 最终成功
    allure.attach("✅ 所有核心模块查询成功，业务链路完整！", name="最终结果")