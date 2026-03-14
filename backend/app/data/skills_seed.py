"""Initial skill seed data for ClawHub marketplace.

Each skill includes detailed descriptions with usage scenarios and examples.
Install counts are approximate values from ClawHub registry popularity.
"""

SKILL_SEEDS = [
    # --- Search ---
    {
        "slug": "web-search",
        "name": "Web Search",
        "summary": "Search the web in real-time to find current information and answer questions.",
        "description": """## Web Search

Enable your agent to search the internet for real-time information.

### Features
- Search Google, Bing, and other search engines
- Return relevant snippets and links
- Support for multiple languages and regions

### Use Cases
- Answer questions about current events
- Find documentation and references
- Research topics in real-time

### Example
**User:** What's the weather in Tokyo today?
**Agent:** *searches the web* According to the latest data, Tokyo is currently 18°C with partly cloudy skies...
""",
        "category": "search",
        "tags": ["search", "real-time", "web"],
        "author": "OpenClaw",
        "version": "2.1.0",
        "install_count": 12847,
        "is_featured": True,
    },
    {
        "slug": "deep-research",
        "name": "Deep Research",
        "summary": "Conduct in-depth multi-step research across multiple sources with synthesis.",
        "description": """## Deep Research

Perform comprehensive research by searching multiple sources, cross-referencing data, and synthesizing findings.

### Features
- Multi-step research workflow
- Cross-reference multiple sources
- Generate structured research reports
- Follow citation chains

### Use Cases
- Market research and competitive analysis
- Academic literature review
- Technical deep-dives on complex topics

### Example
**User:** Research the current state of quantum computing in Japan.
**Agent:** *conducting multi-step research...* I've analyzed 15 sources including RIKEN, University of Tokyo publications, and industry reports...
""",
        "category": "search",
        "tags": ["research", "multi-step", "synthesis"],
        "author": "OpenClaw",
        "version": "1.5.0",
        "install_count": 8432,
        "is_featured": True,
    },
    {
        "slug": "wikipedia",
        "name": "Wikipedia",
        "summary": "Search and retrieve Wikipedia articles in any language.",
        "description": """## Wikipedia

Access Wikipedia's vast knowledge base directly from your agent.

### Features
- Search articles in 300+ languages
- Retrieve full article content or summaries
- Follow internal links for deeper exploration

### Use Cases
- Quick factual lookups
- Historical information
- Definitions and explanations
""",
        "category": "search",
        "tags": ["search", "knowledge", "encyclopedia"],
        "author": "Community",
        "version": "1.2.0",
        "install_count": 6321,
        "is_featured": False,
    },

    # --- Productivity ---
    {
        "slug": "calculator",
        "name": "Calculator",
        "summary": "Perform mathematical calculations, unit conversions, and statistical analysis.",
        "description": """## Calculator

A powerful computation tool for your agent.

### Features
- Basic and advanced math operations
- Unit conversions (length, weight, temperature, currency)
- Statistical functions (mean, median, standard deviation)
- Equation solving

### Use Cases
- Financial calculations
- Engineering computations
- Data analysis support

### Example
**User:** Calculate the compound interest on $10,000 at 5% for 3 years.
**Agent:** *calculating...* $10,000 at 5% annual compound interest for 3 years = $11,576.25
""",
        "category": "productivity",
        "tags": ["math", "calculation", "conversion"],
        "author": "OpenClaw",
        "version": "1.8.0",
        "install_count": 9156,
        "is_featured": False,
    },
    {
        "slug": "calendar",
        "name": "Calendar",
        "summary": "Manage calendar events, check schedules, and set reminders.",
        "description": """## Calendar

Connect your calendar to manage events and schedules.

### Features
- Create, update, and delete calendar events
- Check availability and schedule conflicts
- Set reminders and recurring events
- Support for Google Calendar and Outlook

### Use Cases
- Schedule meetings
- Check daily agenda
- Plan recurring tasks
""",
        "category": "productivity",
        "tags": ["calendar", "scheduling", "reminders"],
        "author": "Community",
        "version": "2.0.1",
        "install_count": 5890,
        "is_featured": False,
    },
    {
        "slug": "todo-manager",
        "name": "Todo Manager",
        "summary": "Create and manage task lists with priorities, deadlines, and progress tracking.",
        "description": """## Todo Manager

Keep track of tasks and projects with your AI assistant.

### Features
- Create, update, and complete tasks
- Set priorities (high, medium, low)
- Add deadlines and reminders
- Organize tasks into projects
- Track completion progress

### Use Cases
- Daily task management
- Project planning
- Sprint task tracking
""",
        "category": "productivity",
        "tags": ["tasks", "todo", "project-management"],
        "author": "Community",
        "version": "1.3.0",
        "install_count": 4567,
        "is_featured": False,
    },

    # --- Development ---
    {
        "slug": "code-execution",
        "name": "Code Execution",
        "summary": "Execute Python, JavaScript, and other code in a secure sandbox environment.",
        "description": """## Code Execution

Run code safely inside a sandboxed environment.

### Features
- Support for Python, JavaScript, TypeScript, and Shell
- Secure sandboxed execution
- Access to common libraries (numpy, pandas, requests, etc.)
- Output capture with stdout/stderr separation
- Timeout protection

### Use Cases
- Data analysis and visualization
- Quick prototyping
- Mathematical computations
- Script testing

### Example
**User:** Generate a chart of Bitcoin price over the last year.
**Agent:** *executing Python code with matplotlib...* Here's the generated chart showing BTC price trends.
""",
        "category": "development",
        "tags": ["code", "python", "sandbox", "execution"],
        "author": "OpenClaw",
        "version": "3.2.0",
        "install_count": 11203,
        "is_featured": True,
    },
    {
        "slug": "github",
        "name": "GitHub",
        "summary": "Interact with GitHub repositories, issues, pull requests, and more.",
        "description": """## GitHub

Full GitHub integration for your AI agent.

### Features
- Browse repositories and files
- Create and manage issues
- Review and create pull requests
- Search code across repositories
- Manage releases and tags

### Use Cases
- Code review assistance
- Issue triage and management
- Repository documentation
- CI/CD monitoring
""",
        "category": "development",
        "tags": ["github", "git", "code-review", "devops"],
        "author": "OpenClaw",
        "version": "2.5.0",
        "install_count": 7845,
        "is_featured": True,
    },
    {
        "slug": "git",
        "name": "Git",
        "summary": "Execute git commands to manage version control within agent workspace.",
        "description": """## Git

Enable your agent to use git version control.

### Features
- Clone, pull, push repositories
- Create and manage branches
- Stage, commit, and diff changes
- View history and logs
- Resolve merge conflicts

### Use Cases
- Automated code commits
- Branch management
- Change tracking
""",
        "category": "development",
        "tags": ["git", "version-control", "scm"],
        "author": "OpenClaw",
        "version": "1.9.0",
        "install_count": 6234,
        "is_featured": False,
    },

    # --- Data ---
    {
        "slug": "file-parser",
        "name": "File Parser",
        "summary": "Read and parse PDF, Word, Excel, CSV, and other document formats.",
        "description": """## File Parser

Parse and extract content from various file formats.

### Features
- PDF text extraction with layout preservation
- Word document (.docx) parsing
- Excel/CSV data reading
- JSON/XML/YAML parsing
- Image text extraction (OCR)

### Use Cases
- Document summarization
- Data extraction from reports
- Invoice and receipt processing

### Example
**User:** Summarize this quarterly report PDF.
**Agent:** *parsing PDF...* The Q3 2025 report shows revenue of $2.3M, up 15% YoY...
""",
        "category": "data",
        "tags": ["file", "pdf", "excel", "parsing"],
        "author": "OpenClaw",
        "version": "2.0.0",
        "install_count": 8901,
        "is_featured": True,
    },
    {
        "slug": "csv-analyzer",
        "name": "CSV Analyzer",
        "summary": "Analyze CSV data with statistics, filtering, grouping, and visualization.",
        "description": """## CSV Analyzer

Powerful CSV data analysis tool with statistical capabilities.

### Features
- Load and preview CSV data
- Statistical summaries (count, mean, median, std)
- Filtering and grouping operations
- Data visualization (charts, plots)
- Export processed data

### Use Cases
- Sales data analysis
- Survey result processing
- Financial data reporting
""",
        "category": "data",
        "tags": ["csv", "data-analysis", "statistics", "visualization"],
        "author": "Community",
        "version": "1.4.0",
        "install_count": 3456,
        "is_featured": False,
    },
    {
        "slug": "json-tool",
        "name": "JSON Tool",
        "summary": "Validate, transform, query, and format JSON data with JSONPath support.",
        "description": """## JSON Tool

Work with JSON data efficiently.

### Features
- JSON validation and formatting
- JSONPath querying
- JSON ↔ CSV/YAML conversion
- Schema validation
- Merge and diff operations

### Use Cases
- API response analysis
- Configuration management
- Data transformation pipelines
""",
        "category": "data",
        "tags": ["json", "data", "transformation"],
        "author": "Community",
        "version": "1.1.0",
        "install_count": 2890,
        "is_featured": False,
    },

    # --- AI ---
    {
        "slug": "image-gen",
        "name": "Image Generation",
        "summary": "Generate images from text descriptions using AI (DALL-E, Stable Diffusion).",
        "description": """## Image Generation

Create images from text prompts using state-of-the-art AI models.

### Features
- Text-to-image generation
- Multiple style options (photorealistic, illustration, anime, etc.)
- Resolution control (256px to 1024px)
- Image editing and variation
- Batch generation

### Use Cases
- Marketing material creation
- Concept art and prototyping
- Social media content
- Presentation visuals

### Example
**User:** Generate a logo for a sushi delivery app.
**Agent:** *generating image...* Here's a modern logo concept featuring a stylized sushi roll with delivery elements.
""",
        "category": "ai",
        "tags": ["image", "generation", "dall-e", "creative"],
        "author": "OpenClaw",
        "version": "2.3.0",
        "install_count": 10234,
        "is_featured": True,
    },
    {
        "slug": "text-to-speech",
        "name": "Text to Speech",
        "summary": "Convert text to natural-sounding speech in multiple languages and voices.",
        "description": """## Text to Speech

Generate natural-sounding audio from text.

### Features
- 50+ voices in 30+ languages
- Adjustable speed and pitch
- SSML support for fine control
- Multiple output formats (MP3, WAV, OGG)

### Use Cases
- Content narration
- Accessibility support
- Language learning
- Podcast generation
""",
        "category": "ai",
        "tags": ["tts", "speech", "audio", "voice"],
        "author": "Community",
        "version": "1.6.0",
        "install_count": 4321,
        "is_featured": False,
    },
    {
        "slug": "translation",
        "name": "Translation",
        "summary": "Translate text between 100+ languages with context-aware accuracy.",
        "description": """## Translation

High-quality translation powered by multiple translation engines.

### Features
- 100+ language pairs
- Context-aware translation
- Document translation (preserves formatting)
- Glossary support for domain-specific terms
- Batch translation

### Use Cases
- Content localization
- International communication
- Document translation
- Multi-language customer support
""",
        "category": "ai",
        "tags": ["translation", "language", "localization", "i18n"],
        "author": "OpenClaw",
        "version": "2.0.0",
        "install_count": 7654,
        "is_featured": True,
    },

    # --- Communication ---
    {
        "slug": "email",
        "name": "Email",
        "summary": "Send, read, and manage emails through Gmail, Outlook, and other providers.",
        "description": """## Email

Full email management for your AI agent.

### Features
- Send and receive emails
- Draft and review messages
- Search inbox and folders
- Attachment handling
- Template support

### Use Cases
- Automated email responses
- Newsletter drafting
- Email summarization
- Contact management
""",
        "category": "communication",
        "tags": ["email", "gmail", "outlook", "messaging"],
        "author": "Community",
        "version": "1.8.0",
        "install_count": 5432,
        "is_featured": False,
    },
    {
        "slug": "slack",
        "name": "Slack",
        "summary": "Send messages, manage channels, and interact with Slack workspaces.",
        "description": """## Slack

Integrate your agent with Slack for team communication.

### Features
- Send and read messages in channels
- Direct message users
- Create and manage channels
- File sharing
- Thread management

### Use Cases
- Team notifications
- Automated status updates
- Meeting summaries to channels
- Cross-channel information relay
""",
        "category": "communication",
        "tags": ["slack", "chat", "team", "messaging"],
        "author": "Community",
        "version": "2.1.0",
        "install_count": 4890,
        "is_featured": False,
    },

    # --- Browser ---
    {
        "slug": "browser-automation",
        "name": "Browser Automation",
        "summary": "Control a headless browser to navigate websites, fill forms, and extract data.",
        "description": """## Browser Automation

Control a browser programmatically for web automation tasks.

### Features
- Navigate to URLs and follow links
- Fill forms and click buttons
- Take screenshots
- Extract structured data from pages
- Handle authentication flows
- Cookie and session management

### Use Cases
- Web scraping and data extraction
- Automated form filling
- Website testing
- Price monitoring

### Example
**User:** Go to the Tokyo Metro website and get the current service status.
**Agent:** *navigating to tokyo-metro.jp...* All lines are operating normally except the Ginza Line which has a 5-minute delay.
""",
        "category": "browser",
        "tags": ["browser", "automation", "scraping", "puppeteer"],
        "author": "OpenClaw",
        "version": "3.0.0",
        "install_count": 9876,
        "is_featured": True,
    },
    {
        "slug": "screenshot",
        "name": "Screenshot",
        "summary": "Capture screenshots of websites, specific elements, or full pages.",
        "description": """## Screenshot

Capture visual snapshots of web pages and content.

### Features
- Full-page screenshots
- Element-specific capture
- Custom viewport sizes (mobile, tablet, desktop)
- PDF generation from web pages
- Batch screenshot capture

### Use Cases
- Design review and comparison
- Bug documentation
- Content archiving
- Visual monitoring
""",
        "category": "browser",
        "tags": ["screenshot", "capture", "visual"],
        "author": "Community",
        "version": "1.2.0",
        "install_count": 3210,
        "is_featured": False,
    },
    {
        "slug": "web-scraper",
        "name": "Web Scraper",
        "summary": "Extract structured data from websites with CSS selectors and XPath.",
        "description": """## Web Scraper

Extract data from websites in a structured format.

### Features
- CSS selector and XPath support
- Pagination handling
- Rate limiting and polite scraping
- Output in JSON, CSV, or structured data
- JavaScript rendering support

### Use Cases
- Price comparison
- Product catalog extraction
- News aggregation
- Job listing collection
""",
        "category": "browser",
        "tags": ["scraping", "data-extraction", "web"],
        "author": "Community",
        "version": "1.5.0",
        "install_count": 4567,
        "is_featured": False,
    },

    # --- CLI & System ---
    {
        "slug": "shell",
        "name": "Shell Commands",
        "summary": "Execute shell commands in a controlled environment with safety checks.",
        "description": """## Shell Commands

Run system commands with built-in safety guardrails.

### Features
- Execute bash/zsh commands
- Command allowlisting for safety
- Output capture and streaming
- Working directory management
- Environment variable handling

### Use Cases
- File management
- System administration
- Build and deployment scripts
- Log analysis
""",
        "category": "development",
        "tags": ["shell", "bash", "cli", "system"],
        "author": "OpenClaw",
        "version": "2.4.0",
        "install_count": 7123,
        "is_featured": False,
    },
    {
        "slug": "memory",
        "name": "Long-term Memory",
        "summary": "Store and recall information across conversations for persistent context.",
        "description": """## Long-term Memory

Give your agent persistent memory across conversations.

### Features
- Store key facts and preferences
- Automatic context recall
- Memory categories (user preferences, project context, learned facts)
- Memory search and retrieval
- Memory management (view, edit, delete)

### Use Cases
- Remember user preferences
- Track project progress across sessions
- Build up domain knowledge over time
- Personalized interactions

### Example
**User:** Remember that I prefer dark mode and use VSCode.
**Agent:** *saved to memory* Got it! I'll remember your preferences for future conversations.
""",
        "category": "ai",
        "tags": ["memory", "context", "persistence", "personalization"],
        "author": "OpenClaw",
        "version": "2.0.0",
        "install_count": 8765,
        "is_featured": True,
    },
]
