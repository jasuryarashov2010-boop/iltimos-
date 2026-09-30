from aiogram.fsm.state import State, StatesGroup


class RecommendationFlow(StatesGroup):
    title = State()
    author = State()
    review = State()
    photo = State()


class EditRecommendationFlow(StatesGroup):
    field = State()
    value = State()


class RejectFlow(StatesGroup):
    reason = State()


class SupportFlow(StatesGroup):
    message = State()


class SupportReplyFlow(StatesGroup):
    reply = State()


class BroadcastFlow(StatesGroup):
    text = State()


class ReactionFlow(StatesGroup):
    emoji = State()


class DesignFlow(StatesGroup):
    header = State()
    footer = State()


class ChannelSettingFlow(StatesGroup):
    target_id = State()
    target_url = State()
    subscription_id = State()
    subscription_url = State()


class UserSearchFlow(StatesGroup):
    query = State()
