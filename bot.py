
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
            welcome_text(ctx),
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
    if looks_urgent(update.message.text):
        await update.message.reply_text(
            tx(ctx, "emergency"),
            reply_markup=paths_kb(ctx)
        )
        return

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
        if anthropic_client is None:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")

        language_name = "русском" if l == "ru" else "English"
        system = (
            "Ты помощник по танцевально-двигательной терапии. "
            "Пользователь описал своё состояние. "
            "Ответь одним коротким тёплым предложением — что ты слышишь в его словах. "
            "Затем скажи что подберёшь подходящую практику. "
            "Отвечай на языке: " + language_name
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
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("practices", practices_command))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("BodyWave bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
