import requests
import logging

logger = logging.getLogger(__name__)

class RequestClient:

    def __init__(self, base_url, headers=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

        if headers:
            self.session.headers.update(headers)

    def build_url(self,path: str) ->str:
        """
               拼接完整 URL
               如果 path 以 http 开头，则直接返回（支持绝对路径）
               否则拼接 base_url + path
        """
        if path.startswith("http"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def get(self, path, **kwargs):
        return self.session.get(
            self.build_url(path),
            **kwargs
        )

    def post(self, path, **kwargs):
        url = self.build_url(path)

        logger.info(f"POST {url}")
        logger.info(f"Request data: {kwargs.get('json')}")

        response = self.session.post(
            url,
            **kwargs
        )

        logger.info(f"Response status: {response.status_code}")

        return response

    def put(self, path, **kwargs):
        return self.session.put(
            self.build_url(path),
            **kwargs
        )

    def delete(self, path, **kwargs):
        return self.session.delete(
            self.build_url(path),
            **kwargs
        )

    def set_header(self, key: str, value: str):
        """动态设置请求头"""
        self.session.headers[key] = value

    def set_cookie(self, key: str, value: str):
        """动态设置 Cookie"""
        self.session.cookies.set(key, value)