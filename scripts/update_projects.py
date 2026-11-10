#!/usr/bin/env python3
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

DESCRIPTIONS = {
    "BTL_KTLT": "C++ mobile subscriber management course project (I still wish it was a videogame).",
    "BTL-KTVXL-N1": "VXL group project: an STM32F103 and MPU6050 inclinometer.",
    "minecraft": "Minecraft server and bots.",
}
START = "<!-- projects:start -->"
END = "<!-- projects:end -->"


def main():
    query = '''query($cursor:String){user(login:"vgbn2"){repositories(first:100,after:$cursor,privacy:PUBLIC,ownerAffiliations:OWNER){pageInfo{hasNextPage endCursor} nodes{name description isFork url defaultBranchRef{target{... on Commit{history{totalCount}}}}}}}}'''
    projects = []
    cursor = None
    while True:
        request = Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": query, "variables": {"cursor": cursor}}).encode(),
            headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"], "Content-Type": "application/json"},
        )
        with urlopen(request) as response:
            result = json.load(response)
        if result.get("errors"):
            raise RuntimeError(result["errors"])
        repositories = result["data"]["user"]["repositories"]
        for repo in repositories["nodes"]:
            name = repo["name"]
            if repo["isFork"] or name in {"vgbn2", "diabetic", "personal_finance_draft"} or not repo["defaultBranchRef"]:
                continue
            count = repo["defaultBranchRef"]["target"]["history"]["totalCount"]
            description = DESCRIPTIONS.get(name, repo["description"] or "No description yet.")
            projects.append((name, description.replace("\n", " "), count))
        if not repositories["pageInfo"]["hasNextPage"]:
            break
        cursor = repositories["pageInfo"]["endCursor"]

    lines = [START, "## Projects", "", "- **[SV Console](https://github.com/vgbn2/personal_finance_draft)** — Market data ingestion and trading research and execution software.", "- **[diabetic](https://github.com/vgbn2/diabetic)** — Glucose monitoring and prediction research, including faint-risk prediction for people with type 1 diabetes.", "", "### More projects", "", "Public non-fork repositories, ordered by total commits on the default branch; counts include all contributors.", ""]
    for name, description, count in sorted(projects, key=lambda item: (-item[2], item[0].lower())):
        lines.append(f"- **[{name}](https://github.com/vgbn2/{name})** — {description} ({count} commits)")
    lines.append(END)
    path = Path("README.md")
    text = path.read_text()
    if text.count(START) != 1 or text.count(END) != 1 or text.index(START) > text.index(END):
        raise ValueError("Expected exactly one ordered pair of project markers")
    path.write_text(text[:text.index(START)] + "\n".join(lines) + text[text.index(END) + len(END):])


if __name__ == "__main__":
    main()
