# WeverseBot

| :exclamation:  This project is no longer being maintained after Naver has acquired Weverse. They completely switched their API, and I do not have the time to make another wrapper.  :exclamation:  |
|-----------------------------------------|

## [Invite to your Server](https://discord.com/oauth2/authorize?client_id=864670527187451914&scope=bot&permissions=2952997936)

[![Discord Bots](https://top.gg/api/widget/864670527187451914.svg)](https://top.gg/bot/864670527187451914)

## To Self-Host:

You will need a PostgreSQL Server. After you have one running, you can do the below.  

``git clone https://github.com/MujyKun/WeverseBot``  

``pip install -r requirements.txt``

Rename `.env.example` to `.env`  
Open the `.env` file and change the weverse auth token, discord bot token, and postgres login to your own.  
[Tutorial for obtaining your own weverse token here.](https://weverse.readthedocs.io/en/latest/api.html#get-account-token)

## Commands:

**The Bot Prefix is set to `^` by default. There is currently no way to change it.**  
**Anything in brackets [] is optional.**  
**Anything in () is required.**  
**In order to disable/enable features, retyping the same exact command will toggle it.**


^weverse [Community Name] -> Follow a weverse community. Use without the community name to get a list of communities.  
^media (Community Name) -> Will enable/disable the media from that community.  
^comments (Community Name) -> Will enable/disable the comments from that community.  
^role (Role) (Community Name) -> Will add or update a role to mention for a community.  
^list -> Will list the currently followed communities in the channel.  

^patreon -> Link to patreon.  
^invite -> Link to invite bot.  
^support -> Link to support server.  
^ping -> Receives Client Ping.  
^servercount -> Displays amount of servers connected to the bot.

