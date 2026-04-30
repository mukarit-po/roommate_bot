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

## Step 4: Set Up PostgreSQL Database

PythonAnywhere provides PostgreSQL databases for free.

1. **Create a PostgreSQL database**:
   - Go to the "Databases" tab in your PythonAnywhere dashboard
   - Click "Create database" (PostgreSQL)
   - Note down the database credentials (host, database name, username, password)

2. **Update your `.env` file**:
   ```bash
   nano .env
   ```

   Add the following content:
   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   ADMIN_CHAT_ID=your_telegram_user_id_here
   DATABASE_URL=postgresql+asyncpg://your_db_username:your_db_password@your_db_host/your_db_name
   LOG_LEVEL=INFO
   ```

   Replace the placeholders with your actual values.

## Step 5: Configure the Bot

1. **Make sure your `.env` file is properly configured** with:
   - Your bot token from BotFather
   - Your Telegram user ID
   - The PostgreSQL database URL from step 4

2. **Test the bot locally first** (optional but recommended):
   ```bash
   python bot.py
   ```
   Make sure it starts without errors.

## Step 6: Run the Bot

### Method 1: Run in Console (Recommended for development/testing)

1. **Start a new console** from PythonAnywhere dashboard
2. **Activate virtual environment and run**:
   ```bash
   source ~/roommate_bot_env/bin/activate
   cd roommate_bot
   python bot.py
   ```

### Method 2: Set Up Always-On Task (For production)

PythonAnywhere free tier doesn't support always-on tasks, but paid tiers do. For free tier, you'll need to keep the console open.

For paid tiers:
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
   - No always-on tasks
   - Limited CPU time

2. **File paths**:
   - Use absolute paths: `/home/your_username/roommate_bot/`
   - Virtual environment: `/home/your_username/roommate_bot_env/`

3. **Environment variables**:
   - Make sure `.env` file is in the project root
   - PythonAnywhere might need `export` commands for some variables

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