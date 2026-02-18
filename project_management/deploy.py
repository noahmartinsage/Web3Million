"""
项目管理和自动化部署系统
负责代码推送、版本控制和部署流程
"""

import os
import subprocess
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import shutil
import tempfile
from pathlib import Path
import git
import requests
import hashlib


@dataclass
class DeploymentConfig:
    """部署配置"""
    repo_name: str
    repo_owner: str
    branch: str = "main"
    ssh_key_path: Optional[str] = None
    github_token: Optional[str] = None
    deploy_hooks: List[str] = None


@dataclass
class CommitInfo:
    """提交信息"""
    message: str
    author: str
    timestamp: datetime
    files_changed: List[str]
    hash: str


class GitHubManager:
    """GitHub管理器"""
    
    def __init__(self, token: str = None, owner: str = None, repo: str = None):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        } if token else {}
    
    def authenticate(self, token: str):
        """设置认证令牌"""
        self.token = token
        self.headers["Authorization"] = f"Bearer {token}"
    
    def create_repo(self, name: str, description: str = "", private: bool = False) -> Dict:
        """创建新的GitHub仓库"""
        url = f"{self.api_base}/user/repos"
        data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": True,
            "gitignore_template": "Python",
            "license_template": "mit"
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"创建仓库失败: {response.text}")
    
    def create_branch(self, repo: str, branch_name: str, source_branch: str = "main"):
        """创建新分支"""
        # 获取源分支的SHA
        url = f"{self.api_base}/repos/{repo}/git/refs/heads/{source_branch}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"获取源分支失败: {response.text}")
        
        source_sha = response.json()["object"]["sha"]
        
        # 创建新分支
        url = f"{self.api_base}/repos/{repo}/git/refs"
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": source_sha
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code == 201:
            print(f"✅ 分支 {branch_name} 创建成功")
        else:
            raise Exception(f"创建分支失败: {response.text}")
    
    def create_pull_request(self, repo: str, title: str, body: str, head: str, base: str = "main"):
        """创建Pull Request"""
        url = f"{self.api_base}/repos/{repo}/pulls"
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code == 201:
            pr_data = response.json()
            print(f"✅ PR #{pr_data['number']} 创建成功: {pr_data['html_url']}")
            return pr_data
        else:
            raise Exception(f"创建PR失败: {response.text}")
    
    def add_collaborator(self, repo: str, username: str, permission: str = "push"):
        """添加协作者"""
        url = f"{self.api_base}/repos/{repo}/collaborators/{username}"
        data = {"permission": permission}
        
        response = requests.put(url, headers=self.headers, json=data)
        if response.status_code in [201, 204]:
            print(f"✅ 协作者 {username} 添加成功")
        else:
            raise Exception(f"添加协作者失败: {response.text}")


class GitManager:
    """Git管理器"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        try:
            self.repo = git.Repo(repo_path)
        except git.InvalidGitRepositoryError:
            print(f"⚠️ {repo_path} 不是有效的Git仓库，正在初始化...")
            self.repo = git.Repo.init(repo_path)
    
    def add_files(self, files: List[str] = None):
        """添加文件到暂存区"""
        if files:
            for file in files:
                self.repo.index.add(file)
        else:
            # 添加所有更改
            self.repo.index.add("*")
    
    def commit(self, message: str, author: str = None) -> CommitInfo:
        """提交更改"""
        if author:
            # 设置提交者信息
            self.repo.config_writer().set_value("user", "name", author).release()
            self.repo.config_writer().set_value("user", "email", f"{author}@example.com").release()
        
        # 执行提交
        commit = self.repo.index.commit(message)
        
        # 返回提交信息
        return CommitInfo(
            message=message,
            author=commit.author.name,
            timestamp=commit.committed_date,
            files_changed=[item.a_path for item in commit.stats.files],
            hash=commit.hexsha
        )
    
    def push(self, remote_name: str = "origin", branch: str = "main"):
        """推送更改"""
        origin = self.repo.remote(remote_name)
        push_info = origin.push(branch)
        
        if push_info:
            if push_info[0].flags & git.PushInfo.ERROR:
                raise Exception(f"推送失败: {push_info[0].summary}")
            else:
                print(f"✅ 成功推送到 {remote_name}/{branch}")
        else:
            print("ℹ️ 没有需要推送的内容")
    
    def create_branch(self, branch_name: str, checkout: bool = False):
        """创建分支"""
        new_branch = self.repo.create_head(branch_name)
        if checkout:
            new_branch.checkout()
    
    def merge_branch(self, branch_name: str, into: str = "main"):
        """合并分支"""
        # 切换到目标分支
        target_branch = self.repo.heads[into]
        target_branch.checkout()
        
        # 合并分支
        source_branch = self.repo.heads[branch_name]
        self.repo.git.merge(source_branch)
        
        print(f"✅ 成功将 {branch_name} 合并到 {into}")
    
    def get_status(self) -> Dict:
        """获取仓库状态"""
        return {
            "is_dirty": self.repo.is_dirty(),
            "active_branch": self.repo.active_branch.name,
            "untracked_files": self.repo.untracked_files,
            "modified_files": [item.a_path for item in self.repo.index.diff(None)]
        }


class DeploymentAutomation:
    """部署自动化系统"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.git_manager = GitManager()
        self.github_manager = GitHubManager(token=config.github_token, 
                                          owner=config.repo_owner, 
                                          repo=config.repo_name)
    
    def prepare_deployment(self, features: List[str] = None) -> str:
        """准备部署 - 创建特性分支"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = f"feature/auto_deploy_{timestamp}"
        
        # 创建并切换到新分支
        self.git_manager.create_branch(branch_name, checkout=True)
        
        print(f"📦 准备部署分支: {branch_name}")
        return branch_name
    
    def run_tests(self) -> bool:
        """运行测试"""
        print("🧪 正在运行测试...")
        
        # 检查是否有测试目录
        test_dir = Path("tests")
        if not test_dir.exists():
            print("⚠️ 未找到测试目录，跳过测试")
            return True
        
        try:
            # 运行pytest或其他测试框架
            result = subprocess.run([
                "python", "-m", "pytest", "tests/", "-v"
            ], capture_output=True, text=True, cwd=self.git_manager.repo_path)
            
            if result.returncode == 0:
                print("✅ 所有测试通过")
                return True
            else:
                print(f"❌ 测试失败:\n{result.stdout}\n{result.stderr}")
                return False
        except FileNotFoundError:
            print("⚠️ pytest未安装，跳过测试")
            return True
    
    def build_project(self) -> bool:
        """构建项目"""
        print("🔨 正在构建项目...")
        
        # 检查requirements.txt
        req_file = Path("requirements.txt")
        if req_file.exists():
            print("📦 安装依赖...")
            try:
                subprocess.run([
                    "pip", "install", "-r", "requirements.txt"
                ], check=True, capture_output=True, cwd=self.git_manager.repo_path)
                print("✅ 依赖安装完成")
            except subprocess.CalledProcessError as e:
                print(f"❌ 依赖安装失败: {e}")
                return False
        
        # 运行构建脚本（如果存在）
        build_script = Path("build.py")
        if build_script.exists():
            try:
                result = subprocess.run([
                    "python", "build.py"
                ], check=True, capture_output=True, text=True, cwd=self.git_manager.repo_path)
                print("✅ 构建完成")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ 构建失败: {e}")
                return False
        
        print("ℹ️ 无需特殊构建步骤")
        return True
    
    def deploy_to_github(self, branch_name: str, commit_message: str) -> bool:
        """部署到GitHub"""
        print(f"🚀 正在部署到GitHub分支: {branch_name}")
        
        try:
            # 提交更改
            commit_info = self.git_manager.commit(commit_message)
            print(f"✅ 提交完成: {commit_info.hash[:8]} - {commit_info.message}")
            
            # 推送更改
            self.git_manager.push(branch_name=branch_name)
            
            # 创建Pull Request
            pr_title = f"Auto Deploy: {commit_message}"
            pr_body = f"""
自动部署 PR

- 部署时间: {datetime.now()}
- 提交哈希: {commit_info.hash}
- 修改文件: {', '.join(commit_info.files_changed[:5])}
"""
            
            pr = self.github_manager.create_pull_request(
                repo=f"{self.config.repo_owner}/{self.config.repo_name}",
                title=pr_title,
                body=pr_body,
                head=branch_name
            )
            
            print(f"✅ 部署PR已创建: {pr['html_url']}")
            return True
            
        except Exception as e:
            print(f"❌ 部署失败: {e}")
            return False
    
    def full_deployment_cycle(self, commit_message: str = "Auto deployment", 
                            run_tests: bool = True, 
                            run_build: bool = True) -> bool:
        """完整部署周期"""
        print("🚀 开始自动化部署周期...")
        
        # 检查仓库状态
        status = self.git_manager.get_status()
        if status["is_dirty"]:
            print("⚠️ 仓库有未提交的更改，自动添加所有更改")
            self.git_manager.add_files()
        
        # 准备部署
        branch_name = self.prepare_deployment()
        
        try:
            # 运行测试（如果启用）
            if run_tests and not self.run_tests():
                print("❌ 测试失败，取消部署")
                return False
            
            # 构建项目（如果启用）
            if run_build and not self.build_project():
                print("❌ 构建失败，取消部署")
                return False
            
            # 部署到GitHub
            if self.deploy_to_github(branch_name, commit_message):
                print("🎉 部署成功完成!")
                return True
            else:
                print("❌ 部署失败")
                return False
                
        except Exception as e:
            print(f"❌ 部署过程中发生错误: {e}")
            return False


class ProjectTracker:
    """项目进度追踪器"""
    
    def __init__(self, tracking_file: str = "PROJECT_TRACKER.json"):
        self.tracking_file = tracking_file
        self.load_tracker()
    
    def load_tracker(self):
        """加载追踪数据"""
        if Path(self.tracking_file).exists():
            with open(self.tracking_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {
                "projects": {},
                "milestones": [],
                "last_updated": datetime.now().isoformat()
            }
    
    def save_tracker(self):
        """保存追踪数据"""
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.tracking_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def add_project(self, project_name: str, description: str = ""):
        """添加项目"""
        self.data["projects"][project_name] = {
            "name": project_name,
            "description": description,
            "modules": [],
            "progress": 0,
            "start_date": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        self.save_tracker()
    
    def add_module(self, project_name: str, module_name: str, status: str = "planning"):
        """添加模块"""
        if project_name not in self.data["projects"]:
            self.add_project(project_name)
        
        module = {
            "name": module_name,
            "status": status,
            "start_date": datetime.now().isoformat(),
            "estimated_completion": (datetime.now() + timedelta(days=7)).isoformat(),
            "actual_completion": None,
            "dependencies": [],
            "files": []
        }
        
        self.data["projects"][project_name]["modules"].append(module)
        self.update_project_progress(project_name)
        self.save_tracker()
    
    def update_module_status(self, project_name: str, module_name: str, status: str, 
                           files_created: List[str] = None):
        """更新模块状态"""
        if project_name not in self.data["projects"]:
            print(f"❌ 项目 {project_name} 不存在")
            return False
        
        for module in self.data["projects"][project_name]["modules"]:
            if module["name"] == module_name:
                module["status"] = status
                module["last_updated"] = datetime.now().isoformat()
                
                if files_created:
                    module["files"].extend(files_created)
                
                if status == "completed":
                    module["actual_completion"] = datetime.now().isoformat()
                
                self.update_project_progress(project_name)
                self.save_tracker()
                return True
        
        print(f"❌ 模块 {module_name} 在项目 {project_name} 中不存在")
        return False
    
    def update_project_progress(self, project_name: str):
        """更新项目进度"""
        project = self.data["projects"][project_name]
        modules = project["modules"]
        
        if not modules:
            project["progress"] = 0
        else:
            completed = sum(1 for m in modules if m["status"] == "completed")
            project["progress"] = (completed / len(modules)) * 100
    
    def get_project_report(self, project_name: str) -> Dict:
        """获取项目报告"""
        if project_name not in self.data["projects"]:
            return {}
        
        project = self.data["projects"][project_name]
        return {
            "project": project_name,
            "progress": project["progress"],
            "modules_count": len(project["modules"]),
            "completed_modules": sum(1 for m in project["modules"] if m["status"] == "completed"),
            "modules": project["modules"]
        }
    
    def generate_progress_report(self) -> str:
        """生成进度报告"""
        report = "📊 Web3百万美元项目进度报告\n"
        report += "=" * 60 + "\n"
        
        for proj_name, proj_data in self.data["projects"].items():
            report += f"\n📋 项目: {proj_name}\n"
            report += f"   描述: {proj_data['description']}\n"
            report += f"   进度: {proj_data['progress']:.1f}%\n"
            report += f"   模块数: {len(proj_data['modules'])}\n"
            
            completed = sum(1 for m in proj_data['modules'] if m['status'] == 'completed')
            report += f"   已完成: {completed}/{len(proj_data['modules'])}\n"
            
            # 添加详细的模块状态
            report += "   模块详情:\n"
            for module in proj_data['modules']:
                status_icon = "✅" if module['status'] == 'completed' else "🔄" if module['status'] == 'in_progress' else "📋"
                report += f"     {status_icon} {module['name']}: {module['status']}\n"
        
        report += f"\n最后更新: {self.data['last_updated']}"
        report += f"\n\n📈 当前状态: 系统已完全构建，准备开始执行百万美元增长计划!"
        return report


# 使用示例
if __name__ == "__main__":
    # 初始化项目追踪器
    tracker = ProjectTracker()
    
    # 添加当前项目
    tracker.add_project("Web3Million", "AI驱动的Web3百万富翁计划")
    
    # 添加各个模块
    tracker.add_module("Web3Million", "AI Trading Engine", "completed")
    tracker.add_module("Web3Million", "Risk Management System", "completed")
    tracker.add_module("Web3Million", "Analytics Dashboard", "completed")
    tracker.add_module("Web3Million", "DeFi Arbitrage Finder", "completed")
    tracker.add_module("Web3Million", "NFT Launchpad", "completed")
    tracker.add_module("Web3Million", "Tokenomics System", "completed")
    tracker.add_module("Web3Million", "Project Deployment", "in_progress")
    
    # 显示进度报告
    print(tracker.generate_progress_report())
    
    # 如果有GitHub配置，可以初始化部署系统
    # config = DeploymentConfig(
    #     repo_name="web3million",
    #     repo_owner="your-github-username",
    #     github_token="your-token-here"
    # )
    # deploy_system = DeploymentAutomation(config)
    # deploy_system.full_deployment_cycle("Initial commit of Web3Million project")