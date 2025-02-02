import random
import json
import uuid
from telebot import TeleBot, types
import os

# 初始化机器人
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = TeleBot(BOT_TOKEN)

# 游戏数据存储文件
GAMES_FILE = 'games.json'

# 数字对应的表情符号
number_emojis = {
    -2: '🚩',   # 标记
    -1: '💣',   # 地雷
    0: '⬜',    # 空白
    1: '1️⃣',
    2: '2️⃣',
    3: '3️⃣',
    4: '4️⃣',
    5: '5️⃣',
    6: '6️⃣',
    7: '7️⃣',
    8: '8️⃣'
}

def get_emoji(number):
    """获取对应数字的表情符号"""
    return number_emojis.get(number, '⬜')
def check_victory_conditions(game, games, gameid):
    """统一检查胜利条件"""
    size = game['size']
    grid = game['grid']
    revealed = set(game['revealed'])
    marked = set(game['marked'])

    # 条件1：所有未揭开的格子都是雷
    all_mines = {(i, j) for j in range(size) for i in range(size) if grid[j][i] == -1}
    unrevealed = {(i, j) for j in range(size) for i in range(size)} - revealed
    if unrevealed == all_mines:
        game['game_over'] = True
        game['marked'] = [f"{i},{j}" for (i, j) in all_mines]
        save_games(games)
        # 更新界面并发送消息
        markup = generate_markup(game, gameid)
        bot.edit_message_reply_markup(
            chat_id=game['chat_id'],
            message_id=game['message_id'],
            reply_markup=markup
        )
        bot.send_message(game['chat_id'], "🎉 恭喜！你成功完成了扫雷！*^_^*")
        # 记录日志
        game['log'].append("游戏胜利: 所有未揭开的格子都是雷*^_^*")
        print(f"游戏日志 ({gameid}): {game['log']}")
        print(f"雷的位置: {[(rx, ry) for ry in range(size) for rx in range(size) if grid[ry][rx] == -1]}")
        del games[gameid]
        save_games(games)
        return True

    # 条件2：所有雷都被正确标记
    marked_mines = {tuple(map(int, pos.split(','))) for pos in marked}
    if marked_mines == all_mines:
        game['game_over'] = True
        game['revealed'] = [f"{i},{j}" for (i, j) in all_mines]
        save_games(games)
        # 更新界面并发送消息
        markup = generate_markup(game, gameid)
        bot.edit_message_reply_markup(
            chat_id=game['chat_id'],
            message_id=game['message_id'],
            reply_markup=markup
        )
        bot.send_message(game['chat_id'], "🎉 恭喜！你成功标记了所有地雷！*^_^*")
        # 记录日志
        game['log'].append("游戏胜利: 所有雷都被正确标记")
        print(f"游戏日志 ({gameid}): {game['log']}")
        print(f"雷的位置: {[(rx, ry) for ry in range(size) for rx in range(size) if grid[ry][rx] == -1]}")
        del games[gameid]
        save_games(games)
        return True

    return False
def save_games(games):
    """保存游戏数据到文件"""
    with open(GAMES_FILE, 'w') as f:
        json.dump(games, f, indent=2)

def load_games():
    """从文件加载游戏数据"""
    try:
        with open(GAMES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
@bot.message_handler(commands=['minesweeper'])
def send_minesweeper(message):
    """处理 /minesweeper 命令"""
    try:
        # 检查用户是否已有进行中的游戏
        games = load_games()
        user_id = message.from_user.id
        for gameid in list(games.keys()):  # 转换为列表避免遍历时修改
            game = games[gameid]
            if game['user_id'] == user_id and not game['game_over']:
                bot.reply_to(message, "你已经有进行中的游戏了，请先完成或使用 /cancel 取消！(>_<)")
                return

        # 解析参数（默认8x8，10个雷）
        size = 8
        mines = 10
        args = message.text.split()[1:]
        if args:
            size = min(max(int(args[0].split('x')[0]), 5), 10)
        if len(args) >= 2:
            mines = min(max(int(args[1]), 1), (size * size) - 1)

        # 初始化空白网格
        grid = [[0 for _ in range(size)] for _ in range(size)]
        gameid = str(uuid.uuid4())

        # 保存游戏数据
        games[gameid] = {
            'user_id': message.from_user.id,
            'chat_id': message.chat.id,
            'size': size,
            'mines': mines,
            'grid': grid,
            'revealed': [],
            'marked': [],
            'game_over': False,
            'first_click': True,  # 标记是否为第一次点击
            'log': []  # 操作日志
        }
        save_games(games)

        # 生成按钮网格
        markup = generate_markup(games[gameid], gameid)
        sent_msg = bot.send_message(
            message.chat.id,
            f"� 扫雷游戏 {size}x{size}（{mines}雷*^_^*）\n点击格子开始游戏！╭(╯ε╰)╮\n使用 /f 命令标记旗子，左上角的坐标为0,0，从上到下x轴递增，从左至右y轴递增O(∩_∩)O\n呐，要将所有的雷都插上旗子才算胜利啊",
            reply_markup=markup
        )
        # 记录消息ID用于后续更新
        games[gameid]['message_id'] = sent_msg.message_id
        save_games(games)

    except Exception as e:
        bot.reply_to(message, f"参数错误: {str(e)} (>_<)")
def generate_markup(game_data, gameid):
    """生成按钮布局"""
    size = game_data['size']
    grid = game_data['grid']
    revealed = set(game_data['revealed'])
    marked = set(game_data['marked'])
    game_over = game_data['game_over']

    markup = types.InlineKeyboardMarkup()
    for y in range(size):
        row = []
        for x in range(size):
            pos = f"{x},{y}"
            if game_over or pos in revealed:
                # 显示数字或地雷
                cell = grid[y][x]
                text = get_emoji(cell)
            elif pos in marked:
                text = number_emojis[-2]  # 标记
            else:
                text = '🟦'  # 未揭开
            btn = types.InlineKeyboardButton(
                text=text,
                callback_data=f"pos={x},{y};gameid={gameid}"
            )
            row.append(btn)
        markup.row(*row)
    return markup
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        # 解析回调参数
        params = dict(p.split('=') for p in call.data.split(';'))
        x, y = map(int, params['pos'].split(','))
        gameid = params['gameid']

        # 加载游戏数据
        games = load_games()
        if gameid not in games:
            bot.answer_callback_query(call.id, "游戏已过期或不存在！＠_＠")
            return

        game = games[gameid]
        
        # 验证用户身份
        if call.from_user.id != game['user_id']:
            bot.answer_callback_query(call.id, "这不是你的游戏！(>_<)")
            return

        # 检查游戏状态
        if game['game_over']:
            # 游戏结束后不再更新消息
            bot.answer_callback_query(call.id, "游戏已结束！(>_<)")
            return

        # 确保消息 ID 有效
        if not hasattr(call.message, 'message_id'):
            bot.answer_callback_query(call.id, "无法找到有效的消息 ID(>_<)")
            return

        # 获取游戏状态变量
        revealed = set(game['revealed'])
        marked = set(game['marked'])
        pos_str = f"{x},{y}"
        grid = game['grid']
        size = game['size']

        # 记录日志：用户点击的位置
        print(f"用户点击位置: ({x}, {y})")
        print(f"当前标记位置: {marked}")
        print(f"当前揭开位置: {revealed}")

        # 如果是第一次点击，生成雷
        if game['first_click']:
            game['first_click'] = False
            # 确保雷不会生成在用户点击的位置及其周围
            safe_zone = {(x + dx, y + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1]}
            safe_zone = {(i, j) for (i, j) in safe_zone if 0 <= i < size and 0 <= j < size}
            
            # 生成雷
            mines_placed = 0
            while mines_placed < game['mines']:
                rx = random.randint(0, size - 1)
                ry = random.randint(0, size - 1)
                if (rx, ry) not in safe_zone and grid[ry][rx] != -1:
                    grid[ry][rx] = -1
                    mines_placed += 1
                    # 更新周围数字
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if 0 <= ry + dy < size and 0 <= rx + dx < size:
                                if grid[ry + dy][rx + dx] != -1:
                                    grid[ry + dy][rx + dx] += 1
            
            # 更新网格
            game['grid'] = grid
            # 记录日志
            game['log'].append(f"第一次点击: ({x}, {y}), 生成雷: {[(rx, ry) for ry in range(size) for rx in range(size) if grid[ry][rx] == -1]}")
            print(f"生成雷的位置: {[(rx, ry) for ry in range(size) for rx in range(size) if grid[ry][rx] == -1]}")

        # 如果位置已被标记，点击无效
        if pos_str in marked:
            bot.answer_callback_query(call.id, "该位置已被标记，请使用 /f 命令取消标记(>_<)")
            return

        # 处理点击揭开逻辑
        if grid[y][x] == -1:  # 踩中地雷
            # 显示所有地雷
            game['game_over'] = True
            game['revealed'] = [f"{i},{j}" for j in range(size) for i in range(size) if grid[j][i] == -1]
            save_games(games)
            
            # 更新游戏界面
            markup = generate_markup(game, gameid)
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup
            )
            
            # 发送失败消息并删除存档
            bot.send_message(call.message.chat.id, "💥 你踩到地雷了！游戏结束！T^T")
            # 记录日志
            game['log'].append(f"游戏结束: 踩中地雷 ({x}, {y})")
            print(f"游戏日志 ({gameid}): {game['log']}")
            print(f"雷的位置: {[(rx, ry) for ry in range(size) for rx in range(size) if grid[ry][rx] == -1]}")
            del games[gameid]
            save_games(games)
            return
        else:  # 安全区域
            # 递归揭开空白区域
            def reveal(x, y):
                pos = f"{x},{y}"
                if pos in revealed or pos in marked:
                    return
                revealed.add(pos)
                
                if grid[y][x] == 0:
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < size and 0 <= ny < size:
                                reveal(nx, ny)
            
            reveal(x, y)
            game['revealed'] = list(revealed)
            # 记录日志
            game['log'].append(f"揭开格子: ({x}, {y})")
            print(f"揭开格子: ({x}, {y})")

        # 保存更新后的状态
        save_games(games)

        # 检查胜利条件
        if check_victory_conditions(game, games, gameid):
            return

        # 更新游戏界面
        markup = generate_markup(game, gameid)
        current_markup = call.message.reply_markup
        if markup != current_markup:  # 只有标记发生变化时才更新
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup
            )
        bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"Error handling callback: {e}")
        bot.answer_callback_query(call.id, "处理操作时发生错误")

@bot.message_handler(commands=['cancel'])
def cancel_game(message):
    """取消当前用户进行中的游戏"""
    games = load_games()
    user_id = message.from_user.id
    canceled = 0
    
    # 找到用户最近的进行中游戏
    for gameid in list(games.keys()):
        game = games[gameid]
        if game['user_id'] == user_id and not game['game_over']:
            try:
                # 尝试更新消息为结束状态
                markup = generate_markup(game, gameid)
                bot.edit_message_reply_markup(
                    chat_id=game['chat_id'],
                    message_id=game['message_id'],
                    reply_markup=markup
                )
            except Exception as e:
                print(f"更新消息失败: {str(e)}")
            
            del games[gameid]
            canceled += 1
            break  # 只取消一个游戏
    
    save_games(games)
    if canceled:
        bot.reply_to(message, "已取消你当前的扫雷游戏 ╮(╯▽╰)╭")
    else:
        bot.reply_to(message, "你没有进行中的游戏！(⊙_⊙)")
@bot.message_handler(commands=['f'])
def flag_cell(message):
    """处理 /f x y 命令，用于插旗子"""
    try:
        # 解析参数
        args = message.text.split()
        if len(args) != 3:
            bot.reply_to(message, "格式错误，请使用：/f x y T^T")
            return
        
        x = int(args[1])
        y = int(args[2])
        
        # 查找用户当前的游戏
        games = load_games()
        user_id = message.from_user.id
        game = None
        gameid = None
        
        # 查找用户最近的进行中游戏
        for gid in games:
            g = games[gid]
            if g['user_id'] == user_id and not g['game_over']:
                game = g
                gameid = gid
                break
        
        if not game:
            bot.reply_to(message, "你没有进行中的游戏！(＞﹏＜)")
            return
        
        pos_str = f"{x},{y}"
        
        # 检查位置是否有效
        if x < 0 or x >= game['size'] or y < 0 or y >= game['size']:
            bot.reply_to(message, "位置超出范围！←_←")
            return
        
        # 如果位置已经被揭开，不能插旗
        if pos_str in game['revealed']:
            bot.reply_to(message, "该位置已被揭开，不能插旗！-_-||")
            return
        
        # 切换插旗状态
        if pos_str in game['marked']:
            game['marked'].remove(pos_str)
            print(f"取消标记: ({x}, {y})")
        else:
            game['marked'].append(pos_str)
            print(f"标记位置: ({x}, {y})")
        
        # 保存更新后的状态
        save_games(games)
        
        # 更新游戏界面
        markup = generate_markup(game, gameid)
        bot.edit_message_reply_markup(
            chat_id=game['chat_id'],
            message_id=game['message_id'],
            reply_markup=markup
        )
        bot.reply_to(message, f"已更新位置 ({x}, {y}) 的插旗状态 *^_^*")

        # 触发胜利检查
        check_victory_conditions(game, games, gameid)
    
    except Exception as e:
        print(f"标记格子时发生错误: {str(e)}")
        bot.reply_to(message, "标记格子时发生错误，请检查输入格式！(>_<)")
        
if __name__ == "__main__":
    # 确保存储文件存在
    if not os.path.exists(GAMES_FILE):
        with open(GAMES_FILE, 'w') as f:
            json.dump({}, f)
    print("Bot is running...")
    bot.polling()
