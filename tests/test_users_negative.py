import pytest
import allure
from jsonschema import validate
from libraries.request_client import RequestClient

# Schemas
error_schema_object = {
    "type": "object",
    "properties": {
        "message": {"type": "string"}
    },
    "required": ["message"]
}

error_schema_array = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "field": {"type": "string"},
            "message": {"type": "string"}
        },
        "required": ["message"]
    }
}


@allure.feature("User Management")
@allure.story("Negative Scenarios")
@pytest.mark.negative
def test_create_user_invalid_token(base_url, end_point):
    """
    验证无效 Token 返回 401
    注意：这个用例不能用 public_client（因为 public_client 带的是正确 Token）
    我们新建一个临时 client，只带错误的 Token
    """
    data = {"name": "invalid_user", "email": "invalid@user.com", "gender": "male", "status": "active"}
    bad_headers = {"Authorization": "Bearer invalidtoken123"}

    # 🆕 新建一个带错误 Token 的临时 client
    bad_client = RequestClient(base_url, headers=bad_headers)

    post_response = bad_client.post(end_point, json=data, timeout=10)
    response_json = post_response.json()

    allure.attach(str(response_json), name="Invalid Token Response", attachment_type=allure.attachment_type.JSON)

    assert post_response.status_code == 401
    validate(instance=response_json, schema=error_schema_object)


@allure.feature("User Management")
@allure.story("Negative Scenarios")
@pytest.mark.negative
def test_create_user_missing_fields(public_client, end_point):
    """验证缺少必填字段返回 422"""
    data = {"name": "missing_fields_user"}  # 缺少 email, gender, status

    post_response = public_client.post(end_point, json=data, timeout=10)
    response_json = post_response.json()

    allure.attach(str(response_json), name="Missing Fields Response", attachment_type=allure.attachment_type.JSON)

    assert post_response.status_code == 422
    validate(instance=response_json, schema=error_schema_array)


@allure.feature("User Management")
@allure.story("Negative Scenarios")
@pytest.mark.negative
def test_create_user_duplicate_email(public_client, end_point):
    """验证重复邮箱返回 422"""
    email = "duplicate@user.com"
    data = {"name": "first_user", "email": email, "gender": "male", "status": "active"}

    # 创建第一个用户
    public_client.post(end_point, json=data, timeout=10)

    # 重复创建相同邮箱的用户
    dup_response = public_client.post(end_point, json=data, timeout=10)
    response_json = dup_response.json()

    allure.attach(str(response_json), name="Duplicate Email Response", attachment_type=allure.attachment_type.JSON)

    assert dup_response.status_code == 422
    validate(instance=response_json, schema=error_schema_array)