# Chicago Public Sector Sales Board

A single self-contained web page listing 509 sales openings in Chicago and Illinois,
scored on the experience each posting actually asks for and on who signs the contract.

Everything is in `index.html`. No build step, no dependencies, no server code. The only
external request is to Google Fonts, and the page falls back to system fonts if that is
blocked.

---

## What is in this folder

| File | What it is | Who should see it |
|---|---|---|
| `index.html` | The shareable site. 509 roles. No CRM data, no names. | Anyone you send the link to |
| `index-internal.html` | Same page plus the 832-company warm-intro table pulled from HubSpot, with joint deal counts and HubSpot record links. | You only. Do not host this publicly. |

`index-internal.html` is included so you have one file with everything. If you publish it
by mistake, you are publishing DeepWalk's partner relationship data. Keep it local, or
host it somewhere access-controlled.

---

## Deploy to GitHub Pages

### Read this first

**A free GitHub account can only serve Pages from a public repository.** Public means the
repo and the site are visible to anyone who finds the URL. The page carries a
`noindex, nofollow` tag so search engines should skip it, but that is a request, not a
lock, and the URL itself is shareable by anyone who has it.

That is probably fine here: the page names no individual and contains no CRM data. But if
you want it genuinely private, see **Keeping it private** at the bottom.

### Option A: no terminal, all in the browser

1. Go to <https://github.com/new>. Name the repo something neutral like `chi-sales-board`.
   Set it to **Public**. Do not add a README. Click **Create repository**.
2. On the empty repo page, click **uploading an existing file**.
3. Drag `index.html` in. Commit straight to `main`.
4. Go to **Settings → Pages**.
5. Under **Build and deployment**, set Source to **Deploy from a branch**, branch to
   **main**, folder to **/ (root)**. Click **Save**.
6. Wait about a minute, then reload that Settings → Pages screen. Your URL appears at the
   top: `https://<your-username>.github.io/chi-sales-board/`

That URL is the link you share.

### Option B: from a terminal, or by asking Claude Code to run it

Put `index.html` in an empty folder, then from inside that folder:

```bash
git init -b main
git add index.html
git commit -m "Chicago public sector sales board"

# create the repo and push. needs the GitHub CLI: https://cli.github.com
gh repo create chi-sales-board --public --source=. --remote=origin --push

# turn on Pages from the main branch root
gh api -X POST repos/:owner/chi-sales-board/pages \
  -f "source[branch]=main" -f "source[path]=/"

# print the live URL once it builds (give it a minute)
gh api repos/:owner/chi-sales-board/pages --jq .html_url
```

If you do not have the GitHub CLI, create the empty repo in the browser first, then:

```bash
git init -b main
git add index.html
git commit -m "Chicago public sector sales board"
git remote add origin https://github.com/<your-username>/chi-sales-board.git
git push -u origin main
```

Then enable Pages through Settings → Pages as in Option A, steps 4 to 6.

### Updating it later

Replace `index.html` and push again. Pages redeploys in about a minute at the same URL.

```bash
git add index.html
git commit -m "Refresh listings"
git push
```

---

## Faster alternatives

**Netlify Drop** — <https://app.netlify.com/drop>. Drag the folder onto the page and you
get a live URL in seconds. Claim it with a free account or it expires. Netlify also lets
you rename the subdomain and add a custom domain on the free tier.

**Cloudflare Pages** — <https://pages.cloudflare.com>. Connect the GitHub repo, or use
`npx wrangler pages deploy .` from the folder. Free, fast, and Cloudflare Access can put
a login in front of it (see below).

**No hosting at all** — `index.html` works when opened directly from disk. Email it, drop
it in Slack, or put it on a shared drive. Double-clicking it opens the full working page.
The one thing that changes is that some browsers block local-file storage, so the status
column may not save between opens. The page detects this and says so in the footer.

---

## Keeping it private

If you would rather not have a public URL:

- **Cloudflare Pages plus Cloudflare Access** puts an email-code login in front of the
  site. Free for up to 50 users and the closest thing to a private link.
- **Netlify password protection** is a paid plan feature.
- **GitHub Pages from a private repo** requires GitHub Pro, Team or Enterprise.
- **Send the file instead of a link.** For two people, this is honestly the simplest
  answer and leaks nothing.

---

## Notes on the page itself

- **Opening screen.** The page opens on a choice between Stephen and Frank. Each has their
  own set of statuses and star ratings on the same 509 roles, and the card shows a summary
  of what that person has tracked so far. Switch person from the "Tracking for" button in
  the filter bar or the link in the footer.
- **Status and rating** live on every row: a status dropdown (Interested, Applied,
  Interviewing, Offer, Passed) and a five-star rating. Click the current star again to clear
  it. Filter chips for status and for minimum rating sit next to the person button, and the
  sort menu has a "my rating" order.
- **Where it is stored.** Marks are shared through a small Supabase database (project
  `chi-sales-board` in the Apex Adventure Alliance organization, table `public.marks`), so both
  of you see the same statuses and ratings on any device and changes appear live. The browser
  keeps a local copy as a cache and offline fallback; the footer says "shared, live" when the
  connection is up. **Export tracking** writes both sets to a JSON file as a backup and **Import
  tracking** merges one back in; newer marks win everywhere, including on the server.
- **Database setup.** `db/schema.sql` is the table, row-level security and the newer-wins trigger.
  `db/setup_supabase.py` creates the project from a Supabase access token, applies the schema and
  writes the URL and anon key into `website/index.html`. The anon key in the page can only read
  and write the marks table. The Postgres password is in the 1Password item
  "chi-sales-board supabase".
- **Postings expire.** Everything was compiled on 10 September 2026, with 52 resume-matched roles added on 11 September. Confirm any role is
  still open before spending real time on it.
- **Filters** live in the sticky bar: seniority band, tier, buyer type, sector, location,
  plus toggles for published pay, confirmed-open requisitions, and roles that were filtered
  out. Every filtered role shows the reason it was filtered.
- **Dark mode** follows the viewer's system setting.
- **Phone width** is supported down to 400px.
