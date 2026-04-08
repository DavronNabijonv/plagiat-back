from config.env import env


PAYME_ID = env.str("PAYME_ID")
PAYME_KEY = env.str("PAYME_KEY")
PAYME_ACCOUNT_FIELD = "id"
PAYME_AMOUNT_FIELD = "total_price"
PAYME_ACCOUNT_MODEL = "core.apps.shared.models.Order"
PAYME_ONE_TIME_PAYMENT = True
