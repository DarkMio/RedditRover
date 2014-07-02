# Massdrop Reddit Bot
In case you're interested in writing reddit bots and like to see how different bots operate, you can view and preview this bot here. Please respect my work and don't run it extensively on your own. This would spam under comments, since my bot is already hosted on a dedicated server. You can run it (please change the `self.comment` in the threading-class) and review it without problems, but when two bots run the same process, we just create clutter on reddit, which will get me and you banned. Thanks.

## Installation & Usage
Run `massdrop.py` and log in. Everything else is done by the bot, even the creatíon of the SQLite3 database.

## Debugging
I haven't written a proper debug-mode yet, so you might want to replace the `except: pass` passages with `self.close()`, which will print a traceback if needed. This might be depricated in the future.

## Version & Changelog
Current MassdropBot is running as v0.3, fixing some weird behaviour with non-escaped chars in links. Also he shouldn't spam himself anymore.
```
v0.3: Fixing behaviour with non-escaped chars in links and stopping the self-spam.
v0.2: Methods to query with referer-link and stuff like that
v0.1: Initial Commit
```

## Planned features
- Processing more than one link in one comment / selfpost.
- Debugger-Features and startup commands.

## Help, questions, contribution
Feel free to mail me, even here on GitHub.

Thanks for your interest and have a good time.