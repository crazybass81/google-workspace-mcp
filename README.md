# Google Workspace MCP Server

**A Model Context Protocol server for seamless integration between Claude Code and Google Workspace services.**

## Features

### ✅ Complete Google Workspace Integration
- **Google Drive**: Full file management (search, read, create, update, delete, upload/download)
- **Google Docs**: Document creation, reading, and editing
- **Google Sheets**: Spreadsheet operations with range updates and batch processing
- **Google Slides**: Presentation management and slide manipulation
- **Google Forms**: Form creation, editing, and response collection
- **Gmail**: Email search, read, send, reply, and label management

### 🔒 Secure Authentication
- OAuth 2.0 authentication with automatic token refresh
- Encrypted token storage
- Minimal scope requirements

### ⚡ Performance Optimized
- Async/await architecture for concurrent operations
- Built-in caching with TTL
- Smart rate limiting to prevent API quota exhaustion
- Request batching where possible

### 🛡️ Robust Error Handling
- Comprehensive error management
- Automatic retry logic for transient failures
- Detailed error messages for debugging

## Installation

### Prerequisites
- Python 3.10 or higher
- Google Cloud Project with Workspace APIs enabled
- OAuth 2.0 credentials

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/google-workspace-mcp.git
cd google-workspace-mcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Create config directory
mkdir -p config
```

### Step 2: Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the following APIs:
   - Google Drive API
   - Google Docs API
   - Google Sheets API
   - Google Slides API
   - Google Forms API
   - Gmail API

4. Configure OAuth Consent Screen:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Choose "External" user type
   - Fill in required fields (App name, User support email, Developer contact)
   - Add scopes:
     - `https://www.googleapis.com/auth/drive`
     - `https://www.googleapis.com/auth/documents`
     - `https://www.googleapis.com/auth/spreadsheets`
     - `https://www.googleapis.com/auth/presentations`
     - `https://www.googleapis.com/auth/forms`
     - `https://www.googleapis.com/auth/gmail.modify`

5. Create OAuth 2.0 Client ID:
   - Go to "Credentials" > "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download credentials JSON file
   - Copy `config/credentials.json.example` to `config/credentials.json`
   - Replace the example values with your downloaded credentials

### Step 3: Initial Authentication

```bash
# Run server for first-time authentication
python3 -m google_workspace_mcp

# Browser will open for OAuth consent
# Grant necessary permissions
# Token will be saved automatically
```

### Step 4: Claude Code Integration

Add to your Claude Code MCP settings (`~/.claude/config/settings.json`):

```json
{
  "mcpServers": {
    "google-workspace": {
      "command": "/usr/local/bin/python3",
      "args": ["-m", "google_workspace_mcp"],
      "cwd": "/path/to/your/google-workspace-mcp",
      "env": {}
    }
  }
}
```

**Note**: Replace `/path/to/your/google-workspace-mcp` with your actual installation path.

## Available Tools

### Google Drive (8 tools)
- `drive_search_files` - Search files/folders
- `drive_read_file` - Read file content
- `drive_create_file` - Create new file
- `drive_update_file` - Update existing file
- `drive_delete_file` - Delete file
- `drive_upload_file` - Upload local file
- `drive_download_file` - Download to local
- `drive_list_shared_drives` - List Team Drives

### Google Docs (4 tools)
- `docs_create` - Create document
- `docs_read` - Read document
- `docs_update` - Update document
- `docs_delete` - Delete document

### Google Sheets (4 tools)
- `sheets_create` - Create spreadsheet
- `sheets_read` - Read range
- `sheets_update` - Update range
- `sheets_delete` - Delete spreadsheet

### Google Slides (4 tools)
- `slides_create` - Create presentation
- `slides_read` - Read presentation
- `slides_update` - Update slides
- `slides_delete` - Delete presentation

### Google Forms (5 tools)
- `forms_create` - Create form
- `forms_read` - Read form structure
- `forms_update` - Update form
- `forms_delete` - Delete form
- `forms_get_responses` - Get form responses

### Gmail (6 tools)
- `gmail_search_messages` - Search emails
- `gmail_read_message` - Read email content
- `gmail_send_message` - Send new email
- `gmail_reply_message` - Reply to email
- `gmail_delete_message` - Delete email
- `gmail_list_labels` - List labels

## Usage Examples

### Search Drive Files
```
In Claude Code:
"Search my Drive for files named 'project report'"

Uses: drive_search_files with query parameter
```

### Read and Summarize Document
```
"Read the document with ID xyz and summarize it"

Uses: drive_read_file → Processes content
```

### Send Email
```
"Send an email to team@example.com with subject 'Meeting Update' and body '...'"

Uses: gmail_send_message
```

### Create Spreadsheet
```
"Create a new spreadsheet called 'Q4 Budget' with headers A1:E1"

Uses: sheets_create → sheets_update
```

## Configuration

### Environment Variables
```bash
# Optional: Custom config directory
export GW_MCP_CONFIG_DIR=~/.config/gw-mcp

# Optional: Log level
export GW_MCP_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Cache Settings
Default cache TTL: 300 seconds (5 minutes)
Max cache size: 1000 items

### Rate Limiting
Default limits:
- 100 requests per 60 seconds per service
- Burst limit: 10 consecutive requests

## Troubleshooting

### Authentication Issues
```bash
# Clear stored tokens
rm ~/.config/gw-mcp/token.pickle

# Re-authenticate
python3 -m google_workspace_mcp
```

### Permission Errors
- Verify all required APIs are enabled in Google Cloud Console
- Check OAuth scopes in consent screen configuration
- Ensure credentials.json is in correct location

### Rate Limit Errors
- Server automatically handles rate limiting with exponential backoff
- Check Google Cloud Console quotas if persistent issues

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Development

### Running Tests
```bash
pytest tests/
pytest tests/ --cov=src --cov-report=html
```

### Project Structure
```
google-workspace-mcp/
├── src/
│   ├── auth/           # OAuth authentication
│   ├── services/       # Google API wrappers
│   ├── tools/          # MCP tool definitions
│   ├── utils/          # Utilities (logging, caching, etc.)
│   └── server.py       # Main MCP server
├── config/             # Configuration files
├── tests/              # Test suite
├── requirements.txt    # Dependencies
├── setup.py           # Package setup
└── README.md          # This file
```

## Architecture

```
Claude Code (MCP Client)
        ↓
MCP Protocol (stdio)
        ↓
Google Workspace MCP Server
  ├── MCP Handler (Tool Registry)
  ├── Service Layer (API Wrappers)
  │   ├── Drive Service
  │   ├── Docs Service
  │   ├── Sheets Service
  │   ├── Slides Service
  │   ├── Forms Service
  │   └── Gmail Service
  ├── Auth Manager (OAuth 2.0)
  └── Infrastructure (Cache, Rate Limit, Logging)
        ↓
Google Workspace APIs
```

## Security Considerations

- **Token Storage**: Tokens encrypted and stored securely in user config directory
- **Scope Minimization**: Only requests necessary permissions
- **No Credential Logging**: Sensitive data never logged
- **Automatic Token Refresh**: Expired tokens refreshed automatically
- **Rate Limiting**: Prevents quota exhaustion and API abuse

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Open an issue on GitHub
- Check troubleshooting section
- Review Google Workspace API documentation

## Acknowledgments

- Built with [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Uses [Google API Python Client](https://github.com/googleapis/google-api-python-client)
- Designed for [Claude Code](https://claude.ai/code)
