"""Create the shared-tracking Supabase project for the sales board and wire the page to it.

Needs a Supabase personal access token (sbp_...) with access to the organization that owns
the Apex Web Maps project. Provide it one of these ways:
    SUPABASE_ACCESS_TOKEN=sbp_...  python db/setup_supabase.py
    python db/setup_supabase.py --op "op://Employee/Supabase apex/password"

Steps: find the organization that owns the Apex project -> create project "chi-sales-board"
(free plan, same region) -> wait until healthy -> run db/schema.sql -> fetch the anon key ->
write the URL and anon key into website/index.html. Nothing secret is written to disk; the
database password is stored in 1Password if `op` is available, otherwise printed once.

Re-running is safe: an existing project named chi-sales-board is reused.
"""
import argparse, json, os, secrets, subprocess, sys, time, urllib.request, urllib.error, io, re, string

API = "https://api.supabase.com/v1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "website", "index.html")
SCHEMA = os.path.join(ROOT, "db", "schema.sql")
APEX_REF = "lcenhesezodgrjrymngg"
NAME = "chi-sales-board"


def api(token, method, path, body=None):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            txt = r.read().decode()
            return json.loads(txt) if txt else None
    except urllib.error.HTTPError as e:
        sys.exit("%s %s -> HTTP %d: %s" % (method, path, e.code, e.read().decode()[:300]))


def get_token(args):
    tok = os.environ.get("SUPABASE_ACCESS_TOKEN", "")
    if not tok and args.op:
        tok = subprocess.run(["op", "read", args.op], capture_output=True, text=True).stdout.strip()
    if not tok.startswith("sbp_"):
        sys.exit("No usable token. Set SUPABASE_ACCESS_TOKEN or pass --op with a 1Password reference to an sbp_ token.")
    return tok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--op", help="1Password secret reference for the sbp_ token")
    ap.add_argument("--org", help="organization id to use (default: the one that owns the Apex project)")
    ap.add_argument("--region", help="region (default: same as the Apex project)")
    args = ap.parse_args()
    tok = get_token(args)

    projects = api(tok, "GET", "/projects")
    apex = next((p for p in projects if p["id"] == APEX_REF), None)
    org = args.org or (apex and apex["organization_id"])
    region = args.region or (apex and apex["region"]) or "us-east-1"
    if not org:
        orgs = api(tok, "GET", "/organizations")
        sys.exit("Apex project not visible to this token. Pass --org. Organizations: " + json.dumps(orgs))
    print("organization:", org, "| region:", region)

    proj = next((p for p in projects if p["name"] == NAME and p["organization_id"] == org), None)
    if proj:
        print("reusing existing project", proj["id"])
    else:
        alphabet = string.ascii_letters + string.digits
        db_pass = "".join(secrets.choice(alphabet) for _ in range(32))
        proj = api(tok, "POST", "/projects", {"name": NAME, "organization_id": org, "region": region,
                                              "db_pass": db_pass})
        print("created project", proj["id"])
        stored = False
        try:
            r = subprocess.run(["op", "item", "create", "--category=login", "--vault=Employee",
                                "--title=chi-sales-board supabase",
                                "username=https://%s.supabase.co" % proj["id"], "password=" + db_pass,
                                "notesPlain=Postgres password for the chi-sales-board Supabase project (org %s). Created by db/setup_supabase.py." % org],
                               capture_output=True, text=True)
            stored = r.returncode == 0
        except FileNotFoundError:
            pass
        if stored:
            print("database password stored in 1Password item 'chi-sales-board supabase'")
        else:
            print("DATABASE PASSWORD (store it now, it is not saved anywhere else):", db_pass)

    ref = proj["id"]
    for _ in range(60):
        p = api(tok, "GET", "/projects/" + ref)
        status = p.get("status")
        print("  status:", status)
        if status == "ACTIVE_HEALTHY":
            break
        time.sleep(10)
    else:
        sys.exit("project did not become healthy in time; re-run to continue")

    sql = io.open(SCHEMA, encoding="utf-8").read()
    api(tok, "POST", "/projects/%s/database/query" % ref, {"query": sql})
    print("schema applied")

    keys = api(tok, "GET", "/projects/%s/api-keys?reveal=true" % ref)
    anon = next((k["api_key"] for k in keys if k.get("name") == "anon"), None) or \
           next((k["api_key"] for k in keys if k.get("type") == "publishable"), None)
    if not anon:
        sys.exit("could not find the anon/publishable key: " + json.dumps([k.get("name") for k in keys]))
    url = "https://%s.supabase.co" % ref

    page = io.open(PAGE, encoding="utf-8").read()
    page, n1 = re.subn(r'var SB_URL\s*=\s*"[^"]*";', 'var SB_URL = "%s";' % url, page)
    page, n2 = re.subn(r'var SB_ANON\s*=\s*"[^"]*";', 'var SB_ANON = "%s";' % anon, page)
    if n1 != 1 or n2 != 1:
        sys.exit("could not find the SB_URL / SB_ANON lines in the page")
    io.open(PAGE, "w", encoding="utf-8", newline="\n").write(page)
    print("page wired to", url)
    print("done. Commit website/index.html and push to publish.")


if __name__ == "__main__":
    main()
