# Massdrop Reddit Bot
In case you're interested in writing reddit bots and like to see how different bots operate, you can view and preview this bot here. Please respect my work and don't run it extensively on your own. This would spam under comments, since my bot is already hosted on a dedicated server. You can run it (please change the `self.comment` in the threading-class) and review it without problems, but when two bots run the same process, we just create clutter on reddit, which will get me and you banned. Thanks.

## Installation & Usage
Run `massdrop.py` and log in. Everything else is done by the bot, even the creatíon of the SQLite3 database.

## Debugging
I haven't written a proper debug-mode yet, so you might want to replace the `except: pass` passages with `self.close()`, which will print a traceback if needed. This might be depricated in the future.

## Version & Changelog
Current MassdropBot is running as v0.5, moving the actual linkfix-object to a file (including self-debug if you run it on its own), adding features to reply with several accounts and bringing two new reply-bots:
- JiffierBot: Finds giant.gfycat-links and replies with the original, jiffier link.
- SmallSubBot: Finds mentioned subreddits and replies them as links in the comments.

These new features are in place to have multiple accounts, since different subreddits ban different bots. In the future there should be a bot-framework, that gives you access to the multi-threaded skeleton of that bot and a numerous features to simply reply with different accounts. This is based upon a hidden feature in PRAW, which isn't official yet - and only the case, since replying to found comments between multiple PRAW-instances isn't as easy with the given generators from on PRAW-comment.

```
v0.4: Should now load inifite amounts of links, represent them with the website title and respond accordingly.
v0.3: Fixing behaviour with non-escaped chars in links and stopping the self-spam.
v0.2: Methods to query with referer-link and stuff like that
v0.1: Initial Commit
```

## Planned features
- Debugger-Features and startup commands.

## Help, questions, contribution
Feel free to mail me, even here on GitHub.

Thanks for your interest and have a good time.
