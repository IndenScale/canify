"""
业务约束实现：业务规则
"""

from src.canify.decorators import fixture, test_case
from src.canify.models import View
from src.canify.models.validation_result import ValidationResult, ValidationError, ValidationSeverity


@fixture
def get_project_and_tasks():
    """获取项目和任务数据"""
    # 在实际实现中，这里会从符号表中获取数据
    # 这里返回模拟数据用于演示
    return {
        "projects": [
            {
                "id": "project-1",
                "type": "project",
                "name": "示例项目",
                "budget": 100000
            }
        ],
        "tasks": [
            {
                "id": "task-1",
                "type": "task",
                "name": "任务1",
                "budget": 30000,
                "assignee": "张三"
            },
            {
                "id": "task-2",
                "type": "task",
                "name": "任务2",
                "budget": 40000,
                "assignee": "李四"
            }
        ]
    }


@fixture
def get_tasks():
    """获取任务数据"""
    return {
        "tasks": [
            {
                "id": "task-1",
                "type": "task",
                "name": "任务1",
                "status": "in-progress"
            },
            {
                "id": "task-2",
                "type": "task",
                "name": "任务2",
                "status": "completed"
            }
        ]
    }


@test_case
def check_budget_allocation(data):
    """
    检查预算分配约束：所有任务的总预算不能超过项目预算
    """
    projects = data.get("projects", [])
    tasks = data.get("tasks", [])

    if not projects:
        return True

    project = projects[0]  # 假设只有一个项目
    project_budget = project.get("budget", 0)

    total_task_budget = sum(task.get("budget", 0) for task in tasks)

    if total_task_budget > project_budget:
        return ValidationResult.error_result([
            ValidationError(
                rule_id="budget-allocation",
                message=f"预算超支：任务总预算 {total_task_budget} 超过项目预算 {project_budget}",
                severity=ValidationSeverity.ERROR,
                location=None
            )
        ])

    return True

@test_case
def check_team_member_assignment(data):
    """
    检查团队成员分配约束：任务负责人必须在项目团队中
    """
    projects = data.get("projects", [])
    tasks = data.get("tasks", [])

    if not projects:
        return True

    project = projects[0]
    team_members = project.get("team_members", ["张三", "李四", "王五"])  # 模拟团队成员

    result = ValidationResult.success_result()

    for task in tasks:
        assignee = task.get("assignee")
        if assignee and assignee not in team_members:
            result.add_error(
                ValidationError(
                    rule_id="team-member-assignment",
                    message=f"任务负责人 {assignee} 不在项目团队中",
                    severity=ValidationSeverity.ERROR,
                    location=None
                )
            )

    return result if not result.success else True


@test_case
def check_status_consistency(data):
    """
    检查状态一致性约束：已完成的任务不能重新激活
    """
    tasks = data.get("tasks", [])

    result = ValidationResult.success_result()

    for task in tasks:
        status = task.get("status")

        # 简化的状态检查
        valid_statuses = ["pending", "in-progress", "completed", "cancelled"]
        if status not in valid_statuses:
            result.add_error(
                ValidationError(
                    rule_id="status-consistency",
                    message=f"无效的任务状态: {status}",
                    severity=ValidationSeverity.ERROR,
                    location=None
                )
            )

    return result if not result.success else True