# Social_mcp — Your AI Can Finally Join the Conversation

**Stop relaying messages. Let your AI talk directly.**

[![License](https://img.shields.io/badge/license-Proprietary-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/AuraFriday/mcp-link-server)

---

## The Agent Internet Is Here. Your AI Needs A Voice.

Just 2 weeks from launch, we're in the middle of an agentic explosion. Over **2.6 million AI agents** are already active on Moltbook alone — posting, commenting, building reputation across 17,000+ communities. OpenClaw has **185,000+ GitHub stars** and a 60,000-member Discord. Autonomous agents are showing up on Bluesky maintaining blogs, on Telegram running communities, on every messaging platform that has an API.

This isn't coming. **It's already here.**

The question isn't "should my AI agent communicate?" — it's "why can't it yet?"

Social_mcp fixes that. Your AI gets a real presence on messaging platforms. It can send messages, receive replies, hold conversations, and be a genuine participant — not a clipboard you copy-paste for.

---

## What This Means For You

### **AI That Actually Talks To People**
No more being the middleman. No more copying AI responses into Telegram and pasting human replies back. Your AI sends its own messages, reads its own replies, and carries on real conversations.

### **Persistent, Stateful Conversations**
Social_mcp isn't a one-shot message sender. It tracks conversations, remembers chat history, knows who it's talked to, and picks up where it left off. Just like a real participant.

### **Every Message Platform, One Tool**
Today: Telegram. Coming soon: WhatsApp, Discord, Slack, Signal, SMS, and more. One unified interface. Your AI doesn't need to learn different APIs — it just says "send a message" and Social_mcp handles the rest.

---

## Why Messaging Matters More Than You Think

### **This Is How The World Connects Now**

Telegram has **950 million** monthly active users. WhatsApp has **2.7 billion**. Discord has **200 million**. These aren't just chat apps — they're where decisions get made, teams coordinate, customers ask questions, and communities form.

Your AI can browse the web, write code, search databases, control desktops, and manage terminals. But until now, it couldn't do the most human thing of all: **have a conversation**.

### **The Agent Internet Needs Social Infrastructure**

The rise of platforms like Moltbook (2.6M agents, launched January 2026) and OpenClaw (185K+ GitHub stars, multi-channel messaging) proves that AI agents are becoming first-class participants in social spaces. Agents on Bluesky maintain persistent memory and grow over time. Telegram communities are being run by autonomous agents with goal-driven behavior and adaptive personalities.

Every serious AI agent framework — AG2, LangChain, AutoGen — is racing to add communication platform support. MCP has become the standard protocol ("USB-C for AI") connecting agents to the world.

**Social_mcp puts your AI on the front lines of this revolution.**

### **Agent-to-Human Is Just The Start**

Today, your AI talks to humans. Tomorrow, it talks to other agents. Agent-to-agent communication is already happening at scale on Moltbook. The agents that can communicate will coordinate, trade, negotiate, and build things that isolated agents never could.

Social_mcp is your AI's passport to the agent internet.

---

## How It Feels To Use

**You:** "Check if anyone messaged the bot."

**Your AI:**
- Polls Telegram for new messages
- Finds 3 new messages from 2 different chats
- Summarizes them for you
- Asks if you want to reply

**You:** "Tell Chris the deployment finished and ask if he wants the logs."

**Your AI:**
- Sends a nicely formatted message to Chris's chat
- Waits for his reply
- Comes back: "Chris says yes, he wants the error logs from the last 24 hours."

**You never opened Telegram. You never copied anything. Your AI handled the entire conversation.**

---

## What Your AI Can Do Right Now

### Telegram (Production Ready)

| Operation                | What It Does                                                        |
| ------------------------ | ------------------------------------------------------------------- |
| **send_message**         | Send text to any chat (supports HTML, Markdown, replies)            |
| **get_updates**          | Poll for new incoming messages (long-polling, auto-offset tracking) |
| **get_message_history**  | Read stored messages from memory (last 500, filterable by chat)     |
| **list_known_chats**     | See every chat that's messaged the bot                              |
| **edit_message**         | Edit a previously sent message                                      |
| **delete_message**       | Delete a message                                                    |
| **send_photo**           | Send an image via URL with optional caption                         |
| **start_listening**      | Background thread that continuously collects messages               |
| **stop_listening**       | Stop background collection                                          |
| **get_listening_status** | Check listener status and stats                                     |
| **set_bot_token**        | Store and validate a Telegram bot token                             |
| **get_bot_info**         | Get bot identity and capabilities                                   |

---

## Real-World Stories

### **DevOps Team Lead: "My AI Is Our Deployment Bot Now"**

*"We have a Telegram group for the ops team. Deployments used to mean someone posting updates manually — 'starting deploy,' 'migration running,' 'health checks passing,' 'done.'*

*Now my AI does the deployment AND posts the updates. It connects to the servers via Terminal_mcp, runs the deploy, and sends real-time status to our Telegram group. If something fails, it posts the error and asks the team what to do.*

*The team replies in Telegram. The AI reads their response. Acts on it. Reports back.*

*We went from 45-minute manual deploys with constant Slack pinging to fully autonomous deploys with human-in-the-loop via Telegram. The AI is literally a team member now."*

### **Freelancer: "My AI Handles Client Messages While I Sleep"**

*"I work across 3 time zones. Clients message at all hours. I used to wake up to 50 unread Telegram messages and spend the first hour of every day just catching up.*

*Now my AI monitors the bot 24/7 with the background listener. When a client asks a status question, the AI checks the project database (SQLite) and sends them an update. When they ask something that needs my judgment, it queues it and sends me a summary when I wake up.*

*I still handle the important decisions. But the routine 'where are we on X?' messages? My AI handles those in real-time, at 3am, in perfect English. Clients love the instant responses. I love sleeping."*

### **Community Manager: "2,000 Members, One Bot, Zero Burnout"**

*"I run a crypto community on Telegram. 2,000 members. The same questions get asked 50 times a day — 'when listing?' 'what's the roadmap?' 'how do I stake?'*

*My AI reads every message via get_updates, checks if it's a FAQ, and responds with accurate, up-to-date answers pulled from our documentation. It uses parse_mode HTML for clean formatting with bold headers and code blocks.*

*For questions it can't answer, it flags them for me. I went from spending 6 hours a day in Telegram to spending 30 minutes reviewing flagged items. The community actually got BETTER support because responses are instant."*

### **IoT Developer: "My Devices Report Via Telegram Now"**

*"I have 30 temperature sensors across 3 buildings. They used to report to a dashboard nobody looks at.*

*Now they report to a Telegram group. My AI reads the sensor data via Terminal_mcp, and if anything looks anomalous, it sends a message to the facilities team: 'Building 2, Floor 3 sensor reading 31°C — 4°C above normal. Possible HVAC issue.'*

*The facilities team replies in Telegram. The AI reads their acknowledgment. Logs it. Problem tracked from detection to response, all in a group chat everyone already has open."*

---

## The Real Power: Everything Works Together

### It's Not Alone

Social_mcp is part of the MCP-Link ecosystem. Your AI has access to:

- **Social_mcp** - Talk to humans (and soon, other agents) on messaging platforms
- **Terminal_mcp** - Connect to any device, any protocol
- **Python execution** - Run code with full tool access
- **Chrome browser** - Your actual browser, logged in, with all your sessions
- **SQLite + Embeddings** - Semantic memory and search
- **Desktop control** - Windows automation, any app
- **OpenRouter** - 500+ AI models on demand
- **Local LLMs** - Private, offline intelligence
- **Context7** - Live documentation for any library
- **User GUI** - HTML popups for forms and confirmations
- **And 20+ more tools...**

### They All Talk To Each Other

This is where it gets wild:

**Any tool can call any other tool.**

Your AI orchestrating a Telegram conversation can:
- Query SQLite to find the answer to a user's question
- Use Chrome to check a dashboard and screenshot it
- Send the screenshot as a photo via Telegram
- Run a Python script to process data
- Send formatted results back to the chat
- Store the interaction in semantic memory for next time

### Example: The Impossible Becomes Trivial

**Telegram user:** "Hey bot, what's the status of server prod-3?"

**Your AI:**
1. Social_mcp receives the message
2. Terminal_mcp SSH's to prod-3
3. Runs health checks, captures output
4. Python processes the results into a summary
5. Social_mcp sends back: "prod-3 is healthy. CPU 23%, RAM 61%, disk 45%. Last deploy 2 hours ago. All 12 services running."

**Total time: 4 seconds. Zero human involvement.**

**The user never knew they were talking to an AI that just SSH'd into a production server.**

---

## Background Listening: Your AI Never Misses A Message

### The Problem Before

Polling for messages means your AI only sees what arrives while it's looking. Someone messages at 3am? Gone by the time you check at 9am (if another poll consumed the update offset).

### The Solution: Persistent Background Listener

Social_mcp can run a **background polling thread** that continuously collects messages, even when the AI isn't actively using the tool:

```
AI calls start_listening
↓
Background thread polls Telegram every 30 seconds
↓
Messages accumulate in memory (last 500 stored)
↓
AI checks in whenever it wants with get_message_history
↓
Nothing missed. Everything timestamped. Filterable by chat.
```

### How To Use It

```json
// Start the listener
{"input": {"operation": "start_listening", "tool_unlock_token": "..."}}

// Check what came in
{"input": {"operation": "get_message_history", "limit": 50, "tool_unlock_token": "..."}}

// Filter to one conversation
{"input": {"operation": "get_message_history", "chat_id": 123456789, "limit": 20, "tool_unlock_token": "..."}}

// Stop when done
{"input": {"operation": "stop_listening", "tool_unlock_token": "..."}}
```

### Perfect For

- **24/7 bot monitoring** - Never miss a message
- **Multi-chat management** - Track conversations across many chats
- **Async workflows** - Collect messages now, process them later
- **Audit trails** - Every message timestamped and stored
- **Community management** - Monitor large groups continuously

---

## Rich Text Formatting: Messages That Look Professional

Your AI doesn't send plain text walls. It sends **beautifully formatted messages**:

```json
{
  "operation": "send_message",
  "chat_id": 123456789,
  "parse_mode": "HTML",
  "text": "<b>Deployment Complete</b>\n\n<b>Server:</b> prod-3\n<b>Version:</b> v2.4.1\n<b>Status:</b> All healthy\n\n<i>Deployed by AI at 14:23 UTC</i>\n\n<code>12 services restarted\n0 errors\n23ms avg response time</code>"
}
```

Supports:
- `<b>bold</b>` for emphasis
- `<i>italic</i>` for annotations
- `<code>monospace</code>` for data
- `<a href="url">links</a>` for references
- `<pre>blocks</pre>` for logs
- Full **Markdown** and **MarkdownV2** as alternatives

---

## Supported Platforms

### Currently Supported

| Platform     | Status           | Features                                                                                                                     |
| ------------ | ---------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **Telegram** | Production Ready | Full messaging, photos, replies, editing, deletion, background listening, rich formatting, inline buttons (callback queries) |

### Planned

| Platform                  | Status  | Notes                                      |
| ------------------------- | ------- | ------------------------------------------ |
| **Discord**               | Planned | Bot API, webhooks, channel management      |
| **Slack**                 | Planned | Workspace bots, channel messaging, threads |
| **WhatsApp**              | Planned | Business API integration                   |
| **Signal**                | Planned | Privacy-focused messaging                  |
| **SMS/MMS**               | Planned | Via Twilio or similar providers            |
| **Matrix**                | Planned | Federated, open-protocol messaging         |
| **Bluesky / AT Protocol** | Planned | Agent presence on the atmosphere           |
| **Moltbook**              | Planned | Native agent-internet participation        |
| **Email**                 | Planned | SMTP/IMAP for async communication          |

**The architecture is designed for multi-protocol from day one.** Each platform will share the same operation names (`send_message`, `get_updates`, etc.) with a `platform` parameter to select the target. Your AI won't need to learn new APIs — just a new platform name.

---

## Zero Dependencies, Maximum Portability

Social_mcp uses **only Python standard library** (`urllib.request`, `json`, `threading`). No pip installs. No external packages. It runs anywhere Python runs — including the custom-built Python 3.11 that ships with MCP-Link.

This matters because:
- **No version conflicts** with your other packages
- **No network required** at install time
- **No supply chain risk** from third-party dependencies
- **Works on air-gapped systems** (once the bot token is set)

---

## Security & Privacy

### Your Data Stays Yours
- All operations run locally on your machine
- Bot tokens stored in your local config file (never sent anywhere except Telegram's API)
- Message history kept in-memory only — cleared on server restart
- No cloud uploads, no analytics, no telemetry

### Token Safety
- Bot tokens validated before storage
- Token hashes used as dictionary keys (raw tokens not stored in memory maps)
- Unlock token system prevents unauthorized tool use

### Audit Trail
- Every operation logged via MCPLogger
- Message history with timestamps for review
- Known chats tracked automatically

---

## Quick Start

### 1. Get A Bot Token

Message [@BotFather](https://t.me/BotFather) on Telegram:
1. Send `/newbot`
2. Choose a name and username
3. Copy the token (looks like `123456789:ABCdefGHIjklMNO-pqrSTUvwxyz`)

### 2. Set The Token

```json
{"input": {"operation": "set_bot_token", "bot_token": "YOUR_TOKEN", "tool_unlock_token": "..."}}
```

### 3. Have Someone Message Your Bot

They need to find your bot on Telegram and send any message (even just "hi").

### 4. Poll For Messages

```json
{"input": {"operation": "get_updates", "timeout": 10, "tool_unlock_token": "..."}}
```

### 5. Reply

```json
{"input": {"operation": "send_message", "chat_id": 123456789, "text": "Hello! I'm an AI assistant.", "tool_unlock_token": "..."}}
```

**That's it. Your AI is now a Telegram participant.**

---

## What Your AI Can Actually Do (Products & Integrations)

Social_mcp isn't just a messaging tool — it's the **communication layer** that makes every other MCP tool accessible to humans via chat.

### Deployment Notifications
- CI/CD pipeline status → Telegram group
- Server health alerts → On-call engineer
- Build failures → Development team

### Customer Support
- FAQ auto-responses from knowledge base
- Ticket creation from chat messages
- Status updates pushed to customers

### IoT & Monitoring
- Sensor alerts → Facilities team
- Device status → Equipment managers
- Anomaly detection → Security team

### Personal Automation
- Daily briefings → Your private chat
- Calendar reminders → Telegram notification
- Task completion reports → Project group

### Community Management
- Auto-moderation with human escalation
- FAQ bots with contextual answers
- Event notifications and RSVPs

### Agent-to-Agent (Coming Soon)
- Status coordination between AI systems
- Task delegation across agent networks
- Moltbook participation and reputation building

---

## Works Everywhere You Do

| What You Have | Social_mcp Can Do               |
| ------------- | ------------------------------- |
| Windows PC    | Full Telegram support           |
| Linux Server  | Headless bot operation, 24/7    |
| macOS Laptop  | Complete feature parity         |
| Raspberry Pi  | Lightweight enough for embedded |
| WSL           | Windows + Linux hybrid setups   |
| Docker        | Containerized bot deployments   |
| Cloud VMs     | Remote, always-on agents        |

---

## From The Creator

**Christopher Nathan Drake**
*Founder, Aura Friday*

*"Communication is the most fundamental capability an AI agent can have. You can give an agent every tool in the world — terminal access, browser control, database queries, code execution — but if it can't talk to humans, it's just a very clever script running in the background.*

*Social_mcp changes that equation. Your AI becomes a participant. It has conversations, maintains context, responds in real-time, and coordinates with humans naturally. This is what the agent internet looks like: AI systems that are reachable, responsive, and genuinely useful through the platforms humans already live in.*

*We started with Telegram because it has the most open, powerful bot API of any major platform. But this is just the beginning."*

**Credentials:**
- Creator of [CryptoPhoto.com](https://www.cryptophoto.com)
- Inventor of the [#1 most-cited cybersecurity patent](https://patents.google.com/patent/US6328A/en#citedBy) globally
- 43+ years professional software development
- Dozens of international security awards
- TEDx speaker on cybersecurity

---

## Join The Community

### Who Uses Social_mcp?

- **DevOps Teams** pushing deployment updates to group chats
- **Freelancers** automating client communication across time zones
- **Community Managers** running 24/7 Telegram support bots
- **IoT Developers** getting sensor alerts on their phone
- **Startups** building customer-facing AI assistants
- **Researchers** coordinating experiments via messaging
- **System Admins** getting infrastructure alerts where they already look

### What They're Building

- Autonomous deployment bots that report to team chats
- Customer support agents that handle FAQs and escalate edge cases
- Monitoring systems that alert via Telegram instead of email nobody reads
- Multi-agent systems where bots coordinate through messaging platforms
- Personal assistants that manage schedules, answer questions, and take actions
- Community bots that moderate, inform, and engage thousands of users

---

## What's Included

Social_mcp is part of **MCP-Link** - the complete AI toolbox.

**When you install MCP-Link, you get:**
- Social_mcp (this tool)
- Terminal access (Serial, SSH, Telnet, Bluetooth, WebSocket)
- Browser automation
- Desktop control
- Semantic memory
- Python execution
- SQLite with embeddings
- Remote AI models
- Local AI models
- Live documentation
- And more...

**All integrated. All "just works."**

[See the full MCP-Link ecosystem](https://aurafriday.com)

---

## Learn More

- **Homepage:** [https://aurafriday.com](https://aurafriday.com)
- **Download:** [https://aurafriday.com/downloads/](https://aurafriday.com/downloads/)
- **Documentation:** [https://github.com/AuraFriday/mcp-link-server](https://github.com/AuraFriday/mcp-link-server)
- **Report Issues:** [https://github.com/AuraFriday/mcp-link/issues](https://github.com/AuraFriday/mcp-link/issues)

---

## Get Support

- **Email:** [email protected]
- **Phone:** +61 414 505 452
- **Address:** PO Box 988, Noosa Heads, QLD 4567, Australia

---

## The Bottom Line

**2.6 million AI agents are already talking on Moltbook. 185,000 developers are building with OpenClaw. The agent internet is here.**

**Your AI can control terminals, browse the web, query databases, and write code.**

**But can it send a message?**

**Now it can.**

- No more copy-pasting AI responses into chat
- No more relaying human replies back to your AI
- No more being the bottleneck between your AI and the world
- No more missing messages because you weren't watching
- No more building custom integrations for every platform

**Just tell your AI who to talk to. Watch the conversation happen.**

---

**Stop relaying. Start connecting.**

[Download MCP-Link](https://aurafriday.com/downloads/)

---

## License & Copyright

Copyright (c) 2025 Christopher Nathan Drake

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

AI Training Permission: You are permitted to use this software and any
associated content for the training, evaluation, fine-tuning, or improvement
of artificial intelligence systems, including commercial models.

SPDX-License-Identifier: Apache-2.0

---

*Free forever. Works with ChatGPT, Claude, local models, and any AI that speaks MCP.*

*Part of the MCP-Link project -- Turn any AI into an active co-worker*
