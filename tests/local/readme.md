这个是针对本地考试管理系统写的考试用例
执行业务串联用例
## pytest -v --env=local tests/local/test_exam_flow.py

执行各功能用例
##  pytest -v --env=local tests/local/ -k "not flow"   

allure可视化报告
## allure serve reports/allure-results  