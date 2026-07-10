"""
GitHub Helper Script.
Reads local Git credentials and calls the GitHub REST API to create a remote repository.
"""

import os
import re
import urllib.request
import json
from pathlib import Path

def get_credentials():
    home = Path.home()
    cred_file = home / ".git-credentials"
    if not cred_file.exists():
        raise FileNotFoundError("Git credentials file not found.")
        
    with open(cred_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Pattern: https://username:password_or_token@github.com
    match = re.search(r"https://([^:]+):([^@]+)@github\.com", content)
    if not match:
        raise ValueError("Could not find GitHub credentials in .git-credentials")
        
    username, token = match.groups()
    return username, token

def create_repository(username, token, repo_name):
    url = "https://api.github.com/user/repos"
    data = {
        "name": repo_name,
        "description": "Walmart Smart Inventory & Restocking Assistant: An Enterprise Multi-Agent AI Platform for Intelligent Inventory Monitoring, Demand Prediction, and Automated Restocking.",
        "private": False,
        "has_issues": True,
        "has_projects": True,
        "has_wiki": True
    }
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "WalmartAgenticAI"
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            resp_data = json.loads(res.read().decode("utf-8"))
            print(f"SUCCESS: Repository '{repo_name}' created on GitHub.")
            print(f"Clone URL: {resp_data['clone_url']}")
            print(f"HTML URL: {resp_data['html_url']}")
            return resp_data["clone_url"], resp_data["html_url"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(error_body)
            if any("name already exists" in err.get("message", "") for err in err_json.get("errors", [])):
                print(f"INFO: Repository '{repo_name}' already exists on GitHub.")
                clone_url = f"https://github.com/{username}/{repo_name}.git"
                html_url = f"https://github.com/{username}/{repo_name}"
                return clone_url, html_url
        except Exception:
            pass
        raise Exception(f"Failed to create repository: HTTP {e.code} - {e.reason}\n{error_body}")

if __name__ == "__main__":
    try:
        username, token = get_credentials()
        print(f"Found credentials for user: {username}")
        clone_url, html_url = create_repository(username, token, "walmart-agentic-ai")
    except Exception as e:
        print(f"ERROR: {str(e)}")
