# Username Checker

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Release](https://img.shields.io/badge/Release-1.0.6-brightgreen.svg)
![Discord](https://img.shields.io/badge/Discord-Webhook-blueviolet.svg)

A desktop tool for bulk username availability checking and real-time username monitoring across multiple platforms, with Discord notifications and proxy support.

---

## Features

- **Bulk Username Checking** — Check hundreds of usernames across multiple platforms simultaneously
- **Sniper Monitor** — Real-time monitoring of a target username; get notified the moment it becomes available
- **Multi-Platform Support** — Pinterest, Instagram, and GitHub
- **Discord Webhook Notifications** — Instant alerts when a username becomes available
- **Proxy Rotation** — Built-in proxy management with blacklist support and SOCKS5 compatibility
- **Export Results** — Save available usernames to file
- **Customizable Settings** — Configure threads, timeouts, delays, and platform selection
- **Clean UI** — Dark-themed interface built with Tkinter

---

## Supported Platforms

| Platform  | Max Length | Allowed Characters                    | Restrictions                              |
|-----------|-----------|----------------------------------------|-------------------------------------------|
| Pinterest | 3–30      | Letters, numbers, underscores          | Cannot be all numbers                     |
| GitHub    | 39        | Letters, numbers, hyphens              | No leading/trailing/consecutive hyphens   |
| Instagram | 30        | Letters, numbers, periods, underscores | No leading/trailing/consecutive periods   |

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip

### Setup

**1. Clone the repository:**

```bash
git clone https://github.com/00ie/username-checker.git
cd username-checker
```

**2. Install dependencies:**

```bash
pip install -r requirements.txt
```

> The `requirements.txt` includes `requests[socks]` for SOCKS5 proxy support. To install it separately:
> ```bash
> pip install requests[socks]
> ```

**3. Configure proxies (optional):**

Create a `proxies.txt` file inside the `username checker/` folder (created automatically on first run). Add one proxy per line. Supported formats:

```
host:port
user:pass@host:port
http://host:port
socks5://host:port
```

The app includes a built-in proxy manager accessible from the GUI. Proxies that fail validation are added to `bad_proxies.txt` and highlighted in red.

**4. Configure Discord webhook (optional):**

Edit `config/settings.json` and add your webhook URL:

```json
{
    "webhook_url": "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE"
}
```

---

## Usage

### Running the Application

```bash
python main.py
```

### Bulk Checker

1. Select the platforms to check from the sidebar
2. Set the number of usernames to generate and their desired length
3. Click **GENERATE LIST** to create random usernames
4. Click **START CHECKING** to begin
5. Available usernames appear highlighted in green in the console
6. Click **EXPORT RESULTS** to save them

### Sniper Monitor

1. Switch to the **SNIPER MONITOR** tab
2. Enter the target username
3. Set the check interval in seconds (default: 60)
4. Click **ACTIVATE SNIPER** to start monitoring
5. The tool will continuously poll until the username becomes available, then send a Discord notification

---

## Configuration

Edit `config/settings.json` to customize behavior:

```json
{
    "threads": 5,
    "timeout": 10,
    "webhook_url": "",
    "use_proxies": false,
    "jitter_min": 0.5,
    "jitter_max": 1.5,
    "platforms": {
        "instagram": true,
        "github": true,
        "pinterest": true
    }
}
```

| Option                    | Description                                          |
|---------------------------|------------------------------------------------------|
| `threads`                 | Number of concurrent checking threads                |
| `timeout`                 | HTTP request timeout in seconds                      |
| `webhook_url`             | Discord webhook URL for notifications                |
| `use_proxies`             | Enable or disable proxy rotation                     |
| `jitter_min` / `jitter_max` | Random delay range between requests (seconds)      |
| `platforms`               | Enable or disable individual platforms               |

---

## Project Structure

```
username-checker/
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── config/
│   ├── settings.json
│   ├── settings.py
│   ├── theme_manager.py
│   └── __init__.py
│
├── core/
│   ├── engine.py
│   ├── platforms.py
│   ├── proxy_checker.py
│   ├── validation.py
│   └── __init__.py
│
├── gui/
│   ├── app_window.py
│   ├── ui_components.py
│   ├── widgets.py
│   └── __init__.py
│
├── utils/
│   ├── animations.py
│   ├── cache.py
│   ├── database.py
│   ├── logger.py
│   ├── notifications.py
│   ├── validators.py
│   └── __init__.py
│
├── assets/
├── data/
├── exports/
├── logs/
└── username checker/
```

---

## Discord Notifications

When a username becomes available, the webhook sends an embed containing:

- The username
- Platforms where it is available
- Direct links to claim
- Timestamp of discovery

---

## Accuracy Tips

- Use a valid Instagram `sessionid` in Settings for better precision
- Increase `jitter_min` / `jitter_max` when rate-limited
- Reduce concurrent threads for Instagram-heavy runs
- Use healthy rotating proxies
- Re-check critical usernames before a final decision

---

## Known Limitations

- Instagram checks can become unstable due to anti-bot behavior, endpoint changes, and temporary restrictions
- Without authentication context, Instagram may return uncertain states more often
- Rate limits can reduce precision and increase `Possibly Available` results

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Too many `Taken` / `Possibly Available` | Increase delay, reduce threads, rotate proxies, retry later |
| Rate limit popup appears | Pause checks, increase jitter, wait for cooldown, then retry |
| Webhook not sending | Validate webhook URL and check network access |
| Different title bar behavior by OS | Expected — depends on your window manager or macOS Tk version |

---

## OS Support

| OS      | Status               |
|---------|----------------------|
| Windows | Full support, best visual integration |
| macOS   | Supported  |
| Linux   | Supported  |

---

## Privacy

- Proxy, session, and runtime files are stored locally
- Sensitive local artifacts are excluded via `.gitignore`
- Review `config/settings.json` before publishing if you changed local values

---

## Changelog

### 1.0.6
- **Instagram robustness** — Multiple fallback methods (API endpoint, HTML profile, mobile API, web search) to reduce false positives and handle endpoint instability
- **Rate limit detection** — Detects HTTP 429 responses across Instagram endpoints with a popup warning
- **Configurable verification delay** — Instagram jitter delay (min/max) now adjustable in the GUI settings
- **Consistent results logging** — Bulk check output appears in the Results Log with color-coded tags (available / possible / taken)
- **Webhook improvements** — Better platform filtering and status-based embed colors

### 1.0.5
- Compiled regex patterns to reduce CPU overhead on validation
- Batch blacklist file saving (every 20 proxies) instead of per-proxy saves, reducing I/O by ~95%
- Discord webhook notifications now run in a background thread queue
- Replaced sleep loop with `threading.Event` for instant stop response in monitor mode
- Jitter delay now only applied to Instagram checks, eliminating unnecessary delays elsewhere
- Reusable header templates to reduce per-request memory allocations
- Usernames under 4 characters return "Possibly Available" to reduce false positives
- Optimized proxy filtering and random selection logic

### 1.0.4
- Improved layout density
- Optimized batch updates and rendering
- Code cleanup

### 1.0.3
- Optimized core engine and proxy checker
- Added session ID support for improved Instagram verification
- Enhanced error handling in platform checkers
- Better visual feedback and UI responsiveness

### 1.0.2
- Reduced UI freezes when switching tabs by batching heavy updates and limiting global bindings
- Proxy table population is now incremental to avoid blocking the main thread

### 1.0.1
- Dedicated **PROXIES** tab with a sortable table (Proxy / Status)
- Visual status column: "BAD" label in red for blacklisted proxies
- Buttons to remove a single proxy, remove all bad proxies, and clear the blacklist
- Export button for `good_proxies.txt` and `bad_proxies.txt`
- Proxies validated at startup if `proxies.txt` exists
- SOCKS proxies auto-marked as bad if PySocks is not installed
- Proxy checker automatically integrates with the blacklist

### 1.0.0
- Initial release
- Bulk username checker with multi-platform support
- Sniper monitor with configurable interval
- Discord webhook integration
- Proxy support with rotation
- Export functionality
- Dark-themed Tkinter UI with resizable sidebar

---

## Credits

- **Sun Valley ttk theme** by `rdbende` (MIT License) — https://github.com/rdbende/sun-valley-ttk-theme

---

## Contact

- **Discord**: [tlmw](https://discord.com/users/tlmw)
- **Telegram**: [@feicoes](https://t.me/feicoes)
- **Discord Server**: [Join](https://discord.gg/2asv4rEhGh)
- **GitHub**: [@00ie](https://github.com/00ie)