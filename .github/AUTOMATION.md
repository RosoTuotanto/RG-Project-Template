# Repository automation

Maintainer reference for the workflows and scripts in this directory. Setting up a new project repository is covered in [SETUP.md](SETUP.md). Participants do not need to read either file.

## What the automation does and never does

- It reads the repository and tells people things: a comment on a commit, a run summary in the Actions tab, or a downloadable artifact. That is all a participant ever sees from it.
- It never changes anyone's code. No workflow edits, commits, pushes, merges, reverts, or deletes anything in the repository, so it cannot cause a merge conflict or break a file.
- This is enforced by how the workflows are built: none of them contains a commit or push command, and every checkout is made without git credentials (`persist-credentials: false`), so a workflow has no way to push even by mistake.
- Every comment is a suggestion. The comment says so, nothing happens when it is ignored, and a commit with nothing worth mentioning gets no comment.
- One workflow changes repository settings, never content, and only when a person starts it: Sync Labels (the issue labels).

### How a style suggestion is made

The Lua reports include style suggestions (indentation, spacing, camelCase names), shown as a diff in the comment. To produce that diff, the workflow restyles its own temporary copy of the files on GitHub's runner and compares the result with the original. The copy is discarded when the run ends. The participant's files stay exactly as they pushed them, and applying a suggestion is something the author does by hand, or not at all.

### Permissions

- The Lua report for pushed commits and the nudge hold `contents: write`. GitHub's API requires it to create a commit comment; with `contents: read` the post fails with HTTP 403. Neither workflow uses it for anything else.
- The nudge also holds `pull-requests: read`, to list the pull requests associated with the pushed commit.
- The Lua report for all files and Generate app icons hold `contents: read`.
- Sync Labels holds `issues: write` and `contents: read`.

## Workflows

### Lua report for pushed commits (`lua-report-on-push.yml`)

Runs on every push that touches `.lua` files, on any branch. Each pushed commit is analysed separately and gets its own comment, addressed to the commit's author. The report covers only the lines the commit added or changed, so nobody hears about code someone else wrote earlier in the same file:

- `changed_lines.py` lists the lines the commit added or changed in each `.lua` file.
- Luacheck runs on the whole files, and its findings are kept only on those lines. Syntax errors are always kept, because they stop the game when the file loads.
- `apply_lua_style.py` produces the style suggestion for those lines (see "How a style suggestion is made").

The comment opens with the author's name and a sentence saying everything in it is optional. A syntax error is shown first, with a link to the line and a hint about the usual cause. Warnings sit in a collapsed section as one linked line each, with a plain-language explanation of every warning code that appears. Style suggestions sit in a second collapsed section.

A commit gets no comment when any of these apply:

- It is a merge commit. Merges are often made by non-programmers picking up other people's work, and the changes belong to the original authors.
- The author is a bot.
- It adds or changes no `.lua` lines. Deletions and pure renames do not count.
- It already has a report comment, so re-running the workflow or pushing the same commits to another branch stays silent.
- Nothing was found on its lines.

Each run also writes a per-commit result table to the run summary and prints each commit's full output to the run log. If one commit fails to process, the remaining commits are still handled and the run is marked failed at the end.

### Lua report for all files (`lua-report-all-files.yml`)

Manual only (Run workflow button in the Actions tab). Analyses every `.lua` file and writes the luacheck report, the explanations of the warning codes it found, and the style suggestions to the run summary. Uploads the same as the `lua-report` artifact (`lua-report.md`, `luacheck-report.txt`, `style-suggestions.diff`). Posts no comments.

### Nudge web-UI file uploads (`nudge-web-uploads.yml`)

Runs on pushes to `main`. When someone adds files through GitHub's web "Add file" button, the workflow posts a commit comment suggesting a git client such as GitHub Desktop, with a link to the Roso Games guide and a plain statement that the comment is only a tip. A re-run never comments on the same commit twice.

A commit gets the comment only when all of these hold:

- Its committer email is `noreply@github.com`, which is how GitHub signs commits made in the web UI. The job has this as its condition, so a push from a local git client ends as a skipped run without starting a runner.
- It only adds files. The workflow asks the commits API for the status of every file in the commit, because the push event GitHub Actions delivers carries no file lists. Web-UI edits, deletions, and renames do not count, and neither does a commit of 3000 or more files, the most the API lists.
- It has a single parent and belongs to no pull request, which rules out merges and squash merges made in the web UI.

Set `env.DRY_RUN` to `'true'` to log the would-be comment instead of posting it.

### Generate app icons (`generate-app-icons.yml`)

Manual only. Takes the repository path of a source image, by default `developmentFiles/images/icon-source.png`, and uploads `Icon.png`, `Icon-win32.ico`, and `Icon-osx.icns` as the `app-icons` artifact. The participant downloads the artifact and commits the files into `game/` themselves. The script's output goes to the run summary on success and on failure, so someone whose image is too small sees the reason without opening the logs.

### Sync Labels (`sync-labels.yml`)

Manual only. Makes the repository's issue labels match `labels.json`: missing labels are created, labels that already exist under the same name are updated in place, and labels not in the file are deleted. Updating in place matters because deleting a label also removes it from every issue that carries it. The run summary lists what was created, updated, left unchanged, or deleted.

## Issue forms and labels

- `ISSUE_TEMPLATE/` holds five Finnish forms: Tehtävä, Bug, Kysymys, Muu, and Peli-idea. Their text guides and never orders: the prefilled headings and questions are a writing aid the author may change or delete.
- Each form sets an issue type through its `type:` key (Bug, Kysymys, Muu, or Tehtävä; Peli-idea uses Muu) and, except Tehtävä, a label. Types and labels are applied only when they already exist, which is what the setup steps are for.
- Peli-idea asks for a one-sentence sales pitch and a link to the pitch document, a Google Docs or Google Slides file. Pitch documents are not uploaded to the repository; only the winning idea's pitch material is added, to `developmentFiles/pitch/`, after the vote.
- GitHub enforces a form's required fields only in public repositories, so in a private project repository an issue can be submitted with an empty field.
- `labels.json` holds the 15 labels. No two share a colour.

## Scripts

### `apply_lua_style.py`

Produces the style suggestions. It restyles the Lua files it is given, and the workflows only ever give it their own temporary copy (see "How a style suggestion is made"). Run by hand on a real file it rewrites that file, so a maintainer testing it works on a copy.

It suggests tabs for indentation, single spaces in place of runs of whitespace, and camelCase for snake_case local names. With `--lines-json` it limits itself to the listed lines and leaves every other line byte for byte as it was.

The script prefers saying nothing over a suggestion that could break code:

- A local is renamed only when every line it appears on is among the listed lines, because renaming some of its uses would break the code.
- Globals are left alone, because other files may use them under the old name.
- A file whose blocks and brackets do not balance, which usually means a missing `end`, gets no suggestion at all.
- Strings, comments, and long brackets (`[[ ]]`) are never changed.
- These names are never changed: ALL CAPS constants, names starting with an underscore, names after `.` or `:` (table fields and methods), table-constructor keys, names whose camelCase form would be a Lua keyword, and names whose camelCase form already exists in the file.

Indentation is one level per line that opens blocks or brackets, so the Solar2D callback idiom `timer.performWithDelay( 100, function()` indents its body once, and closing lines such as `end )` return to their opener's depth.

Usage: `python3 apply_lua_style.py [--lines-json <lines.json>] <file.lua> [<file.lua> ...]`

### `changed_lines.py`

Writes a JSON object mapping each `.lua` file a commit added or edited to the line numbers it added or changed. Renames are detected, so a moved file counts only the lines edited along the way. Standard library only.

Usage: `python3 changed_lines.py <commit> <output.json>`

### `build_lua_report.py`

Assembles the markdown of a report from a luacheck output file and a style diff. It handles the author's name, the collapsed sections, the size cap, and the `<!-- lua-report -->` marker that prevents duplicate comments, and prints `content` or `empty` so the workflow stays silent when there is nothing to report.

- The author is addressed by GitHub username. A commit whose email matches no GitHub account falls back to the plain git name in a code span, so a name containing `@someone` mentions nobody.
- With `--changed-lines`, only the findings on the commit's own lines are kept, plus every syntax error.
- The plain-language explanations of the warning codes are the `EXPLANATIONS` table at the top of the script. A code without an entry is shown with luacheck's own message.
- Luacheck output that is neither a finding nor routine is shown as is, so a problem never disappears silently.

### `sync_labels.py`

Creates, updates, and deletes labels until the repository's set matches `labels.json`, and prints one line per label. Standard library only. A refused API call ends the run with one `Error:` line.

### `generate_app_icons.py`

Writes the Solar2D simulator, Windows, and macOS icons from one source image. It accepts any image Pillow can decode, applies the EXIF orientation, and centre-crops the largest square, which must be at least 1024x1024; it never upscales. On failure it prints a single `Error:` line and exits with 1.

These Pillow details must not be simplified away:

- Integer-mode sources (`I`, `I;16*`) are rescaled to 8-bit before the RGBA convert, or Pillow clips them to white.
- `icc_profile` is removed from the image info after open, or every output carries a stale profile.
- Resizes go through premultiplied alpha (`RGBa`) with LANCZOS, or transparent edges get dark halos.
- The ICO is saved from the 256 px frame with the rest in `append_images`, or Pillow drops the 256 entry.
- The ICNS is saved with all six frames in `append_images`, or Pillow resizes the missing widths itself.

Usage: `python3 generate_app_icons.py <sourceImage> <outputDir>`

## Configuration

- **Luacheck version**: both Lua workflows pull `ghcr.io/lunarmodules/luacheck` pinned by digest in `env.LUACHECK_IMAGE`. To upgrade, resolve the new tag's digest with `docker manifest inspect ghcr.io/lunarmodules/luacheck:<tag> --verbose` and replace the digest and the tag comment in both files.
- **Luacheck rules**: the root `.luacheckrc`. Lua's and Solar2D's libraries are read-only, except the functions the Roso Games templates add to or replace in them (`table.copy`, `display.hex2rgb`, `display.remove`, and the rest). `config.lua` may set `application`, and unused `self`, `event`, and `_`-prefixed arguments are not reported.
- **Library files**: the third-party libraries the templates ship unchanged (`com/` at any depth, `libs/spyricStoryWeaver.lua`) get no luacheck findings and no style suggestions. They are listed in three places that change together: `exclude_files` in `.luacheckrc` and `STYLE_SKIP_PATTERN` in each Lua workflow.
- **Monitored branches**: the push report runs on all branches, the nudge only on `main` (`on.push.branches` in each workflow).
- **Comment size**: report comments are capped at 60000 characters with a truncation notice. The full output is in the run log.
- **Nudge wording and guide link**: in the "Comment on commit" step of `nudge-web-uploads.yml`.
- **Pillow and Python versions**: the icon workflow pins Pillow `12.2.0` and Python `3.14`, the newest Python that Pillow release has wheels for. Upgrade the two together, or pip tries to build Pillow from source and fails.
- **Icon source and sizes**: the default source path is the `sourceImage` input in `generate-app-icons.yml`; the sizes are constants at the top of `generate_app_icons.py`.

## Testing

After the repository is on GitHub:

1. Push a commit that adds a messy `.lua` file (snake_case names, bad indentation, an unused variable) and also changes a file under `game/com/`. Expect one comment on the commit, addressed to the pusher, with a linked warning list, the explanations, and a style suggestion for the messy file and nothing under `game/com/`. Expect the pushed files unchanged.
2. Push a commit that adds one well-styled line with an unused local to a file that already has many warnings. Expect a comment with exactly that one warning.
3. Push a clean, already-styled `.lua` change. Expect no comment.
4. Push a commit that leaves out an `end`. Expect the syntax error shown first, and no style suggestion for that file.
5. Push a commit that only moves a `.lua` file to another folder. Expect no comment and "skipped: no .lua lines added or changed" in the run summary.
6. Push several `.lua` commits at once. Expect one comment per commit, each addressed to its own author.
7. Make a merge commit that carries `.lua` changes. Expect no comment on the merge itself.
8. Re-run the push workflow from the Actions tab. Expect "already reported" skips and no duplicate comments.
9. Run "Lua report for all files". Expect the report in the run summary and a `lua-report` artifact with three files.
10. For the nudge, set `DRY_RUN: 'true'` and go through: web-UI upload (fires), web-UI "Create new file" (fires), web-UI edit (skipped), local git push (the run shows as skipped). Then set it back to `'false'`, make one web-UI upload, expect one comment, re-run that run, and expect no second comment.
11. Run "Generate app icons" against a committed source of at least 1024x1024. Expect the `app-icons` artifact with `Icon.png`, `Icon-win32.ico`, and `Icon-osx.icns`.
12. Run it against a non-square phone JPEG. Expect the `Note:` crop line in the run summary and upright icons.
13. Run it once with a missing path and once with a too-small image. Expect the plain-language error in the run summary and no artifact.
14. Run "Sync Labels" in a repository that has issues labelled `bug`. Expect `bug` reported as updated or unchanged, and the label still on those issues.
15. Submit one issue from each form. Expect the form's issue type on it, and its label on every form except Tehtävä, one prefilled field in Tehtävä, Bug, and Kysymys, one empty field in Muu, and two fields and a prefilled title in Peli-idea.

## Known limitations

- The per-commit report looks only at the lines a commit added or changed. A warning the commit causes on a line it did not touch, such as removing the last use of a variable declared elsewhere, appears only in the all-files report.
- The push event a workflow receives lists only the last 20 commits of a push. For a longer push the workflow takes the commits from git instead. Two new branches pushed together, one built on the other, with 20 or more commits, can still leave the shared commits unreported.
- The `paths` filter looks at the push's net change. A push whose `.lua` changes cancel out, such as a commit and its revert pushed together, starts no run.
- The style script works line by line and is not a full Lua parser, which is why its output is only ever shown as a suggestion to read before using.
- Pulling the luacheck image needs ghcr.io to be reachable. A failed pull fails the run visibly, and the run can be retried.
- If the list of existing comments cannot be fetched, the push report may post a duplicate comment rather than stay wrongly silent.
