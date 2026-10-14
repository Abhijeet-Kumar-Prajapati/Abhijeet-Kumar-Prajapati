#!/usr/bin/env python3
"""
GitHub Profile Auto-Manager
===========================

Apne GitHub profile ko apne aap update karta hai, har baar.

Ye script kya karta hai
-----------------------
1. README ke andar sirf `AUTO` markers ke beech wala hissa badalta hai.
   Aapka likha hua text kabhi nahi hatata.
2. Naye repo banate hi README ka projects table apne aap update ho jata hai.
3. Repos me jo languages use ho rahi hain, unke skills badges khud set hote hain.
4. Har repo ke `topics` apne aap language + description se sync hote hain
   (yeh GitHub search/discovery me dikhne ke liye hota hai).
5. Profile ka bio apne aap set hota hai.
6. Sirf tab commit karta hai jab kuch SACH me badla ho — warna nahi.
   (Isse workflow apne aap se infinite loop me nahi chalta.)

Istemal
-------
    python automation/profile_manager.py --dry-run     # sirf dekho, kuch commit nahi
    python automation/profile_manager.py               # actually update karo

Zaroori environment variable
----------------------------
    GITHUB_TOKEN   - writes ke liye token (repo me Actions se apne aap mil jata hai)

Sirf dependencies: Python 3.9+ (koi pip install nahi karna)
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

API = "https://api.github.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "owner": "Abhijeet-Kumar-Prajapati",
    "profile_repo": "Abhijeet-Kumar-Prajapati",
    "branch": "main",
    "readme_path": "README.md",
    "max_projects": 8,
    "exclude_repos": [],
    "auto_topics": True,
    "auto_bio": True,
    "auto_skills": True,
    "auto_projects": True,
    "commit_message": "chore(profile): auto-update by profile_manager",
    "profile": {
        "bio": "Web Developer - HTML, CSS & JavaScript. Building responsive, clean and user-friendly projects.",
        "name": "Abhijeet Kumar Prajapati",
        "location": "India",
    },
    "topic_rules": {
        "HTML": ["html", "frontend", "web"],
        "CSS": ["css", "frontend", "responsive-design"],
        "JavaScript": ["javascript", "frontend", "web"],
        "Python": ["python", "automation", "scripting"],
        "TypeScript": ["typescript", "frontend"],
    },
}

# Language -> shields.io badge
LANG_BADGES = {
    "HTML": ("E34F26", "html5", "white"),
    "CSS": ("1572B6", "css3", "white"),
    "JavaScript": ("F7DF1E", "javascript", "black"),
    "TypeScript": ("3178C6", "typescript", "white"),
    "Python": ("3776AB", "python", "white"),
    "Java": ("007396", "openjdk", "white"),
    "C": ("A8B9CC", "c", "black"),
    "C++": ("00599C", "cplusplus", "white"),
    "C#": ("512BD4", "csharp", "white"),
    "PHP": ("777BB4", "php", "white"),
    "Ruby": ("CC342D", "ruby", "white"),
    "Swift": ("F05138", "swift", "white"),
    "Kotlin": ("7F52FF", "kotlin", "white"),
    "Dart": ("0175C2", "dart", "white"),
    "React": ("61DAFB", "react", "black"),
    "Vue.js": ("4FC08D", "vuedotjs", "black"),
    "Node.js": ("339933", "nodedotjs", "white"),
    "MySQL": ("4479A1", "mysql", "white"),
    "SQL": ("025E8C", "database", "white"),
    "Git": ("F05032", "git", "white"),
    "GitHub": ("181717", "github", "white"),
    "VS Code": ("007ACC", "visualstudiocode", "white"),
    "PostgreSQL": ("4169E1", "postgresql", "white"),
    "MongoDB": ("47A248", "mongodb", "white"),
    "Linux": ("FCC624", "linux", "black"),
    "Figma": ("F24E1E", "figma", "white"),
    "Docker": ("2496ED", "docker", "white"),
}

# ---------------------------------------------------------------------------
# github api
# ---------------------------------------------------------------------------


class ApiError(RuntimeError):
    pass


def api(method: str, path: str, token: str | None, payload=None, retries: int = 3):
    """GitHub API call with retry + rate-limit backoff."""
    url = API + path
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-profile-auto-manager",
    }
    if token:
        headers["Authorization"] = "Bearer " + token

    last_error = None
    for attempt in range(retries):
        req = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else None
        except HTTPError as e:
            last_error = f"HTTP {e.code} on {method} {path}"
            # rate limit / secondary limit -> ruk ke dobara try karo
            if e.code in (403, 429) and attempt < retries - 1:
                time.sleep(3 * (2 ** attempt))
                continue
            try:
                detail = e.read().decode("utf-8")[:200]
                last_error += f" -> {detail}"
            except Exception:
                pass
            break
        except URLError as e:
            last_error = f"network error on {method} {path}: {e.reason}"
            if attempt < retries - 1:
                time.sleep(2 * (2 ** attempt))
                continue
            break

    raise ApiError(last_error or "unknown error")


def get_file(token, owner, repo, path, ref):
    """Return (content, sha) of a file. Returns (None, None) if not found."""
    try:
        r = api("GET", f"/repos/{owner}/{repo}/contents/{path}?ref={ref}", token)
    except ApiError as e:
        if "HTTP 404" in str(e):
            return None, None
        raise
    content = base64.b64decode(r["content"]).decode("utf-8")
    return content, r["sha"]


def put_file(token, owner, repo, path, ref, sha, content, message):
    """Create or update a file via the Contents API (git install nahi chahiye)."""
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": ref,
    }
    if sha:
        payload["sha"] = sha
    return api("PUT", f"/repos/{owner}/{repo}/contents/{path}", token, payload)


# ---------------------------------------------------------------------------
# readme blocks
# ---------------------------------------------------------------------------

START = "<!-- AUTO:{name}:START -->"
END = "<!-- AUTO:{name}:END -->"


def load_dotenv():
    """.env file se token padhta hai (sirf local run ke liye).

    Isse `setx` ki zaroorat nahi - token disk par ek aise file me rehta hai
    jo .gitignore me listed hai, aur jo kabhi commit nahi hota.
    """
    path = os.path.join(ROOT, ".env")
    if not os.path.exists(path):
        return
    try:
        # utf-8-sig: Windows Notepad/PowerShell jo BOM (\\ufeff) lagate hain
        # use hata deta hai. Iske bina pehla key kabhi read hi nahi hota.
        with open(path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip().lstrip("\ufeff").strip()
                val = val.strip().strip('"').strip("'")
                # env me pehle se token set hai to usi ko priority dete hain
                os.environ.setdefault(key, val)
    except Exception as e:
        print(f"! .env padh nahi paya: {e}")


def replace_block(text: str, name: str, body: str):
    """Replace only the content between AUTO markers. Returns (new_text, changed)."""
    s, e = START.format(name=name), END.format(name=name)
    i, j = text.find(s), text.find(e)
    if i == -1 or j == -1 or j < i:
        return text, False
    replacement = s + "\n" + body.rstrip() + "\n" + e
    updated = text[:i] + replacement + text[j + len(e):]
    return updated, updated != text


# ---------------------------------------------------------------------------
# renderers
# ---------------------------------------------------------------------------


def pick_repos(repos, cfg):
    """Filter out profile repo + excluded, sort by best signal."""
    excluded = {cfg["profile_repo"].lower()} | {x.lower() for x in cfg["exclude_repos"]}
    out = [r for r in repos if r["name"].lower() not in excluded and not r.get("fork")]
    out.sort(key=lambda r: (r["stargazers_count"], r["updated_at"]), reverse=True)
    return out


def render_projects(repos, cfg):
    """Projects table from live repo data."""
    picked = pick_repos(repos, cfg)[: cfg["max_projects"]]
    if not picked:
        return "_Abhi koi public repo nahi hai. Naya repo banate hi yahan apne aap dikh jayega._"

    lines = [
        "| Project | Description | Tech | Stars |",
        "| :--- | :--- | :---: | ---: |",
    ]
    for r in picked:
        name = r["name"]
        desc = (r.get("description") or "").strip()
        desc = desc.replace("|", "\\|") or "_No description yet._"
        lang = r.get("language") or "—"
        demo = r.get("homepage")
        if demo:
            desc += f' <br/>[Live Demo]({demo})'
        lines.append(
            f'| **[{name}]({r["html_url"]})** | {desc} | `{lang}` | ⭐ {r["stargazers_count"]} |'
        )
    return "\n".join(lines)


def render_skills(repos, cfg):
    """Skill badges derived from languages + topics actually present in repos."""
    langs, topics = {}, {}

    for r in repos:
        lang = r.get("language")
        if lang:
            langs[lang] = langs.get(lang, 0) + 1
        for t in r.get("topics") or []:
            topics[t] = topics.get(t, 0) + 1

    # Config me likhi skills PEHLE dikhti hain, phir auto-detected languages.
    # Ye zaroori hai: GitHub sirf dominant language detect karta hai, isliye
    # ek single-file HTML project me CSS/JS count hi nahi hote.
    ordered = []
    for s in cfg.get("skills", []):
        if s not in ordered:
            ordered.append(s)
    for lang in sorted(langs, key=lambda k: -langs[k]):
        if lang not in ordered:
            ordered.append(lang)

    # extra topic chips
    extra = []
    for lang in langs:
        for t in cfg["topic_rules"].get(lang, []):
            if t not in extra:
                extra.append(t)

    parts = []
    groups = cfg.get("skill_groups") or {}

    def _badge(name):
        color, logo, txt = LANG_BADGES.get(name, ("5B4B8A", "", "white"))
        label = quote(name, safe="")  # "C++" jaise names URL-safe ban jate hain
        if logo:
            return (
                f'<img src="https://img.shields.io/badge/{label}-{color}?style=for-the-badge'
                f'&logo={logo}&logoColor={txt}" alt="{name}" title="{name}" />'
            )
        return (
            f'<img src="https://img.shields.io/badge/{label}-{color}?style=for-the-badge"'
            f' alt="{name}" title="{name}" />'
        )

    if groups:
        # Grouped layout - har category ka apna heading.
        # Config me group ka naam + uske skills, order wahi me dikhenge.
        used = set()
        for gname, items in groups.items():
            badges = [_badge(n) for n in items if n in ordered]
            if not badges:
                continue
            used.update(n for n in items if n in ordered)
            parts.append(f"**{gname}**  \n" + "".join(badges))
        # Jo skill kisi group me nahi hai (repo se auto-detect hua) unhe neeche dikhao
        leftover = [s for s in ordered if s not in used]
        if leftover:
            parts.append(
                "**Also using**  \n" + "".join(_badge(s) for s in leftover)
            )
    elif ordered:
        parts.append("\n".join(_badge(name) for name in ordered))

    # "Learning" - jo seekh rahe ho, wahi alag se
    learning = cfg.get("learning", [])
    if learning:
        parts.append(
            "**Currently learning:** "
            + " ".join(f"`{t}`" for t in learning)
        )

    # repo topics se extra chips
    # Jo topic kisi ALREADY DIKHNE WALE skill ke topic_rules se aaya hai,
    # wo redundant hai (jaise Java badge ke saath "dsa", "oop" chips).
    rule_topics = set()
    for name in ordered:
        for t in cfg["topic_rules"].get(name, []):
            rule_topics.add(t.lower())
    known = {s.lower() for s in ordered} | {"web", "frontend"} | rule_topics
    chips = [t for t in topics if t.lower() not in known]
    chips += [t for t in extra if t.lower() not in known and t not in topics]
    chips = list(dict.fromkeys(chips))[:10]
    if chips:
        parts.append("**Also working with:** " + " ".join(f"`{t}`" for t in chips))

    if not parts:
        return "_Skills apne aap yahan aa jayengi jab aap repos banayenge._"

    return "<br><br>\n\n".join(parts)


def render_stats(username):
    return (
        '<div align="center">\n\n'
        f'<img height="165" src="https://github-readme-stats.vercel.app/api?username={username}'
        '&show_icons=true&theme=radical&hide_border=true&include_all_commits=true" alt="GitHub Stats" />\n\n'
        f'<img height="165" src="https://github-readme-stats.vercel.app/api/top-langs?username={username}'
        '&layout=compact&theme=radical&hide_border=true" alt="Top Languages" />\n\n'
        "</div>"
    )


def render_contact(cfg):
    """Contact block from config.

    SECURITY notes
    --------------
    - Email/phone sirf config se aata hai, code me hard-coded kahin nahi.
    - Koi form ya server nahi - sirf `mailto:` link, jo seedha user ke
      inbox me message bhejta hai. Isliye koi data kisi aur jagah
      store ya leak nahi hota.

    - IMPORTANT: email ko shields.io badge ke TEXT me kabhi nahi daalna.
      Badge text image URL ka hissa hota hai, aur shields.io (a THIRD
      PARTY) usse cache kar leta hai - matlab email unke server par
      chala jayega. Isliye badge sirf "Email" likhta hai, aur asli
      address sirf `mailto:` href me rehta hai jo browser hi handle
      karta hai, koi server nahi.

    - Phone chhupana ho to config me `show_phone` = false kar dein.
      Phone number public karne se scam calls aati hain.
    """
    c = cfg.get("contact", {})
    badges = []

    if c.get("show_email", True) and c.get("email"):
        mail = c["email"]
        badges.append(
            f'<a href="mailto:{mail}">'
            '<img src="https://img.shields.io/badge/Email-EA4335?style=for-the-badge'
            '&logo=gmail&logoColor=white" alt="Email" /></a>'
        )

    # Sirf tab dikhe jab number sahi format me ho.
    # 'X' ya placeholder ho to jhootha number public nahi hoga.
    phone = (c.get("phone_e164") or "").strip()
    phone_ok = phone.startswith("+") and len(phone) >= 10 and "X" not in phone.upper()
    if c.get("show_phone") and phone_ok:
        display = phone
        badges.append(
            f'<a href="tel:{phone.replace("+", "")}">'
            f'<img src="https://img.shields.io/badge/Phone-34A853?style=for-the-badge'
            f'&logo=googlemessages&logoColor=white" alt="Phone" /></a>'
        )
        badges.append(f"<br/>**Phone:** `{display}`")
    elif c.get("show_phone") and phone:
        badges.append(
            "<br/>_Phone number set nahi hua - `automation/config.json` me "
            "`phone_e164` sahi format me daalein._"
        )

    if c.get("show_discussions") and c.get("discussions_url"):
        badges.append(
            f'<a href="{c["discussions_url"]}">'
            '<img src="https://img.shields.io/badge/Discussions-6366F1?style=for-the-badge'
            '&logo=github&logoColor=white" alt="Discussions" /></a>'
        )
        badges.append(
            "<br/>💬 _Sabse behtar tarika: **GitHub Discussions** - wahan message "
            "pata chalta hai aur aapka number/email bilkul safe rehta hai._"
        )

    if c.get("show_linkedin") and c.get("linkedin_url"):
        badges.append(
            f'<a href="{c["linkedin_url"]}">'
            '<img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge'
            '&logo=linkedin&logoColor=white" alt="LinkedIn" /></a>'
        )

    if c.get("show_portfolio") and c.get("portfolio_url"):
        badges.append(
            f'<a href="{c["portfolio_url"]}">'
            '<img src="https://img.shields.io/badge/Portfolio-111111?style=for-the-badge'
            '&logo=googlechrome&logoColor=white" alt="Portfolio" /></a>'
        )

    if not badges:
        return "_Contact details chhupi hain._"

    if c.get("allow_messages", True) and c.get("email"):
        badges.append(
            f'<br/><br/><a href="mailto:{c["email"]}?subject=Contact%20from%20GitHub">'
            '📩 <b>Send me a message</b></a>'
        )
        if c.get("response_time"):
            badges.append(f"\n\n<sub>{c['response_time']}</sub>")

    return "<br>\n".join(badges)


# ---------------------------------------------------------------------------
# sync tasks
# ---------------------------------------------------------------------------


def sync_topics(token, cfg, repos, dry_run):
    """Merge auto topics into every repo. Never deletes existing topics."""
    if not cfg["auto_topics"]:
        return 0
    changed = 0
    for r in repos:
        rules = cfg["topic_rules"].get(r.get("language") or "", [])
        wanted = [t for t in rules if t != r.get("language", "").lower()]
        wanted = [t.lower() for t in wanted]
        if not wanted:
            continue
        try:
            cur = api("GET", f'/repos/{cfg["owner"]}/{r["name"]}/topics', token) or {}
        except ApiError:
            continue
        existing = [t.lower() for t in cur.get("names", [])]
        merged = sorted(set(existing) | set(wanted))
        if merged == sorted(existing):
            continue
        if dry_run:
            print(f"  [dry-run] topics -> {r['name']}: {merged}")
        else:
            api("PUT", f'/repos/{cfg["owner"]}/{r["name"]}/topics', token, {"names": merged})
            print(f"  [ok] topics updated -> {r['name']}: {merged}")
        changed += 1
    return changed


def sync_profile(token, cfg, repos, dry_run):
    """Update profile name / location / bio."""
    if not cfg["auto_bio"]:
        return 0
    try:
        me = api("GET", "/user", token)
    except ApiError as e:
        if not token:
            print("  [skip] profile bio - koi token nahi mila (local run).")
            print("         Actions me ye chalta hai; local me .env check karo.")
        elif "401" in str(e) or "403" in str(e):
            print("  [skip] profile bio - token me 'Profile: write' permission nahi hai.")
            print("         (README aur topics phir bhi update ho rahe hain)")
        else:
            print(f"  [skip] profile bio - {e}")
        return 0

    desired = {
        "name": cfg["profile"]["name"],
        "location": cfg["profile"]["location"],
        "bio": cfg["profile"]["bio"],
    }
    # Recruiters GitHub profile me "hireable" flag dekhte hain.
    # Ye on hone se job invites milne lagte hain.
    if "hireable" in cfg["profile"]:
        desired["hireable"] = bool(cfg["profile"]["hireable"])
    payload = {k: v for k, v in desired.items() if v and me.get(k) != v}
    if not payload:
        return 0
    if dry_run:
        print(f"  [dry-run] profile -> {payload}")
    else:
        api("PATCH", "/user", token, payload)
        print(f"  [ok] profile updated -> {list(payload.keys())}")
    return 1


def sync_readme(token, cfg, repos, username, dry_run):
    """Rewrite AUTO blocks in README and commit if changed."""
    content, sha = get_file(token, cfg["owner"], cfg["profile_repo"], cfg["readme_path"], cfg["branch"])
    if content is None:
        print(f"  ! {cfg['readme_path']} nahi mili - skip")
        return 0

    updated = content
    changed_any = False

    if cfg["auto_projects"]:
        updated, ch = replace_block(updated, "PROJECTS", render_projects(repos, cfg))
        changed_any |= ch
    if cfg["auto_skills"]:
        updated, ch = replace_block(updated, "SKILLS", render_skills(repos, cfg))
        changed_any |= ch
    updated, ch = replace_block(updated, "STATS", render_stats(username))
    changed_any |= ch
    # Sirf ek baar - pehle yahan do duplicate calls the, jo flag ko
    # bypass kar dete thay aur har run me extra commit karte thay.
    if cfg.get("auto_contact", True):
        updated, ch = replace_block(updated, "CONTACT", render_contact(cfg))
        changed_any |= ch

    if not changed_any:
        print("  [ok] README already up to date")
        return 0

    if dry_run:
        print("  [dry-run] README would be updated")
    else:
        put_file(
            token, cfg["owner"], cfg["profile_repo"], cfg["readme_path"],
            cfg["branch"], sha, updated, cfg["commit_message"],
        )
        print("  [ok] README committed")
    return 1


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def load_config():
    path = os.path.join(ROOT, "automation", "config.json")
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            for k, v in user_cfg.items():
                if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                    cfg[k].update(v)
                else:
                    cfg[k] = v
        except Exception as e:
            print(f"! config.json parse nahi hua ({e}) - defaults use ho rahe")
    return cfg


def main():
    # Windows console (cp1252) par emoji/arrow print crash kar dete hain.
    # UTF-8 par force kar dete hain taaki local run bhi smooth ho.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="GitHub profile auto-updater")
    ap.add_argument("--dry-run", action="store_true", help="sirf dikhao, kuch commit mat karo")
    args = ap.parse_args()

    cfg = load_config()
    load_dotenv()  # local run ke liye .env support
    token = os.environ.get("GITHUB_TOKEN", "")
    dry_run = args.dry_run

    print(f"Profile Auto-Manager  |  @{cfg['owner']}")
    print(f"Mode: {'DRY RUN (kuch nahi badlega)' if dry_run else 'LIVE UPDATE'}")
    print("-" * 55)

    read_token = token  # public data bhi token se hi padhte hain (zyada limit)

    try:
        user = api("GET", f'/users/{cfg["owner"]}', read_token)
        repos = api("GET", f'/users/{cfg["owner"]}/repos?per_page=100&sort=updated', read_token) or []
    except ApiError as e:
        print(f"! GitHub API se data nahi mila: {e}")
        return 1

    print(f"  profile : @{user['login']} ({user.get('public_repos', 0)} public repos)")
    print(f"  repos   : {len(repos)} mile")
    print("-" * 55)

    # Har step alag-alag try me hai, taaki ek fail hone par baaki
    # steps chalti rahein aur poora workflow fail na dikhe.
    print("[1/3] Repo topics sync")
    try:
        sync_topics(token, cfg, repos, dry_run)
    except ApiError as e:
        print(f"  [fail] topics sync: {e}")

    print("[2/3] Profile bio/location sync")
    try:
        sync_profile(token, cfg, repos, dry_run)
    except ApiError as e:
        print(f"  [fail] profile sync: {e}")

    print("[3/3] README auto-blocks update")
    try:
        sync_readme(token, cfg, repos, cfg["owner"], dry_run)
    except ApiError as e:
        print(f"  [fail] readme sync: {e}")

    print("-" * 55)
    print("Done." + ("  (dry run - kuch commit nahi hua)" if dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())