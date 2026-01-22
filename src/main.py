"""
GitLab MR Reviewer - 主 CLI 應用程式
"""

import logging
from pathlib import Path
from typing import Optional

import click

from src.config import Config
from src.gitlab_.client import GitLabClient
from src.logger import setup_logging
from src.scanner.mr_scanner import MRScanner
from src.state.manager import StateManager
from src.clone.manager import CloneManager


# 全域變數
config: Optional[Config] = None
gitlab_client: Optional[GitLabClient] = None
mr_scanner: Optional[MRScanner] = None
state_manager: Optional[StateManager] = None
clone_manager: Optional[CloneManager] = None
logger: Optional[logging.Logger] = None


def init_app():
    """初始化應用程式"""
    global config, gitlab_client, mr_scanner, state_manager, clone_manager, logger
    
    # 載入設定
    config = Config.from_env()
    
    # 初始化日誌
    logger = setup_logging(
        log_level=config.log_level,
        log_dir=config.state_dir
    )
    
    logger.info("應用程式初始化開始")
    
    # 初始化各個元件
    gitlab_client = GitLabClient(
        url=config.gitlab_url,
        token=config.gitlab_token,
        ssl_verify=config.gitlab_ssl_verify
    )
    
    state_manager = StateManager(db_path=config.db_path)
    mr_scanner = MRScanner(gitlab_client, state_manager)
    clone_manager = CloneManager(config=config, state_manager=state_manager)
    
    logger.info("應用程式初始化完成")


@click.group()
@click.version_option(version="1.0.0", prog_name="gitlab-mr-reviewer")
def cli():
    """GitLab MR Reviewer - 自動化 MR 審查工作流程"""
    pass


@cli.command()
@click.option(
    "--exclude-wip",
    is_flag=True,
    help="排除 WIP (Work In Progress) 的 MR"
)
@click.option(
    "--exclude-draft",
    is_flag=True,
    help="排除草稿 (Draft) 的 MR"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="僅顯示操作而不實際執行"
)
def scan(exclude_wip: bool, exclude_draft: bool, dry_run: bool):
    """掃描 GitLab 並建立 MR Clone"""
    try:
        init_app()
        
        logger.info("開始掃描 MR")
        logger.info(f"設定: exclude_wip={exclude_wip}, exclude_draft={exclude_draft}, dry_run={dry_run}")
        
        # 掃描 MR
        scan_results = mr_scanner.scan(
            projects=config.projects,
            exclude_wip=exclude_wip,
            exclude_draft=exclude_draft
        )
        
        # 統計結果
        total_mrs = sum(len(result.merge_requests) for result in scan_results)
        logger.info(f"掃描完成，發現 {total_mrs} 個 MR")
        
        if dry_run:
            click.echo(f"✓ 試執行模式：將處理 {total_mrs} 個 MR")
            for result in scan_results:
                if result.error:
                    click.echo(f"  ✗ {result.project}: {result.error}")
                else:
                    for mr in result.merge_requests:
                        click.echo(f"  → {mr.project_name}#{mr.iid}: {mr.title}")
            return
        
        # 建立 clone
        for result in scan_results:
            if result.error:
                click.echo(f"✗ {result.project}: {result.error}")
                logger.error(f"掃描 {result.project} 時出錯: {result.error}")
                continue
            
            for mr in result.merge_requests:
                try:
                    clone_path = clone_manager.create_clone(mr)
                    click.echo(f"✓ {mr.project_name}#{mr.iid}: {clone_path}")
                    logger.info(f"建立 clone: {clone_path}")
                except Exception as e:
                    click.echo(f"✗ {mr.project_name}#{mr.iid}: {e}")
                    logger.error(f"建立 clone 失敗: {e}")
        
        click.echo(f"✓ 掃描和 clone 建立完成")
        logger.info("掃描和 clone 建立完成")
        
    except Exception as e:
        click.echo(f"✗ 錯誤: {e}", err=True)
        if logger:
            logger.error(f"掃描失敗: {e}")
        exit(1)


@cli.command("list-clones")
def list_clones():
    """列出所有已建立的 MR Clone"""
    try:
        init_app()
        
        logger.info("列出所有 clone")
        
        clones = clone_manager.list_clones()
        
        if not clones:
            click.echo("沒有 clone")
            return
        
        for project, mr_iids in clones.items():
            click.echo(f"\n{project}:")
            for mr_iid in sorted(mr_iids):
                clone_path = clone_manager.get_clone_path(project, mr_iid)
                if clone_path:
                    click.echo(f"  #{mr_iid}: {clone_path}")
        
        click.echo(f"\n總計: {sum(len(iids) for iids in clones.values())} 個 clone")
        logger.info(f"列出 {sum(len(iids) for iids in clones.values())} 個 clone")
        
    except Exception as e:
        click.echo(f"✗ 錯誤: {e}", err=True)
        if logger:
            logger.error(f"列出 clone 失敗: {e}")
        exit(1)


@cli.command("clean-clone")
@click.option(
    "--iid",
    required=True,
    type=int,
    help="MR 編號"
)
@click.option(
    "--project",
    required=True,
    type=str,
    help="專案名稱"
)
def clean_clone(iid: int, project: str):
    """刪除指定的 MR Clone"""
    try:
        init_app()
        
        logger.info(f"刪除 clone: {project}#{iid}")
        
        # 查找對應的 clone
        clone_path = clone_manager.get_clone_path(project, iid)
        
        if not clone_path:
            click.echo(f"✗ Clone 不存在: {project}#{iid}")
            logger.warning(f"Clone 不存在: {project}#{iid}")
            exit(1)
        
        # 建立臨時 MRInfo 以便刪除
        from src.gitlab_.models import MRInfo
        mr_info = MRInfo(
            id=0,
            project_id=0,
            project_name=project,
            iid=iid,
            title="",
            description="",
            state="",
            author="",
            created_at="",
            updated_at="",
            source_branch="",
            target_branch="",
            web_url="",
            draft=False,
            work_in_progress=False
        )
        
        if clone_manager.delete_clone(mr_info):
            click.echo(f"✓ Clone 已刪除: {project}#{iid}")
            logger.info(f"Clone 已刪除: {project}#{iid}")
        else:
            click.echo(f"✗ 刪除失敗: {project}#{iid}")
            logger.error(f"刪除 clone 失敗: {project}#{iid}")
            exit(1)
        
    except Exception as e:
        click.echo(f"✗ 錯誤: {e}", err=True)
        if logger:
            logger.error(f"刪除 clone 失敗: {e}")
        exit(1)


# Deprecated commands removed


if __name__ == "__main__":
    cli()
