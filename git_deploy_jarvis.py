import os
import sys
import git
from github import Github
from github import Auth
from dotenv import load_dotenv

def deploy():
    # Load dotenv from workspace
    dotenv_path = r"c:\Users\DELL\OneDrive\Desktop\assistent\.env"
    load_dotenv(dotenv_path)
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("[ERROR] GITHUB_TOKEN not found in .env file!")
        sys.exit(1)
        
    project_path = r"c:\Users\DELL\OneDrive\Desktop\assistent"
    repo_name = "JARVIS"
    
    print("[GIT] Connecting to GitHub...")
    try:
        auth = Auth.Token(token)
        g = Github(auth=auth)
        user = g.get_user()
        username = user.login
        print(f"[GIT] Authenticated as: {username}")
    except Exception as e:
        print(f"[ERROR] Error authenticating with GitHub: {e}")
        sys.exit(1)
        
    print(f"[GIT] Creating public repository '{repo_name}' on GitHub...")
    try:
        remote_repo = user.create_repo(
            repo_name, 
            description="JARVIS: Advanced Voice-Activated Agentic AI Desktop Assistant", 
            private=False
        )
        print(f"[GIT] Successfully created remote repository: {remote_repo.html_url}")
    except Exception as e:
        print(f"[GIT] Repository might already exist or error: {e}. Attempting to fetch existing repository...")
        try:
            remote_repo = user.get_repo(repo_name)
            print(f"[GIT] Using existing repository: {remote_repo.html_url}")
        except Exception as fe:
            try:
                remote_repo = user.get_repo(f"{username}/{repo_name}")
                print(f"[GIT] Using existing repository: {remote_repo.html_url}")
            except Exception as ffe:
                print(f"[ERROR] Failed to access repository: {ffe}")
                sys.exit(1)
                
    # Git operations
    print("[GIT] Initializing local repository...")
    try:
        if os.path.exists(os.path.join(project_path, ".git")):
            local_repo = git.Repo(project_path)
            print("[GIT] Opened existing local Git repository.")
        else:
            local_repo = git.Repo.init(project_path)
            print("[GIT] Initialized fresh local Git repository.")
    except Exception as ge:
        print(f"[ERROR] Error opening/initializing local repo: {ge}")
        sys.exit(1)
        
    # Configure git username and email if not configured locally to prevent commit failure
    with local_repo.config_writer() as cw:
        try:
            cw.set_value("user", "name", "BOSS")
            cw.set_value("user", "email", "boss@assistant.ai")
        except Exception as ce:
            print(f"[GIT] Config warning: {ce}")
            
    print("[GIT] Staging files (applying .gitignore rules)...")
    try:
        local_repo.git.add(all=True)
    except Exception as ae:
        print(f"[ERROR] Error staging files: {ae}")
        sys.exit(1)
        
    print("[GIT] Committing changes...")
    try:
        local_repo.index.commit("Deploy JARVIS: Core implementation & premium README.md")
        print("[GIT] Committed successfully.")
    except Exception as ce:
        print(f"[GIT] Commit status: {ce} (No changes to commit or already committed).")
        
    print("[GIT] Configuring remote repository...")
    remote_url = f"https://{token}@github.com/{username}/{repo_name}.git"
    
    try:
        if 'origin' in [r.name for r in local_repo.remotes]:
            origin = local_repo.remotes.origin
            origin.set_url(remote_url)
        else:
            origin = local_repo.create_remote('origin', remote_url)
        print("[GIT] Remote origin configured.")
    except Exception as re:
        print(f"[ERROR] Error configuring remote: {re}")
        sys.exit(1)
        
    print("[GIT] Pushing codebase to GitHub (main branch)...")
    try:
        active_branch = local_repo.active_branch.name
        print(f"[GIT] Active local branch is: {active_branch}")
        
        # Rename branch to main if it's master for modern standards
        if active_branch == "master":
            try:
                local_repo.git.branch("-M", "main")
                active_branch = "main"
                print("[GIT] Renamed branch to main.")
            except Exception as be:
                print(f"[GIT] Warning renaming branch: {be}")
                
        origin.push(refspec=f"{active_branch}:{active_branch}", force=True)
        print(f"[SUCCESS] Code pushed successfully to: {remote_repo.html_url}")
    except Exception as pe:
        print(f"[GIT] Error pushing: {pe}. Retrying with master branch...")
        try:
            origin.push(refspec="master:master", force=True)
            print(f"[SUCCESS] Code pushed successfully to: {remote_repo.html_url}")
        except Exception as pe2:
            print(f"[ERROR] Fatal error pushing to GitHub: {pe2}")
            sys.exit(1)

if __name__ == "__main__":
    deploy()
