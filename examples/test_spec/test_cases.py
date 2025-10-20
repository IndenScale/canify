"""
测试用的 test_case 模块
"""

from src.canify.decorators import test_case


@test_case
def validate_budget_allocation(data):
    """验证预算分配"""
    # 简单的验证逻辑
    total_budget = data.get("total_budget", 0)
    allocated_budget = data.get("allocated_budget", 0)

    if allocated_budget > total_budget:
        return False

    return True


@test_case
def validate_owner_level(data):
    """验证负责人级别"""
    owner_level = data.get("owner_level", "")

    # 允许的负责人级别
    allowed_levels = ["高级经理", "总监", "副总裁"]

    return owner_level in allowed_levels


@test_case
def validate_security_compliance(data):
    """验证安全合规"""
    has_encryption = data.get("has_encryption", False)
    has_backup = data.get("has_backup", False)

    return has_encryption and has_backup