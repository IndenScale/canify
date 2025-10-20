"""
测试用的 fixture 模块
"""

from src.canify.decorators import fixture


@fixture
def get_budget_data():
    """获取预算数据"""
    return {
        "project_name": "测试项目",
        "total_budget": 100000,
        "allocated_budget": 80000,
        "remaining_budget": 20000
    }


@fixture
def get_owner_data():
    """获取负责人数据"""
    return {
        "owner_name": "张三",
        "owner_level": "高级经理",
        "department": "技术部"
    }


@fixture
def get_security_data():
    """获取安全数据"""
    return {
        "has_encryption": True,
        "has_backup": True,
        "compliance_level": "high"
    }