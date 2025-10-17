"""
业务约束实现：业务规则
"""

from src.core.models import SymbolTable
from src.core.exceptions import BusinessRuleViolation

def check_budget_allocation(symbol_table: SymbolTable):
    """
    检查预算分配约束：所有任务的总预算不能超过项目预算
    """
    projects = symbol_table.get_entities_by_type("project")
    if not projects:
        return

    project = projects[0]  # 假设只有一个项目
    project_budget = project.raw_data.get("budget", 0)

    tasks = symbol_table.get_entities_by_type("task")
    total_task_budget = sum(task.raw_data.get("budget", 0) for task in tasks)

    if total_task_budget > project_budget:
        raise BusinessRuleViolation(
            rule_id="budget-allocation",
            message=f"预算超支：任务总预算 {total_task_budget} 超过项目预算 {project_budget}",
            location=project.location
        )

def check_team_member_assignment(symbol_table: SymbolTable):
    """
    检查团队成员分配约束：任务负责人必须在项目团队中
    """
    projects = symbol_table.get_entities_by_type("project")
    if not projects:
        return

    project = projects[0]
    team_members = project.raw_data.get("team_members", [])

    tasks = symbol_table.get_entities_by_type("task")
    for task in tasks:
        assignee = task.raw_data.get("assignee")
        if assignee and assignee not in team_members:
            raise BusinessRuleViolation(
                rule_id="team-member-assignment",
                message=f"任务负责人 {assignee} 不在项目团队中",
                location=task.location
            )

def check_status_consistency(task):
    """
    检查状态一致性约束：已完成的任务不能重新激活
    """
    status = task.raw_data.get("status")

    # 这个规则需要更复杂的实现来跟踪状态变化历史
    # 这里简化为检查状态值是否合理
    valid_statuses = ["pending", "in-progress", "completed", "cancelled"]
    if status not in valid_statuses:
        raise BusinessRuleViolation(
            rule_id="status-consistency",
            message=f"无效的任务状态: {status}",
            location=task.location
        )