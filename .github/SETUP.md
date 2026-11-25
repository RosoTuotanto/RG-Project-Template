# Setting up a new project repository

Every Roso Games project gets its own private repository, made from this baseline. This guide takes a new repository from nothing to ready for its group. What each workflow does is in [AUTOMATION.md](AUTOMATION.md).

The new repository is a copy with its own history, never a fork. A fork carries the baseline's whole commit history; a copy starts with a single commit and belongs only to its project.

## Once per account or organization

The issue types live in the settings of the account or organization that owns the project repositories, so this is done once and then serves every repository there.

### Issue types

The issue forms give each issue a type: Bug, Kysymys, Muu, or Tehtävä. A form can only apply a type that exists.

1. Open the account's or organization's **Settings**.
2. In the sidebar, under "Code, planning, and automation", select **Planning**, then **Issue types**.
3. With **Create new type**, add Kysymys, Muu, and Tehtävä. Bug is one of GitHub's default types.
4. Delete or disable the default types Task and Feature, which no form uses.

## For each new repository

### 1. Create the repository

Use one of these two ways. Never use Fork.

- From GitHub: on the baseline's template repository, https://github.com/RosoTuotanto/RG-Project-Template, click **Use this template**, then **Create a new repository**. Choose the owner, type the project's name, choose **Private**, and click **Create repository from template**.
- From a local copy of the baseline: create an empty private repository on GitHub and clone it. Copy every file and folder of the baseline into the clone, including `.github` and the other names that start with a dot, but not `.git` or `.scratch`. Commit and push to `main`.

### 2. Create the labels

In the **Actions** tab, open **Sync Labels** and click **Run workflow**. Afterwards the repository has exactly the 15 project labels.

Do this before anyone opens an issue. A form applies its label only when the label already exists, and issues opened earlier stay unlabelled.

### 3. Create the project board

The board is a GitHub Projects board made by hand, with five columns and four MoSCoW cards.

1. Open the **Projects** tab of the account or organization that owns the repository and click **New project**.
2. Under "Start from scratch", choose **Board**. Name the project after the repository and click **Create project**.
3. Open the menu in the board's top-right corner and click **Settings**. Edit the options of the **Status** field until they are these five, in this order: PRODUCT BACKLOG (gray), SPRINT BACKLOG (blue), IN PROGRESS (yellow), IN REVIEW (purple), and DONE (green).
4. Back on the board, add four draft items to the PRODUCT BACKLOG column, from top to bottom: `MUST HAVE:`, `SHOULD HAVE:`, `COULD HAVE:`, and `WON'T HAVE:`. They mark the priority levels of the column, and an issue is dragged under the card of its priority.
5. On the repository's main page, click **Projects**, then **Link a project**, and pick the board.

Once one board exists, the next one is quicker to make as a copy. Open the existing board's menu, click **Make a copy**, select the option that copies draft issues, and name the copy after the new repository. The copy has the columns and every draft item of the original, so delete any draft item other than the four cards. It has no repository link, no auto-add workflow, and no collaborators, so step 5 above and sections 4 and 5 below are still done for it.

### 4. Send new issues to the board

A new board is empty, and issues do not land on it by themselves until its workflows are on.

1. Open the board, and in the top-right open the menu and click **Workflows**.
2. In the "Default workflows" list, click **Auto-add to project**, then **Edit**. Under "Filters", select the project repository and type `is:issue` as the filter. Click **Save and turn on workflow**.
3. In the same list, open the workflow that runs when an item is added to the project and click **Edit**. Set the status it gives to PRODUCT BACKLOG and click **Save and turn on workflow**.

Issues that already exist are not added; add those to the board by hand.

### 5. Give the group access

- Give the group's producers and participants write access to the repository.
- Give them write access to the board in the board's **Settings**, under **Manage access**. The board has its own access list, separate from the repository's.
- Connect the repository to the group's `#github` Discord channel.

### 6. Check that it works

1. Open **Issues**, click **New issue**, and expect the five forms: Bug, Kysymys, Muu, Peli-idea, and Tehtävä.
2. Submit one test issue from the Kysymys form. Expect the `kysymys` label and the Kysymys type on it, and the issue in the board's PRODUCT BACKLOG column.
3. Push a commit that adds a `.lua` file with an unused variable. Expect one comment on that commit and the file itself unchanged.
4. Close the test issue and remove the test file.

## Later in the project

- After the pitch meeting and the vote, delete `.github/ISSUE_TEMPLATE/peli_idea.yml`, and add the winning idea's pitch material to `developmentFiles/pitch/`.
- When the group has chosen its game, build its Roso Games template and copy the contents of `dst/<template>/game/` into `game/` and of `dst/<template>/developmentFiles/` into `developmentFiles/`, following [Projektin antaminen ryhmälle](https://github.com/RosoTuotanto/RG-Game-Templates#projektin-antaminen-ryhmälle). Commit it in one commit.
- The Lua report comments on that commit like on any other, addressed to whoever made it.
- The app icon guide for participants is `developmentFiles/images/README.md`.
