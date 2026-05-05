import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
import anthropic

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Clients
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── TEXTS ────────────────────────────────────────────────────────────────────
T = {
    "ru": {
        "welcome": (
            "Привет! Я *BodyWave* 🌊\n\n"
            "Твой помощник по танцевально‑двигательной терапии.\n"
            "Помогу тебе снять напряжение, заземлиться и почувствовать себя лучше "
            "через простые практики движения.\n\n"
            "Как хочешь начать сегодня?"
        ),
        "paths": ["🌿 Как я сейчас", "💧 Что я чувствую", "🌺 У меня запрос"],
        "p1_q": "Опиши в нескольких словах, как ты сейчас себя чувствуешь:\n_(напиши текстом или выбери ниже)_",
        "p1_hints": ["Устал(а)", "Тревожусь", "Злюсь", "Напряжён(а)"],
        "p2_q": "Что ты сейчас чувствуешь?\nВыбери одно или несколько:",
        "emotions": [
            "Тревога 🌀", "Усталость 🍂", "Злость 🌋", "Напряжение ⚡",
            "Грусть 🌧", "Пустота 🌫", "Стресс 🌊", "Онемение 🪨"
        ],
        "p3_q": "Что тебя беспокоит больше всего?",
        "topics": [
            "🌊 Стресс и работа", "🌀 Тревога", "🌺 Отношения",
            "⚡ Напряжение в теле", "🌿 Просто хочу подвигаться"
        ],
        "time_q": "Сколько у тебя времени?",
        "times": ["🐚 5–10 минут", "🌿 15–20 минут", "🌊 30+ минут"],
        "analyzing": "🌊 Подбираю практику для тебя...",
        "practice_intro": "Вот твоя практика:",
        "start_btn": "▶️ Начать",
        "next_btn": "✓ Готово — дальше",
        "finish_btn": "🌿 Завершить",
        "after_q": "Как ты сейчас после практики?",
        "after_opts": [
            "🌟 Стало легче", "🌊 Примерно так же",
            "🌿 Нужно ещё", "📖 Записать в дневник"
        ],
        "diary_saved": "✅ Сохранено в твой дневник!\n\n_{date}_",
        "again_btn": "🌊 Новая практика",
        "back_btn": "← Назад",
        "step_label": "Шаг {i} из {total}",
        "type_state": "💬 Напиши как ты себя чувствуешь, и я подберу практику:",
    },
    "en": {
        "welcome": (
            "Hi! I'm *BodyWave* 🌊\n\n"
            "Your dance-movement therapy assistant.\n"
            "I'll help you release tension, ground yourself and feel better "
            "through simple movement practices.\n\n"
            "How would you like to start today?"
        ),
        "paths": ["🌿 How I feel now", "💧 What I feel", "🌺 I have a request"],
        "p1_q": "Describe in a few words how you feel right now:\n_(type or choose below)_",
        "p1_hints": ["Tired", "Anxious", "Angry", "Tense"],
        "p2_q": "What are you feeling right now?\nChoose one or more:",
        "emotions": [
            "Anxiety 🌀", "Tiredness 🍂", "Anger 🌋", "Tension ⚡",
            "Sadness 🌧", "Emptiness 🌫", "Stress 🌊", "Numbness 🪨"
        ],
        "p3_q": "What bothers you most right now?",
        "topics": [
            "🌊 Work stress", "🌀 Anxiety", "🌺 Relationships",
            "⚡ Body tension", "🌿 Just want to move"
        ],
        "time_q": "How much time do you have?",
        "times": ["🐚 5–10 min", "🌿 15–20 min", "🌊 30+ min"],
        "analyzing": "🌊 Finding your practice...",
        "practice_intro": "Here is your practice:",
        "start_btn": "▶️ Start",
        "next_btn": "✓ Done — next",
        "finish_btn": "🌿 Finish",
        "after_q": "How do you feel after the practice?",
        "after_opts": [
            "🌟 Feeling lighter", "🌊 About the same",
            "🌿 Need more", "📖 Save to journal"
        ],
        "diary_saved": "✅ Saved to your journal!\n\n_{date}_",
        "again_btn": "🌊 New practice",
        "back_btn": "← Back",
        "step_label": "Step {i} of {total}",
        "type_state": "💬 Type how you feel and I will find a practice for you:",
    }
}

# ── PRACTICES DATABASE ───────────────────────────────────────────────────────
PRACTICES = {
    "ru": {
        "mini": [
            {
                "id": "grounding",
                "title": "🌿 Заземление",
                "subtitle": "5Basics · А. Гиршон · 10 мин",
                "tags": ["тревога", "стресс", "напряжение", "усталость"],
                "steps": [
                    ("Найди опору 🌿",
                     "Встань или сядь удобно. Почувствуй, как ноги касаются пола — "
                     "словно корни дерева уходят в землю.\n\nСделай *3 медленных вдоха* через нос — "
                     "живот расширяется на вдохе, опускается на выдохе."),
                    ("Почувствуй вес тела 💧",
                     "Позволь телу стать *тяжёлым*. Медленно перенеси вес с одной ноги на другую — "
                     "как вода перетекает из одного сосуда в другой.\n\nТаз — гидравлический центр, "
                     "волна расходится от него."),
                    ("Палсинг 🌊",
                     "Начни *мягкое раскачивание от пяток* — небольшое сгибание‑разгибание коленей.\n\n"
                     "Волна поднимается снизу вверх через весь позвоночник.\n"
                     "Не делай усилий — позволь волне самой найти свой ритм. 10–15 минут."),
                    ("Тишина 🐚",
                     "Замри. Послушай *остаточные пульсации* в теле.\n\n"
                     "Как ты сейчас? Что изменилось?\n\nПобудь в тишине 1–2 минуты."),
                ]
            },
            {
                "id": "lymph",
                "title": "💧 Движение лимфы",
                "subtitle": "Внутренний Океан · А. Гиршон · 10 мин",
                "tags": ["пустота", "онемение", "усталость"],
                "steps": [
                    ("Намерение 🌊",
                     "Осознай свою *текущую ситуацию*. Почувствуй, что тебе хочется сделать дальше.\n\n"
                     "Когда выбор сделан — сделай это с *прямотой и ясностью*, без колебаний."),
                    ("Прямота 💧",
                     "Каждое движение — *прицельно и осмысленно*.\n\n"
                     "От замысла к действию — кратчайший путь без лишнего.\n"
                     "Попробуй сделать несколько простых движений руками с полным намерением."),
                    ("Касание 🌿",
                     "Мягко *защипывай и приподнимай кожу* на руках, плечах — "
                     "освобождая фасцию под ней.\n\nЗатем мягко растягивай кожу от кончиков пальцев "
                     "к плечу — к сердцу. Это активирует лимфоток."),
                    ("Интеграция 🐚",
                     "Замедлись. Почувствуй *лёгкость в теле*.\n\n"
                     "Лимфа учит различать своё и чужое — буквально и метафорически.\n"
                     "Как ты сейчас?"),
                ]
            },
        ],
        "full": [
            {
                "id": "reich",
                "title": "🌋 Работа с мышечным панцирем",
                "subtitle": "По методу В. Райха · сегментная работа · 30 мин",
                "tags": ["злость", "напряжение", "стресс", "отношения"],
                "steps": [
                    ("Диагностика тела 🌺",
                     "Закрой глаза. Спроси себя: *где в теле живёт напряжение прямо сейчас?*\n\n"
                     "Найди одно конкретное место. Просто наблюдай без оценки.\n"
                     "Что ты там чувствуешь? Тепло, давление, пульсацию?"),
                    ("Дыхание в напряжение 💧",
                     "Направь дыхание прямо в то место.\n\n"
                     "На *вдохе* — расширяй это место изнутри, как раздувается парус.\n"
                     "На *выдохе* — отпускай.\n\n_5–7 дыхательных циклов_"),
                    ("Движение из напряжения 🌊",
                     "Включи *ритмичную музыку*. Позволь напряжённой части тела начать двигаться.\n\n"
                     "Не контролируй — следуй за импульсом, как волна следует за ветром.\n"
                     "Если это плечи — дай им двигаться. Если живот — дай ему."),
                    ("Выразительное движение 🌋",
                     "Усиль движение. Добавь *голос* — звук, крик, пение.\n\n"
                     "Грудной и диафрагмальный сегменты: удары, взмахи руками, глубокое дыхание.\n"
                     "Тазовый сегмент: вращение, прыжки, махи ногами.\n\nПозволь телу выразить всё накопленное."),
                    ("Интеграция 🌿",
                     "Замедлись. Лягь или сядь.\n\n"
                     "Почувствуй тело *целиком* — от макушки до стоп.\n"
                     "Что изменилось? Побудь с этим ощущением *2–3 минуты*.\n\n"
                     "Можешь записать что почувствовал(а)."),
                ]
            },
            {
                "id": "five_rhythms",
                "title": "🎵 Танец пяти ритмов",
                "subtitle": "Структурная интеграция · 30 мин",
                "tags": ["работа", "пустота", "движение", "творчество"],
                "steps": [
                    ("Flowing 🌊",
                     "*Плавные, мягкие, округлые движения.*\n\n"
                     "Представь, что ты — вода. Твои движения текут без усилий, "
                     "перетекают из одной формы в другую.\n\n_5 минут_"),
                    ("Staccato ⚡",
                     "*Резкие, сильные, чёткие движения.*\n\n"
                     "Это 'мужская' энергия. Каждое движение — с намерением, с силой, "
                     "с точкой начала и конца.\n\n_5 минут_"),
                    ("Chaos 🌀",
                     "*Хаотические движения.*\n\n"
                     "Отпусти контроль. Позволь телу двигаться непредсказуемо — "
                     "как будто ты расплавился и двигаешься сам по себе.\n\n_5 минут_"),
                    ("Lyrical 🌸",
                     "*Тонкие, изящные движения.*\n\n"
                     "'Полёт бабочки' или 'падающего листа'. "
                     "Лёгкость, невесомость, игривость.\n\n_5 минут_"),
                    ("Stillness 🐚",
                     "*Движение в неподвижности.*\n\n"
                     "Наблюдай за первичными импульсами движения. 'Пульсирующая статуя'.\n\n"
                     "Как ты сейчас? Что открылось? _5 минут_"),
                ]
            },
        ]
    },
    "en": {
        "mini": [
            {
                "id": "grounding",
                "title": "🌿 Grounding",
                "subtitle": "5Basics · A. Girshon · 10 min",
                "tags": ["anxiety", "stress", "tension", "tiredness"],
                "steps": [
                    ("Find your ground 🌿",
                     "Stand or sit comfortably. Feel your feet on the floor — "
                     "like roots of a tree going deep into the earth.\n\nTake *3 slow breaths* through the nose — "
                     "belly expands on inhale, drops on exhale."),
                    ("Feel your weight 💧",
                     "Let the body become *heavy*. Slowly shift weight from one foot to the other — "
                     "like water flowing from one vessel to another.\n\nThe pelvis is the hydraulic center, "
                     "the wave radiates from it."),
                    ("Pulsing 🌊",
                     "Begin *gentle rocking from the heels* — small bends and straightens of the knees.\n\n"
                     "The wave rises upward through the whole spine.\n"
                     "Don't try — let the wave find its own rhythm. 10–15 minutes."),
                    ("Stillness 🐚",
                     "Freeze. Listen to the *residual pulses* in your body.\n\n"
                     "How are you now? What has changed?\n\nStay in silence for 1–2 minutes."),
                ]
            },
            {
                "id": "lymph",
                "title": "💧 Lymph Flow",
                "subtitle": "Inner Ocean · A. Girshon · 10 min",
                "tags": ["emptiness", "numbness", "tiredness"],
                "steps": [
                    ("Intention 🌊",
                     "Become aware of your *current situation*. Feel what you want to do next.\n\n"
                     "When the choice is made — do it with *directness and clarity*, without hesitation."),
                    ("Directness 💧",
                     "Each movement — *precise and purposeful*.\n\n"
                     "From intention to action — the shortest path without detours.\n"
                     "Try a few simple arm movements with full intention."),
                    ("Touch 🌿",
                     "Gently *pinch and lift the skin* on your arms and shoulders — "
                     "freeing the fascia beneath.\n\nThen gently stretch the skin from fingertips "
                     "toward the shoulder — toward the heart. This activates lymph flow."),
                    ("Integration 🐚",
                     "Slow down. Feel *lightness in the body*.\n\n"
                     "Lymph teaches us to distinguish our own from others — literally and metaphorically.\n"
                     "How are you now?"),
                ]
            },
        ],
        "full": [
            {
                "id": "reich",
                "title": "🌋 Working with Muscle Armor",
                "subtitle": "W. Reich method · segmental work · 30 min",
                "tags": ["anger", "tension", "stress", "relationships"],
                "steps": [
                    ("Body scan 🌺",
                     "Close your eyes. Ask yourself: *where does tension live in my body right now?*\n\n"
                     "Find one specific place. Just observe without judgment.\n"
                     "What do you feel there? Warmth, pressure, pulsation?"),
                    ("Breathe into tension 💧",
                     "Direct your breath right into that place.\n\n"
                     "On *inhale* — expand from inside, like a sail filling with wind.\n"
                     "On *exhale* — let go.\n\n_5–7 breath cycles_"),
                    ("Move from tension 🌊",
                     "Turn on *rhythmic music*. Let the tense part of the body start moving.\n\n"
                     "Don't control — follow the impulse, like a wave follows the wind.\n"
                     "If it's shoulders — let them move. If it's the belly — let it."),
                    ("Expressive movement 🌋",
                     "Amplify the movement. Add *voice* — sound, shout, singing.\n\n"
                     "Chest and diaphragm: strikes, arm sweeps, deep breathing.\n"
                     "Pelvic segment: rotation, jumps, leg swings.\n\nLet the body express everything accumulated."),
                    ("Integration 🌿",
                     "Slow down. Lie or sit.\n\n"
                     "Feel the body *as a whole* — from crown to feet.\n"
                     "What changed? Stay with this sensation for *2–3 minutes*.\n\n"
                     "You may write down what you felt."),
                ]
            },
            {
                "id": "five_rhythms",
                "title": "🎵 Dance of Five Rhythms",
                "subtitle": "Structural Integration · 30 min",
                "tags": ["work", "emptiness", "movement", "creativity"],
                "steps": [
                    ("Flowing 🌊",
                     "*Smooth, soft, rounded movements.*\n\n"
                     "Imagine you are water. Your movements flow without effort, "
                     "shifting from one form to another.\n\n_5 minutes_"),
                    ("Staccato ⚡",
                     "*Sharp, strong, clear movements.*\n\n"
                     "This is active energy. Each movement — with intention, with power, "
                     "with a clear beginning and end.\n\n_5 minutes_"),
                    ("Chaos 🌀",
                     "*Chaotic movements.*\n\n"
                     "Release control. Let the body move unpredictably — "
                     "as if you have melted and are moving on your own.\n\n_5 minutes_"),
                    ("Lyrical 🌸",
                     "*Delicate, graceful movements.*\n\n"
                     "'Flight of a butterfly' or 'falling leaf'. "
                     "Lightness, weightlessness, playfulness.\n\n_5 minutes_"),
                    ("Stillness 🐚",
                     "*Movement in stillness.*\n\n"
                     "Observe the primary movement impulses. 'Pulsating statue'.\n\n"
                     "How are you now? What has opened? _5 minutes_"),
                ]
            },
        ]
    }
}

# ── HELPERS ──────────────────────────────────────────────────────────────────
def lang(ctx):
    return ctx.user_data.get("lang", "ru")

def tx(ctx, key, **kwargs):
    text = T[lang(ctx)].get(key, key)
    return text.format(**kwargs) if kwargs else text

def kb(buttons, cols=1):
    """Build InlineKeyboardMarkup from list of (text, callback_data)."""
    rows = []
    row = []
    for i, (text, data) in enumerate(buttons):
        row.append(InlineKeyboardButton(text, callback_data=data))
        if len(row) == cols:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)

def paths_kb(ctx):
    paths = tx(ctx, "paths")
    return kb([(p, f"path_{i}") for i, p in enumerate(paths)], cols=1)

def pick_practice(user_state, lang_code):
    """Pick best practice based on user state using AI."""
    pracs = PRACTICES[lang_code]
    emotion = user_state.get("emotion", "")
    topic = user_state.get("topic", "")
    time_choice = user_state.get("time", "")

    # Determine mini vs full
    is_full = "30" in time_choice or topic != ""

    pool = pracs["full"] if is_full else pracs["mini"]

    # Simple tag matching
    query = (emotion + " " + topic).lower()
    best = pool[0]
    best_score = 0
    for p in pool:
        score = sum(1 for tag in p["tags"] if tag in query)
        if score > best_score:
            best_score = score
            best = p

    return best, "full" if is_full else "mini"

# ── HANDLERS ─────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    keyboard = kb([
        ("🇷🇺 Русский", "lang_ru"),
        ("🇬🇧 English", "lang_en"),
    ], cols=2)
    await update.message.reply_text(
        "Привет! / Hello! 🌊\n\nВыбери язык / Choose language:",
        reply_markup=keyboard
    )

async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # ── Language ──
    if data.startswith("lang_"):
        ctx.user_data["lang"] = data.split("_")[1]
        await query.edit_message_text(
            tx(ctx, "welcome"),
            parse_mode="Markdown",
            reply_markup=paths_kb(ctx)
        )

    # ── Path selection ──
    elif data.startswith("path_"):
        path = int(data.split("_")[1])
        ctx.user_data["path"] = path
        l = lang(ctx)

        if path == 0:  # How I feel now — free text
            ctx.user_data["awaiting_text"] = True
            hints = tx(ctx, "p1_hints")
            hint_kb = kb([(h, f"hint_{h}") for h in hints], cols=2)
            await query.edit_message_text(
                tx(ctx, "p1_q"),
                parse_mode="Markdown",
                reply_markup=hint_kb
            )

        elif path == 1:  # What I feel — emotions
            emotions = tx(ctx, "emotions")
            emo_kb = kb([(e, f"emo_{e}") for e in emotions], cols=2)
            await query.edit_message_text(
                tx(ctx, "p2_q"),
                parse_mode="Markdown",
                reply_markup=emo_kb
            )

        elif path == 2:  # I have a request — topics
            topics = tx(ctx, "topics")
            topic_kb = kb([(t, f"topic_{i}") for i, t in enumerate(topics)], cols=1)
            await query.edit_message_text(
                tx(ctx, "p3_q"),
                parse_mode="Markdown",
                reply_markup=topic_kb
            )

    # ── Hint (quick emotion) ──
    elif data.startswith("hint_"):
        emotion = data[5:]
        ctx.user_data["emotion"] = emotion
        ctx.user_data["awaiting_text"] = False
        await show_time_picker(query, ctx)

    # ── Emotion selected ──
    elif data.startswith("emo_"):
        emotion = data[4:]
        ctx.user_data["emotion"] = emotion
        await show_time_picker(query, ctx)

    # ── Topic selected ──
    elif data.startswith("topic_"):
        idx = int(data.split("_")[1])
        topics = tx(ctx, "topics")
        ctx.user_data["topic"] = topics[idx]
        await show_time_picker(query, ctx)

    # ── Time selected ──
    elif data.startswith("time_"):
        idx = int(data.split("_")[1])
        times = tx(ctx, "times")
        ctx.user_data["time"] = times[idx]
        await show_practice_choice(query, ctx)

    # ── Start practice ──
    elif data.startswith("start_"):
        prac_id = data[6:]
        l = lang(ctx)
        all_pracs = PRACTICES[l]["mini"] + PRACTICES[l]["full"]
        practice = next((p for p in all_pracs if p["id"] == prac_id), None)
        if practice:
            ctx.user_data["practice"] = practice
            ctx.user_data["step"] = 0
            await show_step(query, ctx)

    # ── Next step ──
    elif data == "next_step":
        ctx.user_data["step"] = ctx.user_data.get("step", 0) + 1
        await show_step(query, ctx)

    # ── After practice ──
    elif data.startswith("after_"):
        idx = int(data.split("_")[1])
        opts = tx(ctx, "after_opts")
        chosen = opts[idx]

        if idx == 3:  # Save to diary
            from datetime import date
            d = date.today().strftime("%d.%m.%Y")
            practice = ctx.user_data.get("practice", {})
            text = tx(ctx, "diary_saved", date=d)
            text += f"\n\n*{practice.get('title', '')}*"
        else:
            text = chosen

        restart_kb = kb([(tx(ctx, "again_btn"), "restart")], cols=1)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=restart_kb)

    # ── Restart ──
    elif data == "restart":
        ctx.user_data.pop("practice", None)
        ctx.user_data.pop("step", None)
        ctx.user_data.pop("emotion", None)
        ctx.user_data.pop("topic", None)
        ctx.user_data.pop("time", None)
        await query.edit_message_text(
            tx(ctx, "welcome"),
            parse_mode="Markdown",
            reply_markup=paths_kb(ctx)
        )

async def show_time_picker(query, ctx):
    times = tx(ctx, "times")
    time_kb = kb([(t, f"time_{i}") for i, t in enumerate(times)], cols=1)
    await query.edit_message_text(
        tx(ctx, "time_q"),
        reply_markup=time_kb
    )

async def show_practice_choice(query, ctx):
    await query.edit_message_text(tx(ctx, "analyzing"))
    l = lang(ctx)
    practice, ptype = pick_practice(ctx.user_data, l)
    ctx.user_data["practice"] = practice

    text = (
        f"{tx(ctx, 'practice_intro')}\n\n"
        f"*{practice['title']}*\n"
        f"_{practice['subtitle']}_"
    )
    start_kb = kb([(tx(ctx, "start_btn"), f"start_{practice['id']}")], cols=1)
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=start_kb)

async def show_step(query, ctx):
    practice = ctx.user_data.get("practice")
    step_idx = ctx.user_data.get("step", 0)
    steps = practice["steps"]
    total = len(steps)

    if step_idx >= total:
        # After practice
        opts = tx(ctx, "after_opts")
        after_kb = kb([(o, f"after_{i}") for i, o in enumerate(opts)], cols=1)
        await query.edit_message_text(
            tx(ctx, "after_q"),
            reply_markup=after_kb
        )
        return

    title, body = steps[step_idx]
    progress = "●" * (step_idx + 1) + "○" * (total - step_idx - 1)
    step_label = tx(ctx, "step_label", i=step_idx + 1, total=total)
    is_last = step_idx == total - 1

    text = f"_{step_label}_ {progress}\n\n*{title}*\n\n{body}"
    btn_text = tx(ctx, "finish_btn") if is_last else tx(ctx, "next_btn")
    step_kb = kb([(btn_text, "next_step")], cols=1)

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=step_kb)

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle free text input for state description."""
    if not ctx.user_data.get("awaiting_text"):
        await update.message.reply_text(
            tx(ctx, "type_state")
        )
        return

    ctx.user_data["awaiting_text"] = False
    user_text = update.message.text
    ctx.user_data["emotion"] = user_text

    # Use AI to analyze and suggest
    try:
        l = lang(ctx)
        system = (
            "Ты помощник по танцевально-двигательной терапии. "
            "Пользователь описал своё состояние. "
            "Ответь одним коротким тёплым предложением — что ты слышишь в его словах. "
            "Затем скажи что подберёшь подходящую практику. "
            "Отвечай на языке: " + l
        )
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            messages=[{"role": "user", "content": user_text}],
            system=system
        )
        reply = response.content[0].text
    except Exception:
        reply = "Понял тебя 🌊" if l == "ru" else "I hear you 🌊"

    times = tx(ctx, "times")
    time_kb = kb([(t, f"time_{i}") for i, t in enumerate(times)], cols=1)
    await update.message.reply_text(
        f"{reply}\n\n{tx(ctx, 'time_q')}",
        reply_markup=time_kb
    )

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("BodyWave bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
