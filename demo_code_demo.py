#!/usr/bin/env python3
"""
示例代码 - Hermes Team Collaboration Demo
这是团队协作项目的示例代码
"""

class TeamBot:
    """团队协作机器人基类"""
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.created_at = datetime.now()
    
    def __repr__(self):
        return f"{self.name} ({self.role})"
    
    def process_task(self, task: str) -> str:
        """处理任务"""
        return f"[{self.name}] 处理任务：{task}"


class MocPro(TeamBot):
    """moc-pro - 本地开发"""
    
    def __init__(self):
        super().__init__("moc-pro", "本地开发 + Owner")
    
    def develop(self, feature: str) -> str:
        """开发功能"""
        return f"🚀 {self.name} 开发功能：{feature}"
    
    def test(self, test_name: str) -> str:
        """测试"""
        return f"🧪 {self.name} 运行测试：{test_name}"


class Xiaoxiami(TeamBot):
    """小虾米 - Code Review"""
    
    def __init__(self):
        super().__init__("小虾米", "Code Review 自动化")
    
    def review(self, pr_number: int) -> str:
        """代码审查"""
        return f"🔍 {self.name} Review PR #{pr_number}"
    
    def approve(self) -> str:
        """批准"""
        return f"✅ {self.name} 批准代码"


class Xiaohe(TeamBot):
    """小河虾 - Automation"""
    
    def __init__(self):
        super().__init__("小河虾", "GitHub Actions 自动化")
    
    def backup(self) -> str:
        """自动备份"""
        return f"💾 {self.name} 执行每日备份"
    
    def deploy(self) -> str:
        """部署"""
        return f"🚀 {self.name} 自动部署"


if __name__ == "__main__":
    # 示例用法
    moc_pro = MocPro()
    print(moc_pro.develop("新功能"))
    print(moc_pro.test("单元测试"))
    
    xiaoxiami = Xiaoxiami()
    print(xiaoxiami.review(1))
    print(xiaoxiami.approve())
    
    xiaohe = Xiaohe()
    print(xiaohe.backup())
    print(xiaohe.deploy())
