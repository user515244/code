from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

from settings import api_token


class SomeState(StatesGroup):
    amount = State()
    wallet = State()
    accept_policy = State()


bot = Bot(token=api_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

profile_btn = KeyboardButton("Profile")
code_btn = KeyboardButton("Code")
referals_btn = KeyboardButton("Referals")
buy_crypto_btn = KeyboardButton("Buy crypto")
review_btn = KeyboardButton("Reviews")
help_btn = KeyboardButton("Help")
bnb_button = InlineKeyboardButton(text="BNB", callback_data="buy_bnb")
eth_button = InlineKeyboardButton(text="ETH", callback_data="buy_eth")
back_button = InlineKeyboardButton(text="Home", callback_data="home_btn")
start_menu = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(buy_crypto_btn, profile_btn,
                                                                                   referals_btn).add(code_btn,
                                                                                                     review_btn,
                                                                                                     help_btn)
currency_menu = InlineKeyboardMarkup().add(eth_button).add(bnb_button).add(back_button)
home_button_menu = InlineKeyboardMarkup().add(back_button)
confirm_btn: InlineKeyboardButton = InlineKeyboardButton(text="I accept", callback_data="confirm_correct1")
not_accept = InlineKeyboardButton(text="I don't accept", callback_data="go_back")
accept_menu = InlineKeyboardMarkup().add(confirm_btn, not_accept)


@dp.message_handler(commands=['start'])
async def echo_send(message: types.Message):
    await message.reply("Hello " + message.from_user.first_name, reply_markup=start_menu)


@dp.message_handler()
async def echo_send(message: types.Message):
    if message.text == "Buy crypto":
        await message.reply("Choose currency:", reply_markup=currency_menu)


@dp.callback_query_handler(text="buy_eth")
async def handle_callback_query(callback: types.CallbackQuery):
    await callback.message.edit_text("Write amount:", reply_markup=home_button_menu)
    await SomeState.amount.set()
    await callback.answer()


@dp.message_handler(state=SomeState.amount)
async def handle_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount > 10:
            await message.reply("Amount is greater than 10. Please enter your crypto wallet address:")
            await state.update_data(amount=amount)
            await SomeState.wallet.set()
        else:
            await message.reply("Amount is less than or equal to 10. Please enter a new amount:",
                                reply_markup=home_button_menu)
            await SomeState.amount.set()
    except ValueError:
        await message.reply("Invalid input. Please enter a valid amount.")


@dp.message_handler(state=SomeState.wallet)
async def handle_wallet(message: types.Message, state: FSMContext):
    wallet = message.text.strip()
    if wallet:
        await state.update_data(wallet=wallet)
        await SomeState.accept_policy.set()
        await message.reply("Please review our privacy policy and accept it by clicking the button below.",
                            reply_markup=InlineKeyboardMarkup().add(
                                InlineKeyboardButton(text="I accept", callback_data="accept_policy"),
                                InlineKeyboardButton(text="I don't accept", callback_data="decline_policy")
                            ))
    else:
        await message.reply("Invalid input. Please enter a valid wallet address.")


@dp.callback_query_handler(text="accept_policy", state=SomeState.accept_policy)
async def handle_accept_policy(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    amount = data.get("amount")
    wallet = data.get("wallet")
    if amount and wallet:
        await callback.message.edit_text(f"Amount: {amount}\nWallet: {wallet}\n\nIs everything correct?",
                                         reply_markup=accept_menu)
    else:
        await callback.message.edit_text("Invalid state. Please try again.")


@dp.callback_query_handler(text=["confirm_correct"])
async def handle_callback_query(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.reset_state()
    await callback.message.edit_text("You have confirmed the privacy policy. You will be redirected to the start menu.")


@dp.callback_query_handler(text_contains="go_back")
async def handle_go_back(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.finish()
    await callback.message.edit_text("You have declined the privacy policy. You will be redirected to the start menu.")


@dp.callback_query_handler(text="decline_policy", state=SomeState.accept_policy)
async def handle_decline_policy(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.finish()
    await callback.message.edit_text("You have declined the privacy policy. You will be redirected to the start menu.")


executor.start_polling(dp, skip_updates=True)
