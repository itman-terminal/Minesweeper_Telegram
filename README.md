# Minesweeper_Telegram
A Telegram Minesweeper Game Bot
# How To Use
First, please install the dependency.
```shell
python -m pip install telebot uuid
```

# Set Bot Token
Create a Bot From: https://t.me/@botfather

Enter in the edit command mode of @botfather:
```
minesweeper - 开始游戏
f - 放置旗子
cancel - 不玩了
continue - 继续游戏
```

Set the `BOT_TOKEN` variable to the TOKEN you got from @botfather.

Then run it directly:
```shell
python ./minesweeper.py
```

碎碎念:以后说不定会有Inline模式的游戏...但是这是以后的事了

以及: Bot将游戏数据存放在./games.json里面了，可以使用 `/check` 命令查看游戏数据
2025.2.16:增加计时，/continue命令，剩余雷数（并不是标记正确的技术，仅是总雷数减已标记的雷数）
