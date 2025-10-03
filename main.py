import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter
import datetime

# 🔑 Sizning ma’lumotlaringiz
API_TOKEN = "7549621572:AAHDbr_7VgIqa_ivBFRjWa5tOIwK1pyTL3Q"
CHANNEL_ID = -1002757443787  # Kanal ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Foydalanuvchilarni vaqt bilan saqlash
users = {}

@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=True))
async def track_new_member(event: ChatMemberUpdated, bot: Bot):
    if event.chat.id == CHANNEL_ID and event.new_chat_member.status == "member":
        user_id = event.from_user.id
        users[user_id] = datetime.datetime.now()
        print(f"{user_id} qo‘shildi, vaqt saqlandi.")

async def check_expired():
    while True:
        now = datetime.datetime.now()
        for user_id, joined in list(users.items()):
            if (now - joined).days >= 30:
                try:
                    # Avval ban, keyin unban → faqat chiqarib yuborish uchun
                    await bot.ban_chat_member(CHANNEL_ID, user_id)
                    await bot.unban_chat_member(CHANNEL_ID, user_id)
                    print(f"{user_id} chiqarildi (30 kun o‘tdi).")
                    del users[user_id]
                except Exception as e:
                    print(f"Xato: {e}")
        await asyncio.sleep(3600)  # Har soatda tekshiradi

async def main():
    asyncio.create_task(check_expired())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())