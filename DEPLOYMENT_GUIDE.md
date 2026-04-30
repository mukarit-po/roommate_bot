# Deploying Roommate Bot to PythonAnywhere

This guide will walk you through deploying the Roommate Expense Bot to PythonAnywhere.

## Prerequisites

- PythonAnywhere account (free tier works)
- Telegram bot token from [@BotFather](https://t.me/botfather)
- Your Telegram user ID (get it from [@userinfobot](https://t.me/userinfobot))

## Step 1: Set Up PythonAnywhere Environment

1. **Create a PythonAnywhere account** at [pythonanywhere.com](https://www.pythonanywhere.com)

2. **Create a new console**:
   - Go to the "Consoles" tab
   - Click "Bash" to open a new bash console

3. **Set up a virtual environment**:
   ```bash
   python3.10 -m venv roommate_bot_env
   source roommate_bot_env/bin/activate
   ```

## Step 2: Upload Your Code

### Option A: Upload via Git (Recommended)

1. **Push your code to GitHub/GitLab**:
   ```bash
   # On your local machine
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Clone on PythonAnywhere**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git roommate_bot
   cd roommate_bot
   ```

### Option B: Upload Files Manually

1. **Create the project directory**:
   ```bash
   mkdir roommate_bot
   cd roommate_bot
   ```

2. **Upload files** using PythonAnywhere's file upload feature or scp/rsync

## Step 3: Install Dependencies

1. **Activate your virtual environment**:
   ```bash
   source ~/roommate_bot_env/bin/activate
   ```

2. **Install Python packages**:
   ```bash
   cd roommate_bot
   pip install -r requirements.txt
   ```

   If you encounter issues, you might need to install some packages individually:
   ```bash
   pip install aiogram pydantic-settings sqlalchemy aiosqlite asyncpg greenlet
   ```

## Step 4: Set Up Database

### For Free Tier Users: Use SQLite (Recommended)

PythonAnywhere free tier works perfectly with SQLite - no additional setup needed!

1. **Keep the default SQLite configuration**:
   ```env
   DATABASE_URL=sqlite+aiosqlite:///./roommate_bot.db
   ```

2. **That's it!** SQLite will automatically create the database file in your project directory.

### Alternative: PostgreSQL on PythonAnywhere (Paid Feature)

If you upgrade to a paid plan, you can use PostgreSQL:

1. **Create a PostgreSQL database**:
   - Go to the "Databases" tab in your PythonAnywhere dashboard
   - Click "Create database" (PostgreSQL)
   - Note down the database credentials

2. **Update your `.env` file**:
   ```env
   DATABASE_URL=postgresql+asyncpg://your_db_username:your_db_password@your_db_host/your_db_name
   ```

### Alternative: Free PostgreSQL from External Providers

If you want PostgreSQL without upgrading, use these free options:

#### Option A: Neon (Recommended)
1. Go to [neon.tech](https://neon.tech) and create a free account
2. Create a new project
3. Copy the connection string
4. Update your `.env`:
   ```env
   DATABASE_URL=postgresql+asyncpg://[your-connection-string-from-neon]
   ```

#### Option B: Supabase
1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project
3. Go to Settings → Database → Connection string
4. Use the connection string in your `.env`

#### Option C: ElephantSQL
1. Go to [elephantsql.com](https://elephantsql.com) and create a free account
2. Create a new instance (Tiny Turtle plan is free)
3. Copy the database URL
4. Update your `.env` with the provided URL

## Step 5: Configure the Bot

1. **Create your `.env` file**:
   ```bash
   nano .env
   ```

   Add the following content:
   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   ADMIN_CHAT_ID=your_telegram_user_id_here
   DATABASE_URL=sqlite+aiosqlite:///./roommate_bot.db
   LOG_LEVEL=INFO
   ```

   **For free tier users**: Keep `DATABASE_URL=sqlite+aiosqlite:///./roommate_bot.db` (default)

   **For PostgreSQL users**: Replace with your PostgreSQL connection string

2. **Get your credentials**:
   - **BOT_TOKEN**: From [@BotFather](https://t.me/botfather) on Telegram
   - **ADMIN_CHAT_ID**: Your Telegram user ID from [@userinfobot](https://t.me/userinfobot)
   - **DATABASE_URL**: Use SQLite for free tier, or PostgreSQL URL from step 4

## Step 6: Run the Bot

### Method 1: Run in Console (Recommended for development/testing)

1. **Start a new console** from PythonAnywhere dashboard
2. **Activate virtual environment and run**:
   ```bash
   source ~/roommate_bot_env/bin/activate
   cd roommate_bot
   python bot.py
   ```

### Method 2: Keep Console Open (Free Tier)

For PythonAnywhere free tier users:

1. **Start the bot in a console**:
   ```bash
   source ~/roommate_bot_env/bin/activate
   cd roommate_bot
   python bot.py
   ```

2. **Keep the console active**:
   - Don't close the browser tab
   - PythonAnywhere consoles stay active while the tab is open
   - If you need to leave, the console will timeout after ~1 hour

3. **Restart when needed**:
   - If the console times out, start a new console and run the bot again
   - Your SQLite database will persist between restarts

### Method 3: Always-On Task (Paid Tiers Only)

For paid PythonAnywhere tiers:
1. Go to "Tasks" tab
2. Create a new "Always-on task"
3. Set the command:
   ```bash
   source ~/roommate_bot_env/bin/activate && cd ~/roommate_bot && python bot.py
   ```

## Step 7: Verify Deployment

1. **Check the console output** for any errors
2. **Test your bot** by sending commands in Telegram:
   - `/start`
   - `/help`
   - `/create_group`
   - `/add 25.50 dinner`

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**:
   - Make sure you're in the virtual environment
   - Try reinstalling packages: `pip install -r requirements.txt`

2. **Database connection errors**:
   - Verify your DATABASE_URL in `.env`
   - Check that PostgreSQL database is created and credentials are correct

3. **Bot not responding**:
   - Check that BOT_TOKEN is correct
   - Verify the bot is running (check console output)
   - Make sure no other instance of the bot is running

4. **Permission errors**:
   - Make sure files are executable: `chmod +x bot.py`

### Logs and Debugging

1. **Check logs** in the console where the bot is running
2. **Test database connection**:
   ```python
   python -c "from database import init_db; import asyncio; asyncio.run(init_db())"
   ```

3. **Test bot token**:
   ```python
   python -c "from config import settings; print('Bot token loaded successfully')"
   ```

### PythonAnywhere Specific Issues

1. **Free tier limitations**:
   - Console sessions timeout after ~1 hour of inactivity
   - No always-on tasks (bot will stop when console closes)
   - Limited CPU time per day
   - SQLite database files are stored locally

2. **File paths**:
   - Use absolute paths: `/home/your_username/roommate_bot/`
   - Virtual environment: `/home/your_username/roommate_bot_env/`

3. **Environment variables**:
   - Make sure `.env` file is in the project root
   - PythonAnywhere might need `export` commands for some variables

4. **SQLite on PythonAnywhere**:
   - Database file will be created in your project directory
   - File path: `/home/your_username/roommate_bot/roommate_bot.db`
   - SQLite works perfectly for free tier users

## Maintenance

### Updating the Bot

1. **Pull latest changes**:
   ```bash
   cd ~/roommate_bot
   git pull origin main
   ```

2. **Restart the bot**:
   - Stop the current console
   - Start a new console and run the bot again

### Backup

- Regularly backup your database from PythonAnywhere's database tab
- Consider exporting important data periodically

## Support

If you encounter issues:
1. Check PythonAnywhere's help pages
2. Review the bot's logs for error messages
3. Verify all configuration files are correct
4. Test components individually (database, bot token, etc.)

## Security Notes

- Never commit `.env` files to version control
- Use strong passwords for your database
- Keep your bot token secure
- Regularly update dependencies for security patches