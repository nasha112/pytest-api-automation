import pytest
import requests
from jsonschema import validate
from libraries.util import read_excel_data, load_schema
import logging
import allure

logger = logging.getLogger(__name__)

# ✅ Load success schema
success_schema = load_schema("success_user_schema.json")

# Safe Excel load
try:
    user_data = read_excel_data("tests/user_data.xlsx")
except Exception as e:
    logger.error(f"❌ Failed to load Excel data: {e}")
    user_data = [("dummy", "dummy@example.com", "male", "active")]  # fallback


@allure.feature("User Management")
@allure.story("Create User")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("positive")
@pytest.mark.parametrize("name,email,gender,status", user_data)
def test_can_create_user(base_url, headers, end_point, name, email, gender, status,db_client):
    allure.dynamic.title(f"Create user → {name}")
    allure.dynamic.description_html(f"""
    <b>Test Objective:</b> Verify that a user can be created, retrieved, and deleted.<br>
    <b>Parameters:</b> {name}, {email}, {gender}, {status}
    """)

    data = {"name": name, "email": email, "gender": gender, "status": status}

    with allure.step("➡️ Create User (POST)"):
        post_response = requests.post(base_url + end_point, headers=headers, json=data, timeout=10)
        response_json = post_response.json()

        allure.attach(str(response_json), name="POST Response", attachment_type=allure.attachment_type.JSON)

        assert post_response.status_code == 201, f"❌ POST failed: {post_response.text}"
        user_id = response_json["id"]

        # ✅ Schema validation
        validate(instance=response_json, schema=success_schema)

    with allure.step("➡️ Get User (GET)"):
        get_response = requests.get(f"{base_url}{end_point}{user_id}", headers=headers, timeout=10)
        response_json = get_response.json()

        allure.attach(str(response_json), name="GET Response", attachment_type=allure.attachment_type.JSON)

        assert get_response.status_code == 200, f"❌ GET failed: {get_response.text}"
        validate(instance=response_json, schema=success_schema)

    with allure.step("➡️ Delete User (DELETE)"):
        delete_response = requests.delete(f"{base_url}{end_point}{user_id}", headers=headers, timeout=10)

        allure.attach(str(delete_response.text), name="DELETE Response", attachment_type=allure.attachment_type.TEXT)

        assert delete_response.status_code == 204, f"❌ DELETE failed: {delete_response.text}"

    # 只有在 db_client 不为 None 时才执行数据库校验
    if db_client is not None:
        with allure.step("✅ 校验数据库落库（直连MySQL）"):
            sql = "SELECT id, name, email, gender, status FROM users WHERE email = %s"
            db_result = db_client.fetch_one(sql, (email,))
            assert db_result is not None, f"❌ 数据库中找不到邮箱为 {email} 的用户！"

             # 断言数据库里的关键字段和请求一致
            assert db_result["name"] == name, f"数据库name({db_result['name']})与请求({name})不一致！"
            assert db_result["email"] == email
            assert db_result["gender"] == gender
            assert db_result["status"] == status

            allure.attach(str(db_result), name="DB Query Result", attachment_type=allure.attachment_type.JSON)
            logger.info(f"✅ 数据库校验通过: {db_result}")
            db_client.close()
    else:
        allure.attach("公网环境，跳过数据库校验", name="DB Check Skipped")