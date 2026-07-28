# Tech Revision Notes

My interview-prep notes (Spring, JPA/Hibernate, Security/JWT, microservices,
Kafka, Docker, Redis, testing, design patterns, system design, plugin
architecture) published as a small static website so I can read them on my
phone from anywhere.

- **Notes** live as plain `.txt` / `.md` files under the topic folders
  (`Month1/`, `Month2/`, `PluginArchitecture/`, `Solid7DesignPatterns/`,
  `SystemDesign/`, …). These are the source of truth and are never modified.
- **`revision-notes/build.py`** reads those notes and generates the HTML site.
- **GitHub Actions** rebuilds and republishes the site automatically on every
  push, so I never have to build or commit HTML by hand.

---

## 📱 Read it online

Once Pages is enabled (steps below), the site is at:

```
https://<your-username>.github.io/<your-repo-name>/
```

Bookmark that on your phone.

---

## One-time setup: publish to GitHub Pages

The local Git repo is already initialised with a first commit. To put it online:

1. **Create an empty repo on GitHub** (no README/.gitignore — this repo already
   has them). Note: with a free GitHub account, Pages requires the repo to be
   **public**. If these notes must stay private, GitHub Pages needs a paid plan.

2. **Connect it and push** (run from this folder — replace the URL):

   ```bash
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```

3. **Turn on Pages:** on GitHub go to **Settings → Pages → Build and deployment
   → Source** and choose **GitHub Actions**. Do this right after creating the
   repo (ideally before, or immediately after, the first push).

4. Open the **Actions** tab and wait for the "Deploy notes site to GitHub Pages"
   run to finish (~1 minute). Your link appears at the top of the deploy step
   and under Settings → Pages.

   > If your very first run fails on the deploy step because Pages wasn't enabled
   > yet, just enable it (step 3) and re-run the workflow from the **Actions** tab
   > (the run has a **Re-run jobs** button; the workflow also supports manual
   > "Run workflow").

That's it. From now on the site updates itself whenever you push.

---

## Adding or editing notes later

**From your computer:** drop a new `.txt`/`.md` into any topic folder (or edit
an existing one), then:

```bash
git add -A
git commit -m "Add note"
git push
```

The Action rebuilds and the live site updates in about a minute.

**From your phone:** open the repo on github.com, navigate into a topic folder,
tap **Add file → Create new file** (or the pencil to edit), commit — same result.

You can add whole new topic folders too; they show up on the site automatically.
Nested `Topic/Week/note.txt` and flat `Topic/note.txt` layouts both work.

---

## Preview locally (optional)

You only need Python 3 — no packages to install.

```bash
python revision-notes/build.py     # generate the HTML
python revision-notes/serve.py     # serve at http://localhost:8000/
```

`build.py` only ever reads your notes; it writes the generated HTML into
`revision-notes/` (which is git-ignored — CI regenerates it).
