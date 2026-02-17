"""
Tamaani: The Mine of Consent
Telegram-бот прототип — минимальная карточная механика
Требует: pip install python-telegram-bot==20.x
Запуск: BOT_TOKEN=... python tamaani_bot.py
"""

import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

logging.basicConfig(level=logging.INFO)

# ─── КАРТОЧКИ ДЕЙСТВИЙ ──────────────────────────────────────────────────────

# Карточки игроков (хорошие инструменты)
PLAYER_CARDS = [
    {"id": "lawsuit",     "name": "⚖️ Судебный иск",         "nature": +2, "profit": -1, "time": 3, "desc": "Стратегическая тяжба по ILO 169 / UNDRIP"},
    {"id": "intl_adv",    "name": "🌐 Международная адвокация","nature": +1, "profit": 0,  "time": 3, "desc": "ООН, IACtHR, Special Rapporteur"},
    {"id": "fpic",        "name": "📋 СПОС / FPIC",           "nature": +2, "profit": +1, "time": 0, "desc": "Требование консультаций — право вето"},
    {"id": "ngo",         "name": "🤝 Союз с НПО",            "nature": +2, "profit": -1, "time": 2, "desc": "Amnesty, Survival, медиа-кампания"},
    {"id": "direct",      "name": "🏕️ Прямое действие",       "nature": +3, "profit": -2, "time": 3, "desc": "Блокады, лагеря, неповиновение"},
    {"id": "negotiation", "name": "🤲 Переговоры и IBA",      "nature": +1, "profit": +2, "time": 2, "desc": "Revenue-sharing, соглашения"},
    {"id": "rights",      "name": "🌿 Права природы",         "nature": +2, "profit": -1, "time": 2, "desc": "Реки и леса как субъекты права"},
]

# Карточки оппозиции (автоматические события)
OPPOSITION_CARDS = [
    {"id": "police",      "name": "🚔 Полицейские операции",  "nature": -3, "profit": +2, "desc": "Подавление протестов"},
    {"id": "pr",          "name": "📢 PR-кампания корпорации","nature": -1, "profit": +1, "desc": "Медиа работают против"},
    {"id": "lobby",       "name": "💼 Лоббирование",          "nature": -2, "profit": +2, "desc": "Изменение законов в пользу компании"},
    {"id": "divide",      "name": "✂️ Разделение общины",     "nature": -2, "profit": +1, "desc": "Подкуп местных элит"},
    {"id": "econ",        "name": "💸 Экономическое давление", "nature": -1, "profit": +2, "desc": "Угрозы рабочими местами"},
    {"id": "isds",        "name": "🏛️ Международный арбитраж","nature": -1, "profit": +3, "desc": "ISDS — иск против государства"},
    {"id": "false_acc",   "name": "📰 Ложные обвинения",      "nature": -2, "profit": +1, "desc": "Лидеров общины арестовывают"},
    {"id": "land",        "name": "🏗️ Захват земли",          "nature": -3, "profit": +2, "desc": "Добыча начинается без согласия"},
]

# ─── КЕЙСЫ — СТАРТОВЫЕ СЦЕНАРИИ ────────────────────────────────────────────

CASES = {
    "anbara": {
        "id": "anbara",
        "name": "🇷🇺 Алмазы Анбара + Эвенки",
        "region": "Якутия, Россия",
        "resource": "Алмазы",
        "intro": (
            "📍 *Якутия, 2010-е*\n\n"
            "Компания «Алмазы Анбара» планирует рудник на *священной реке* — "
            "единственном источнике питьевой воды, рядом с оленьими пастбищами эвенков.\n\n"
            "Единогласное голосование всех жителей села — *против*.\n"
            "Ассоциация коренных народов активно включилась.\n\n"
            "Сможет ли община остановить выдачу лицензии?"
        ),
        "nature_start": 6,   # сильная позиция — единство общины
        "profit_start": 4,   # ресурсов немного, но есть
        "opp_weights": {     # какие карты оппозиции чаще появляются
            "lobby": 3, "false_acc": 2, "pr": 2,
            "police": 1, "divide": 1, "econ": 1, "isds": 1, "land": 1,
        },
        "real_outcome": "ПОБЕДА",
        "real_outcome_text": (
            "📖 *Как было в реальности:*\n"
            "Министр охраны природы Якутии отказал в выдаче лицензии.\n"
            "Первый раз в Якутии коренной народ остановил добывающий проект через "
            "публичные слушания и единогласное голосование общины.\n\n"
            "_Факторы победы: единство, статус священного места, критическая инфраструктура (вода), юридическая поддержка._"
        ),
    },

    "norilsk": {
        "id": "norilsk",
        "name": "🇷🇺 Норильск Никель + Таймыр",
        "region": "Таймыр, Красноярский край",
        "resource": "Никель, палладий, медь",
        "intro": (
            "📍 *Таймыр, наши дни*\n\n"
            "Норникель работает здесь с 1930-х. ~10 000 человек: долганы, ненцы, "
            "нганасаны, эвенки, энцы.\n\n"
            "90% оленьих пастбищ недоступны. SO₂ — почти 2 млн тонн в год. "
            "Средняя продолжительность жизни коренных — на 15–20 лет меньше.\n"
            "2020: разлив 21 000 тонн дизтоплива.\n\n"
            "«Этнологическая экспертиза» есть — но без права вето.\n\n"
            "Можно ли что-то изменить изнутри?"
        ),
        "nature_start": 3,   # уже сильно повреждена
        "profit_start": 6,   # корпорация богатая, ресурсы есть
        "opp_weights": {
            "police": 3, "lobby": 3, "land": 2, "false_acc": 2,
            "pr": 2, "econ": 2, "divide": 1, "isds": 1,
        },
        "real_outcome": "ПРОВАЛ",
        "real_outcome_text": (
            "📖 *Как было в реальности:*\n"
            "Культурный геноцид через уничтожение среды жизнеобеспечения продолжается.\n"
            "Прирост состояния Потанина за 5 лет — в 1197 раз больше всех компенсаций "
            "коренным народам за тот же период.\n\n"
            "_СПОС: имитация. «Консультация» без права вето — не согласие._"
        ),
    },

    "diavik": {
        "id": "diavik",
        "name": "🇨🇦 Diavik Diamond + Dene",
        "region": "Северо-Западные территории, Канада",
        "resource": "Алмазы",
        "intro": (
            "📍 *Северо-Западные территории, 2000-е*\n\n"
            "Rio Tinto открывает алмазный рудник на озере Lac de Gras. "
            "Народы дене, метис и инуит — рядом.\n\n"
            "Канадское законодательство требует консультаций. "
            "Возможны IBA — Impact Benefit Agreements: рабочие места, доля в контрактах, мониторинг.\n\n"
            "Но карибу уже страдают. Озеро загрязняется.\n\n"
            "Компромисс или капитуляция — где граница?"
        ),
        "nature_start": 5,
        "profit_start": 5,
        "opp_weights": {
            "econ": 3, "pr": 2, "divide": 2, "lobby": 2,
            "land": 1, "isds": 1, "police": 1, "false_acc": 0,
        },
        "real_outcome": "КОМПРОМИСС",
        "real_outcome_text": (
            "📖 *Как было в реальности:*\n"
            "IBA подписаны с 5 группами коренных народов: рабочие места, "
            "преференции в контрактах, участие в экологическом мониторинге.\n"
            "Проект работает до сих пор.\n\n"
            "Экологический ущерб есть. Полного контроля нет. "
            "Но это — один из лучших примеров переговорного участия в Канаде.\n\n"
            "_Компромисс — это не победа и не поражение. Это то, с чем нужно жить дальше._"
        ),
    },
}

def weighted_opp_deck(case: dict) -> list:
    """Строит колоду оппозиции с весами под конкретный кейс."""
    weights = case.get("opp_weights", {})
    deck = []
    for card in OPPOSITION_CARDS:
        count = weights.get(card["id"], 1)
        deck.extend([card] * count)
    random.shuffle(deck)
    return deck

# Роли игроков
ROLES = [
    {"id": "chief",       "name": "👴 Вождь",      "bonus": "direct",    "bonus_text": "+1 🌿 к Прямому действию"},
    {"id": "journalist",  "name": "📷 Журналист",   "bonus": "ngo",       "bonus_text": "+1 🌿 к Союзу с НПО"},
    {"id": "activist",    "name": "✊ Активист",    "bonus": "rights",    "bonus_text": "+1 🌿 к Правам природы"},
    {"id": "lawyer",      "name": "⚖️ Юрист",      "bonus": "lawsuit",   "bonus_text": "-1 ⏱ к Судебному иску"},
]

# ─── СОСТОЯНИЕ ИГРЫ ─────────────────────────────────────────────────────────

games = {}  # chat_id → game_state

def new_game(num_players: int, case=None) -> dict:
    deck = PLAYER_CARDS * 2  # 14 карт
    random.shuffle(deck)

    if case:
        opp_deck = weighted_opp_deck(case)
    else:
        opp_deck = OPPOSITION_CARDS * 2
        random.shuffle(opp_deck)

    hand_size = 3
    hands = {}
    for i in range(num_players):
        hands[i] = deck[i*hand_size:(i+1)*hand_size]
    remaining = deck[num_players*hand_size:]

    roles = random.sample(ROLES, min(num_players, len(ROLES)))

    nature_start = case["nature_start"] if case else 5
    profit_start = case["profit_start"] if case else 5

    return {
        "nature": nature_start,
        "profit": profit_start,
        "turn": 0,
        "max_turns": 8,
        "current_player": 0,
        "num_players": num_players,
        "hands": hands,
        "deck": remaining,
        "opp_deck": opp_deck,
        "roles": roles,
        "log": [],
        "phase": "play",
        "last_opp": None,
        "case": case,
    }

def get_role(game: dict, player_idx: int) -> dict | None:
    if player_idx < len(game["roles"]):
        return game["roles"][player_idx]
    return None

def apply_role_bonus(card: dict, role: dict | None) -> dict:
    """Применяет бонус роли к карточке."""
    if role and role["bonus"] == card["id"]:
        modified = card.copy()
        modified["nature"] = card["nature"] + 1  # бонус +1 природа
        return modified
    return card

def draw_card(game: dict, player_idx: int):
    """Добирает карту в руку если есть в колоде."""
    if game["deck"]:
        game["hands"][player_idx].append(game["deck"].pop())

def play_turn(game: dict, player_idx: int, card_idx: int) -> str:
    """Выполняет ход. Возвращает описание результата."""
    hand = game["hands"][player_idx]
    if card_idx >= len(hand):
        return "❌ Нет такой карты"
    
    player_card = hand[card_idx]
    role = get_role(game, player_idx)
    player_card = apply_role_bonus(player_card, role)
    
    # Ход оппозиции — случайная карта из колоды
    if game["opp_deck"]:
        opp_card = game["opp_deck"].pop(0)
        game["opp_deck"].append(opp_card)  # кладём в конец (цикличная)
    else:
        opp_card = random.choice(OPPOSITION_CARDS)
    game["last_opp"] = opp_card
    
    # Применяем эффекты
    nature_delta = player_card["nature"] + opp_card["nature"]
    profit_delta = player_card["profit"] + opp_card["profit"]
    
    game["nature"] = max(0, min(10, game["nature"] + nature_delta))
    game["profit"] = max(0, min(10, game["profit"] + profit_delta))
    
    # Убираем сыгранную карту
    hand.pop(card_idx)
    draw_card(game, player_idx)
    
    game["turn"] += 1
    game["current_player"] = (player_idx + 1) % game["num_players"]
    
    # Лог
    entry = (
        f"Ход {game['turn']}: {role['name'] if role else 'Игрок'} → "
        f"{player_card['name']} vs {opp_card['name']} | "
        f"🌿{nature_delta:+} 💰{profit_delta:+}"
    )
    game["log"].append(entry)
    
    return entry

def check_end(game: dict) -> str | None:
    """Проверяет конец игры. None = продолжаем."""
    if game["nature"] <= 0:
        return "lose_nature"
    if game["profit"] <= 0:
        return "lose_profit"
    if game["nature"] >= 9 and game["profit"] >= 6:
        return "win_early"
    if game["turn"] >= game["max_turns"]:
        if game["nature"] >= 5 and game["profit"] >= 5:
            return "win"
        else:
            return "lose_time"
    return None

# ─── ФОРМАТИРОВАНИЕ ─────────────────────────────────────────────────────────

def bar(value: int, max_val: int = 10) -> str:
    filled = round(value / max_val * 8)
    return "█" * filled + "░" * (8 - filled)

def status_text(game: dict) -> str:
    n = game["nature"]
    p = game["profit"]
    t = game["turn"]
    mt = game["max_turns"]
    return (
        f"🌿 Природа: {n}/10  {bar(n)}\n"
        f"💰 Прибыль: {p}/10  {bar(p)}\n"
        f"⏱ Ход: {t}/{mt}\n"
    )

def hand_keyboard(hand: list, player_idx: int) -> InlineKeyboardMarkup:
    buttons = []
    for i, card in enumerate(hand):
        label = f"{card['name']} (🌿{card['nature']:+} 💰{card['profit']:+})"
        buttons.append([InlineKeyboardButton(label, callback_data=f"play_{player_idx}_{i}")])
    return InlineKeyboardMarkup(buttons)

def end_text(result: str, game: dict) -> str:
    endings = {
        "lose_nature": "💔 ПРИРОДА УНИЧТОЖЕНА\nШахта запущена. Земля общины разрыта. Это можно было предотвратить.",
        "lose_profit": "💔 ОБЩЕСТВО ИСТОЩЕНО\nБез ресурсов борьба невозможна. Голоса не услышаны.",
        "win_early":   "🏆 ДОСРОЧНАЯ ПОБЕДА\nОбщина отстояла землю и сохранила баланс. СПОС соблюдён.",
        "win":         "✅ ВЫЖИЛИ\nНелегко. Но природа цела, ресурсы есть. Борьба продолжается.",
        "lose_time":   "⏰ ВРЕМЯ ВЫШЛО\nСлишком мало сделано. Корпорация воспользовалась паузой.",
    }
    summary = "\n".join(game["log"][-4:]) if game["log"] else ""
    text = f"{endings.get(result, '?')}\n\n{'─'*30}\nПоследние ходы:\n{summary}"
    case = game.get("case")
    if case:
        text += f"\n\n{'─'*30}\n{case['real_outcome_text']}"
    return text

# ─── КОМАНДЫ БОТА ────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🪨 *Tamaani: The Mine of Consent*\n\n"
        "Добывающая компания хочет зайти на земли коренного народа. "
        "Ваша задача — защитить территорию, не потеряв ни природу, ни ресурсы для борьбы.\n\n"

        "━━━━━━━━━━━━━━━\n"
        "*Как играть*\n\n"
        "1️⃣ Выбери кейс — реальная история из жизни коренных народов\n"
        "2️⃣ Получи роль (вождь, юрист, активист, журналист) — у каждой свой бонус\n"
        "3️⃣ Каждый ход играй карту действия из руки\n"
        "4️⃣ В ответ система разыгрывает карту корпорации/государства\n"
        "5️⃣ Следи за двумя счётчиками — они должны остаться выше нуля\n\n"

        "━━━━━━━━━━━━━━━\n"
        "*Два счётчика*\n\n"
        "🌿 *Природа* — состояние земли, воды, пастбищ\n"
        "Падает от полицейских операций, захвата земли, загрязнения\n\n"
        "💰 *Прибыль* — ресурсы общины для борьбы\n"
        "Растёт от переговоров и соглашений, падает от прямых действий\n\n"
        "Если любой счётчик достигнет 0 — игра проиграна.\n"
        "Продержитесь 8 ходов с обоими выше 5 — выжили.\n\n"

        "━━━━━━━━━━━━━━━\n"
        "*Карты действий (твои)*\n\n"
        "⚖️ Судебный иск — долго, но сильно защищает природу\n"
        "📋 СПОС/FPIC — требование права вето, дешевле всего\n"
        "🤝 Союз с НПО — медиадавление на корпорацию\n"
        "🏕️ Прямое действие — блокады и лагеря, эффективно но дорого\n"
        "🤲 Переговоры и IBA — соглашения с долей в прибыли\n"
        "🌐 Международная адвокация — ООН, спецдокладчик\n"
        "🌿 Права природы — реки и леса как субъекты права\n\n"

        "━━━━━━━━━━━━━━━\n"
        "*Начать игру*\n\n"
        "/play1 — соло\n"
        "/play2 — вдвоём\n"
        "/play3 — втроём\n"
        "/play4 — вчетвером\n\n"
        "_После выбора числа игроков предложу выбрать кейс_",
        parse_mode="Markdown"
    )

async def show_case_keyboard(update: Update, num_players: int):
    buttons = [
        [InlineKeyboardButton("🇷🇺 Алмазы Анбара + Эвенки", callback_data=f"case_anbara_{num_players}")],
        [InlineKeyboardButton("🇷🇺 Норильск Никель + Таймыр", callback_data=f"case_norilsk_{num_players}")],
        [InlineKeyboardButton("🇨🇦 Diavik + Dene (Канада)", callback_data=f"case_diavik_{num_players}")],
        [InlineKeyboardButton("▶ Без кейса", callback_data=f"case_none_{num_players}")],
    ]
    await update.message.reply_text(
        f"Игроков: {num_players}\n\nВыбери кейс-сценарий:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def play_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE, num_players: int):
    await show_case_keyboard(update, num_players)

async def play1(u, c): await play_cmd(u, c, 1)
async def play2(u, c): await play_cmd(u, c, 2)
async def play3(u, c): await play_cmd(u, c, 3)
async def play4(u, c): await play_cmd(u, c, 4)

async def case_anbara_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await show_case_keyboard(update, 1)

def start_game_with_case(cid: int, num_players: int, case_id: str) -> dict:
    case = CASES.get(case_id) if case_id != "none" else None
    game = new_game(num_players, case)
    games[cid] = game
    return game

async def hand_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    game = games.get(cid)
    if not game:
        await update.message.reply_text("Нет активной игры. /play1 чтобы начать.")
        return
    if game["phase"] == "end":
        await update.message.reply_text("Игра завершена. /play1 — новая игра.")
        return

    cp = game["current_player"]
    role = get_role(game, cp)
    hand = game["hands"][cp]
    role_text = f"Роль: {role['name']} ({role['bonus_text']})" if role else ""

    await update.message.reply_text(
        f"🎴 *Игрок {cp+1}* — твой ход!\n{role_text}\n\n"
        f"{status_text(game)}\n"
        "Выбери карту:",
        reply_markup=hand_keyboard(hand, cp),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cid = update.effective_chat.id

    data = query.data

    # ── Выбор кейса ──
    if data.startswith("case_"):
        parts = data.split("_")
        # case_anbara_2 → parts = ["case", "anbara", "2"]
        # case_none_1  → parts = ["case", "none", "1"]
        case_id = parts[1]
        num_players = int(parts[2])
        game = start_game_with_case(cid, num_players, case_id)
        case = game.get("case")

        roles_text = "\n".join(
            f"  Игрок {i+1}: {r['name']} — {r['bonus_text']}"
            for i, r in enumerate(game["roles"])
        )

        if case:
            await query.message.reply_text(
                case["intro"],
                parse_mode="Markdown"
            )

        await query.message.reply_text(
            f"🎮 Игра начата! ({num_players} игрок{'а' if num_players > 1 else ''})\n\n"
            f"*Роли:*\n{roles_text}\n\n"
            f"{status_text(game)}\n"
            "/hand — твои карты",
            parse_mode="Markdown"
        )
        return

    # ── Ход карточкой ──
    if data.startswith("play_"):
        game = games.get(cid)
        if not game:
            return
        _, p_str, c_str = data.split("_")
        player_idx = int(p_str)
        card_idx = int(c_str)

        if player_idx != game["current_player"]:
            await query.message.reply_text("⚠️ Сейчас не твой ход.")
            return

        result_text = play_turn(game, player_idx, card_idx)
        end = check_end(game)

        opp = game["last_opp"]
        opp_line = f"\n🏭 Оппозиция: *{opp['name']}* — {opp['desc']}" if opp else ""

        msg = f"✅ {result_text}{opp_line}\n\n{status_text(game)}"

        if end:
            game["phase"] = "end"
            await query.message.reply_text(msg, parse_mode="Markdown")
            await query.message.reply_text(end_text(end, game), parse_mode="Markdown")
        else:
            cp = game["current_player"]
            role = get_role(game, cp)
            hand = game["hands"][cp]
            role_text = f"Роль: {role['name']}" if role else ""
            await query.message.reply_text(
                f"{msg}\n\n🎴 *Игрок {cp+1}* — {role_text}\nВыбери карту:",
                reply_markup=hand_keyboard(hand, cp),
                parse_mode="Markdown"
            )

async def status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    game = games.get(cid)
    if not game:
        await update.message.reply_text("Нет активной игры.")
        return
    case = game.get("case")
    case_line = f"📍 *{case['name']}* — {case['region']}\n" if case else ""
    await update.message.reply_text(case_line + status_text(game), parse_mode="Markdown")

async def log_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    game = games.get(cid)
    if not game or not game["log"]:
        await update.message.reply_text("История пуста.")
        return
    await update.message.reply_text("\n".join(game["log"]))

async def roles_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    game = games.get(cid)
    if not game:
        await update.message.reply_text("Нет активной игры.")
        return
    text = "\n".join(
        f"Игрок {i+1}: {r['name']} — {r['bonus_text']}"
        for i, r in enumerate(game["roles"])
    )
    await update.message.reply_text(f"🎭 Роли:\n{text}")

async def stop_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    if cid in games:
        del games[cid]
    await update.message.reply_text("Игра остановлена.")

# ─── ЗАПУСК ──────────────────────────────────────────────────────────────────

import os

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("Укажи BOT_TOKEN=... в переменных окружения")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play1", play1))
    app.add_handler(CommandHandler("play2", play2))
    app.add_handler(CommandHandler("play3", play3))
    app.add_handler(CommandHandler("play4", play4))
    app.add_handler(CommandHandler("hand", hand_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("log", log_cmd))
    app.add_handler(CommandHandler("roles", roles_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен. Ctrl+C для остановки.")
    app.run_polling()

if __name__ == "__main__":
    main()
