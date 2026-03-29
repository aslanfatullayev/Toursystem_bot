from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    language = State()
    name = State()
    age = State()
    phone = State()
    tg_username = State()


class ClientStates(StatesGroup):
    ai_chat = State()


class ManagerStates(StatesGroup):
    replying = State()   # data: lead_id, client_id


class AddTour(StatesGroup):
    title = State()
    description = State()
    country = State()
    price = State()
    dates = State()
