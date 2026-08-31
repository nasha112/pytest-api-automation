import pytest
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
def test_can_create_user(public_client, end_point, name, email, gender, status):
    """
    使用 public_client（已自动携带 Authorization Header）
    测试代码不再拼接 URL，不再关心 requests 细节
    """
    allure.dynamic.title(f"Create user → {name}")
    allure.dynamic.description_html(f"""
    <b>Test Objective:</b> Verify that a user can be created, retrieved, and deleted.<br>
    <b>Parameters:</b> {name}, {email}, {gender}, {status}
    """)

    data = {"name": name, "email": email, "gender": gender, "status": status}

    # ---------- 1. Create User ----------
    with allure.step("➡️ Create User (POST)"):
        # 🆕 使用 public_client.post()，路径自动拼接 base_url
        post_response = public_client.post(end_point, json=data, timeout=10)
        response_json = post_response.json()

        allure.attach(str(response_json), name="POST Response", attachment_type=allure.attachment_type.JSON)

        assert post_response.status_code == 201, f"❌ POST failed: {post_response.text}"
        user_id = response_json["id"]

        # ✅ Schema validation
        validate(instance=response_json, schema=success_schema)

    # ---------- 2. Get User ----------
    with allure.step("➡️ Get User (GET)"):
        # 🆕 路径直接拼接 user_id
        get_response = public_client.get(f"{end_point}{user_id}", timeout=10)
        response_json = get_response.json()

        allure.attach(str(response_json), name="GET Response", attachment_type=allure.attachment_type.JSON)

        assert get_response.status_code == 200, f"❌ GET failed: {get_response.text}"
        validate(instance=response_json, schema=success_schema)

    # ---------- 3. Delete User ----------
    with allure.step("➡️ Delete User (DELETE)"):
        delete_response = public_client.delete(f"{end_point}{user_id}", timeout=10)

        allure.attach(str(delete_response.text), name="DELETE Response", attachment_type=allure.attachment_type.TEXT)

        assert delete_response.status_code == 204, f"❌ DELETE failed: {delete_response.text}"