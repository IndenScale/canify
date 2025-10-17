"""
业务约束实现：项目规则
"""

from src.core.models import SymbolTable
from src.core.exceptions import CanifyValidationError

def check_single_project_entity(symbol_table: SymbolTable):
    """
    检查项目中是否只有一个 project 实体。
    """
    project_entities = symbol_table.get_entities_by_type("project")
    num_projects = len(project_entities)

    if num_projects != 1:
        locations = [p.location for p in project_entities]
        
        if num_projects == 0:
            message = "验证失败：项目中未找到任何 'project' 类型的实体，期望找到 1 个。"
            error_location = None 
        else:
            message = f"验证失败：项目中找到了 {num_projects} 个 'project' 类型的实体，期望找到 1 个。"
            error_location = locations[0] if locations else None

        # 理想情况下，我们应该定义一个更具体的 BusinessRuleViolation 异常
        # 并将 rule_id="project-singleton" 传递进去，以便更好地追踪错误来源
        raise CanifyValidationError(
            message=message,
            location=error_location
        )
