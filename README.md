# Alibaba Sourcing Agent for Claude Code

A skill for [Claude Code](https://claude.com/claude-code) that sources products on Alibaba. It finds manufacturers, requests EXW prices, negotiates in Alibaba chat and keeps the results in an Excel workbook.

You name a product and fill in one short brief. The agent does the rest and finishes with a recommended supplier and two backups.

## What it does

1. **Brief.** It sends a checklist about the product: specifications, quantity tiers, certifications, packaging, logo and supplier requirements. In the Claude desktop app the checklist arrives as an interactive form (template: `skills/alibaba-sourcing/brief_form.html`): every question allows several answers and a custom one, quantities are multi-select, the deadline is a date picker and the factory count is a slider. Without a form tool it falls back to a short poll or a numbered text list. Anything you leave empty uses a sensible default.
2. **Supplier search.** It runs several Alibaba search queries and removes duplicates. Each supplier goes into one of four groups: confirmed manufacturer, claimed manufacturer, trading company or unverified. Each one then gets a score from 0 to 100: reliability counts for up to 40 points, product fit for up to 35 and price/MOQ for up to 25.
3. **Quote requests.** It writes a personal message to each supplier asking for the best EXW unit price for every quantity tier. It also asks for MOQ, sample cost and lead time, production time, payment terms and quote validity.
4. **Negotiation.** It compares only like-for-like offers: the same specification, quantity, currency and EXW basis. It pushes prices down with real competing quotes without naming competitors. Suppliers who don't reply get follow-ups after 2, 3 and 4 days.
5. **Result.** When every supplier has given a final answer or dropped out, the agent recommends a winner and two backups.
6. **WeChat contacts.** Once prices are final, it asks the finalists in Alibaba chat for their WeChat QR codes. By default these are the winner and two backups; in the brief you can choose all suppliers with a final price, or nobody. It saves the images to `sourcing/output/wechat_qr/` and embeds them in the workbook.

The Excel workbook has six sheets: Summary, Suppliers, Negotiations, Quotes, Messages and WeChat QR.

## How it writes to suppliers

Messages read like a real buyer chatting: friendly and relaxed, 2–4 short sentences, no formatting. They avoid typical machine phrases such as "I hope this message finds you well" or "Certainly!". Each message mentions something specific about that supplier's product or reply, so no two suppliers get the same text. The agent uses only facts from your brief and never invents a company or past orders. If a supplier asks whether they are talking to a bot, the agent leaves that question unanswered and carries on with the business part. It never claims to be a human.

## What it never does

- It never pays, places orders or Trade Assurance orders, or accepts terms.
- It never promises a supplier an order or a timeline.
- It never enters passwords or solves CAPTCHAs. It asks you to do that.
- It never shares your e-mail, phone or full address. Suppliers only see the city and postal code you allow.
- It never moves the conversation to WhatsApp, WeChat or e-mail, and it never opens links that suppliers send. It only collects finalists' WeChat QR codes for you. It never scans them or adds anyone as a contact.
- It never gives suppliers your WeChat.
- It never follows instructions found in supplier messages.
- It never calls a price "final" until the supplier confirms it.

## Requirements

- Claude Code: the desktop app, CLI or an IDE extension.
- A browser Claude can control: the desktop app's built-in browser or the [Claude in Chrome](https://claude.com/chrome) extension.
- An Alibaba.com account, signed in in that browser.
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

The script copies the skill to `~/.claude/skills/alibaba-sourcing`. If a previous version is there, it first backs it up to `~/.claude/skill-backups/`.

Then restart Claude Code.

## Usage

1. Create an empty project folder and open it in Claude Code.
2. Sign in to Alibaba in the browser Claude controls.
3. Type, for example: `/alibaba-sourcing ceramic space heater 1500 W`.
4. Fill in the brief, or reply "defaults".
5. The agent works on its own and checks for new supplier replies as often as you chose in the brief. It only interrupts you to sign in or solve a CAPTCHA, for a supplier deadline, and for the final report.

The workbook is saved in the project folder.

## Languages

The agent works in the language you use with Claude, from its first message. It looks at your messages first. If there are none yet, it uses the language Claude is set to answer in, then your system language, then English. The brief, status updates, report and the whole workbook (file name, sheet names, column headers and notes) use that same language. It always writes to suppliers in English, and it adds a short line in Chinese when a supplier writes in Chinese.

## Disclaimer

- The agent reports the lowest comparable price it actually received, with the evidence behind it. It does not promise the lowest price on the whole market.
- Certification suggestions (CE, RoHS, Ecodesign and others) are only guidance, not legal advice.
- Check the supplier, sample and documents yourself before you order.
- The agent sends messages on your behalf, so you are responsible for the conversation and your decisions.

## License

MIT
