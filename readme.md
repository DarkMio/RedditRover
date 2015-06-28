# Massdrop Reddit Bot
In case you're interested in writing reddit bots and like to see how different bots operate, you can view and preview this bot here. Please respect my work and don't run it extensively on your own. This would spam under comments, since my bot is already hosted on a dedicated server. You can run it (please change the `self.comment` in the threading-class) and review it without problems, but when two bots run the same process, we just create clutter on reddit, which will get me and you banned. Thanks.

## Progress

![Feature Complete](http://progressed.io/bar/65?title=Feature%20Complete)
![Database Provider](http://progressed.io/bar/90?title=Database%20Provider)
![Framework](http://progressed.io/bar/70?title=Framework)
![Threading](http://progressed.io/bar/100?title=Threading)
![Modules](http://progressed.io/bar/0?title=Modules)

## Installation & Usage
No clue what the bot will use in plugins, but currently he is running only with builtins (and later with PRAW.)

## Debugging
Bot features are writting in Abstract Base Classes. Inherit them properly and then test them extensively with strings.

## Version & Changelog
This bot is now again under development. Way less complex code, more segmentation and more single responsibility principle.

```
v0.6: (Currently being worked on.) Recode of the bot.
--------------------------------------------------------------------------------------------------------------
v0.5: Added more bots - and then it kept fucking up.
v0.4: Should now load inifite amounts of links, represent them with the website title and respond accordingly.
v0.3: Fixing behaviour with non-escaped chars in links and stopping the self-spam.
v0.2: Methods to query with referer-link and stuff like that
v0.1: Initial Commit
```

## Planned features & work in progress
- Debugger-Features and startup commands.
- Ban Lists (for subreddits and users!)
- Multi Login (configparser already reads logins somehow, maybe needs better grouping.)
- Maybe a nitpicky answer module
- SmallSubBot generates Set of subreddits (eliminates the possibility of a subreddit being called twice)

##### Planned Massdrop Features
- After reading Massdrop links wait some time before responding (LIFO queue)
- Price History (min/max/current?)
- End date of current drop
- Unit Order Limit

## Help, questions, contribution
Feel free to mail me, even here on GitHub.

Thanks for your interest and have a good time.
