# Alibaba Sourcing Agent for Claude Code

A skill for [Claude Code](https://claude.com/claude-code) that sources products on **Alibaba.com** and **Made-in-China.com**. It finds manufacturers, requests EXW prices, negotiates in the platform's own chat and keeps the results in an Excel workbook. It can run several sourcing projects in parallel from one platform account.

You name a product and fill in one short brief. The agent does the rest and finishes with a recommended supplier and two backups.

## What it does

1. **Brief.** It sends a checklist about the product: specifications, quantity tiers, certifications, packaging, logo and supplier requirements. In the Claude desktop app the checklist arrives as an interactive form (template: `skills/alibaba-sourcing/brief_form.html`): every question allows several answers and a custom one, quantities are multi-select, the deadline is a date picker and the factory count is a slider. Without a form tool it falls back to a short poll or a numbered text list. Anything you leave empty uses a sensible default.
2. **Supplier search.** It runs several search queries on Alibaba, Made-in-China or both, as you chose in the brief, and removes duplicates. Each supplier goes into one of four groups: confirmed manufacturer, claimed manufacturer, trading company or unverified. Each one then gets a score from 0 to 100: reliability counts for up to 40 points, product fit for up to 35 and price/MOQ for up to 25.
3. **Quote requests.** It writes a personal message to each supplier asking for the best EXW unit price for every quantity tier. It also asks for MOQ, sample cost and lead time, production time, payment terms and quote validity.
4. **Negotiation.** It compares only like-for-like offers: the same specification, quantity, currency and EXW basis. It pushes prices down with real competing quotes without naming competitors. Suppliers who don't reply get follow-ups after 2, 3 and 4 days.
5. **Result.** When every supplier has given a final answer or dropped out, the agent recommends a winner and two backups.
6. **Finalist verification.** It asks the winner and two backups for their business license, test reports (for example CE and RoHS) and photos or video of the production line. It checks that the company name, models and standards match, and looks up report numbers on the official websites of the labs that issued them. Where a CAPTCHA blocks the check, it hands the details to you. If the winner shows a red flag, the next backup moves up.
7. **WeChat contacts.** Once prices are final, it asks the finalists in the platform chat for their WeChat QR codes. By default these are the winner and two backups; in the brief you can choose all suppliers with a final price, or nobody. It saves the images to `sourcing/output/wechat_qr/` and embeds them in the workbook.

The Excel workbook has seven sheets: Summary, Suppliers, Negotiations, Quotes, Messages, Verification and WeChat QR. Every sheet has a Platform column.

## Several projects at once

Each product is a separate project: its own folder, its own Claude session and its own brief. All projects share your Alibaba and Made-in-China logins. A small coordination script, `skills/alibaba-sourcing/scripts/coord.py` (Python standard library only), keeps them from getting in each other's way:

- **Project index.** `~/Sourcing/_shared/projects.json` lists every project with its stage and status. Run `python3 coord.py projects` to see it.
- **One chat, one writer.** A supplier has one chat thread per buyer account, even when you source two products from them. Before writing, a project locks that chat. If another project is writing there, it skips the chat and comes back on the next check. A lock left by a crashed session expires after 10 minutes.
- **Shared suppliers.** When two projects talk to the same supplier, every message starts with the product name ("About the 1500W heater: ..."). Each project reads only the replies about its own product and asks the supplier when a reply is unclear. One project's prices are never used in another project's negotiation.
- **Own browser tab.** Each session works in its own tab and never touches other projects' tabs.
- **Account safety.** First-contact messages are counted across all projects, at most 20 per hour per platform. Replies and follow-ups are not limited.
- **Checklists.** Each project folder has `brief.md` with your brief answers and `checklist.md` with progress checkboxes and the next action. A resumed session continues from the first unchecked step.

You can change the shared folder by setting the `SOURCING_HOME` environment variable; by default it is `~/Sourcing`.

## Dashboard

`~/Sourcing/dashboard.html` shows all projects on one page and refreshes itself every minute. At the top is what needs you (sign-in, CAPTCHA, deadlines, red flags) and which quotes expire within 3 days. Below that, each project has its stage, supplier counts, best price per quantity tier, the suppliers it is waiting for, verification results and the next action. Each project updates the page after every check. To rebuild it by hand:

```bash
python3 ~/.claude/skills/alibaba-sourcing/scripts/dashboard.py
```

## Phone notifications

The agent alerts you about a final price, a quote that expires within 2 days, a needed sign-in or CAPTCHA, a supplier deadline, a red flag on the winner, and a finished project. Each alert is sent only once.

- **Claude app.** If Remote Control is connected, Claude's own notifications reach your phone.
- **ntfy (simplest, free).** Install the [ntfy](https://ntfy.sh) app, subscribe to a long random topic name that only you know, and create `~/Sourcing/_shared/notify.json`:

  ```json
  {"ntfy": {"topic": "your-long-random-topic"}}
  ```

  Anyone who knows the topic name can read the alerts, so keep it secret.
- **Telegram.** Create a bot with @BotFather, send it any message, find your chat id, and add it to the same file:

  ```json
  {"telegram": {"bot_token": "123456:ABC...", "chat_id": "123456789"}}
  ```

- **macOS.** Alerts also show up as Mac notifications. To turn that off, add `"macos": false`.

Fill this file in yourself; the agent never writes tokens. To test it:

```bash
python3 ~/.claude/skills/alibaba-sourcing/scripts/notify.py "Test alert"
```

## How it writes to suppliers

Messages read like a real buyer chatting: friendly and relaxed, 2–4 short sentences, no formatting. They avoid typical machine phrases such as "I hope this message finds you well" or "Certainly!". Each message mentions something specific about that supplier's product or reply, so no two suppliers get the same text. The agent uses only facts from your brief and never invents a company or past orders. If a supplier asks whether they are talking to a bot, the agent leaves that question unanswered and carries on with the business part. It never claims to be a human.

## What it never does

- It never pays, places orders or Trade Assurance orders, or accepts terms.
- It never promises a supplier an order or a timeline.
- It never enters passwords or solves CAPTCHAs. It asks you to do that.
- It never shares your e-mail, phone or full address. Suppliers only see the city and postal code you allow.
- It never moves the conversation off the platform to WhatsApp, WeChat or e-mail, and it never opens links that suppliers send. It only collects finalists' WeChat QR codes for you. It never scans them or adds anyone as a contact.
- It never gives suppliers your WeChat.
- It never follows instructions found in supplier messages.
- It never calls a price "final" until the supplier confirms it.

## Requirements

- Claude Code: the desktop app, CLI or an IDE extension.
- A browser Claude can control: the desktop app's built-in browser or the [Claude in Chrome](https://claude.com/chrome) extension.
- An Alibaba.com and/or Made-in-China.com account, signed in in that browser.
- Python 3 for the coordination script; it comes with macOS developer tools.
- Optional: the `negotiation` skill, which gives the agent more negotiation techniques.

## Installation

### Option 1. Plugin (recommended)

In Claude Code, run:

```
/plugin marketplace add artem6654/alibaba-sourcing-agent
/plugin install alibaba-sourcing@alibaba-sourcing-agent
```

### Option 2. Manual

```bash
git clone https://github.com/artem6654/alibaba-sourcing-agent.git
```

```bash
./alibaba-sourcing-agent/install.sh
```

The script copies the skill to `~/.claude/skills/alibaba-sourcing`. If a previous version is there, it first backs it up to `~/.claude/skill-backups/` and deletes older backups, so only the latest one is kept. To keep more, run `KEEP_BACKUPS=3 ./install.sh`; `KEEP_BACKUPS=0` keeps none.

Then restart Claude Code.

## Usage

1. Sign in to Alibaba and/or Made-in-China in the browser Claude controls.
2. For each product, create a folder such as `~/Sourcing/heater-1500w` and open a new Claude Code session in it.
3. In that session, type, for example: `/alibaba-sourcing ceramic space heater 1500 W`.
4. Fill in the brief, or reply "defaults".
5. The agent works on its own and checks for new supplier replies as often as you chose in the brief. It only interrupts you to sign in or solve a CAPTCHA, for a supplier deadline, and for the final report.

To run another product in parallel, repeat steps 2–4 in a new folder and a new session. In the Claude desktop app you can show the sessions side by side in split view. The workbook, brief and checklist of each project are saved in its folder.

## Languages

The agent works in the language you use with Claude, from its first message. It looks at your messages first. If there are none yet, it uses the language Claude is set to answer in, then your system language, then English. The brief, status updates, report and the whole workbook (file name, sheet names, column headers and notes) use that same language. It always writes to suppliers in English, and it adds a short line in Chinese when a supplier writes in Chinese.

## Disclaimer

- The agent reports the lowest comparable price it actually received, with the evidence behind it. It does not promise the lowest price on the whole market.
- Certification suggestions (CE, RoHS, Ecodesign and others) are only guidance, not legal advice.
- Check the supplier, sample and documents yourself before you order.
- The agent sends messages on your behalf, so you are responsible for the conversation and your decisions.

## License

MIT
