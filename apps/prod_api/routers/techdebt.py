from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import subprocess, os, json, tempfile

router = APIRouter()

class RepoRequest(BaseModel):
    repo_url: str
    github_token: str = None
    ai_feedback: bool = True

@router.post("/scan")
def scan_repo(req: RepoRequest):
    try:
        tmpdir = tempfile.mkdtemp()
        repo_path = os.path.join(tmpdir, "repo")

        clone_cmd = ["git", "clone"]
        if req.github_token and "github.com" in req.repo_url:
            token_url = req.repo_url.replace(
                "https://", f"https://oauth2:{req.github_token}@"
            )
            clone_cmd.append(token_url)
        else:
            clone_cmd.append(req.repo_url)
        clone_cmd.append(repo_path)
        subprocess.run(clone_cmd, check=True)

        # --- run static analyzers ---
        bandit_out = subprocess.run(
            ["bandit", "-r", repo_path, "-f", "json"], capture_output=True, text=True
        ).stdout
        bandit_json = json.loads(bandit_out) if bandit_out else {}
        sec_issues = len(bandit_json.get("results", []))

        radon_out = subprocess.run(
            ["radon", "cc", "-j", repo_path], capture_output=True, text=True
        ).stdout
        complexity_json = json.loads(radon_out) if radon_out else {}
        hotspots = sum(len(v) for v in complexity_json.values())

        pylint_out = subprocess.run(
            ["pylint", repo_path, "--output-format=json"], capture_output=True, text=True
        ).stdout
        pylint_json = json.loads(pylint_out) if pylint_out else []
        pylint_avg = (
            sum(x.get("score", 0) for x in pylint_json if "score" in x) / len(pylint_json)
            if pylint_json else 0
        )

        score = max(0, 100 - (sec_issues + hotspots / 2))

        result = {
            "ok": True,
            "summary": {
                "security_issues": sec_issues,
                "complexity_hotspots": hotspots,
                "tech_debt_score": round(score, 2),
                "roi": {
                    "days_loss_per_month": round(hotspots * 0.2, 1),
                    "monthly_loss_usd": round(hotspots * 120, 2),
                    "potential_savings_usd": round(hotspots * 72, 2)
                }
            }
        }

        # --- optional AI summary ---
        if req.ai_feedback and os.getenv("OPENAI_API_KEY"):
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            analysis_prompt = f"""
            Summarize technical debt for this repo:
            Security issues: {sec_issues}
            Complexity hotspots: {hotspots}
            Pylint average: {pylint_avg}
            Tech debt score: {score}
            """
            feedback = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a senior software auditor."},
                    {"role": "user", "content": analysis_prompt}
                ]
            )
            result["ai"] = {"analysis": feedback.choices[0].message.content}

        report_path = "reports/techdebt_report.json"
        os.makedirs("reports", exist_ok=True)
        json.dump(result, open(report_path, "w"), indent=2)
        result["report_path"] = report_path
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
