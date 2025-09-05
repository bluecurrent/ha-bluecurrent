"""Constants for the Blue Current integration."""

import logging

DOMAIN = "blue_current"

LOGGER = logging.getLogger(__package__)

EVSE_ID = "evse_id"
MODEL_TYPE = "model_type"
CARD = "card"
UID = "uid"
BCU_APP = "BCU-APP"
WITHOUT_CHARGING_CARD = "without_charging_card"
CHARGING_CARD_ID = "charging_card_id"
SERVICE_START_CHARGE_SESSION = "start_charge_session"
PLUG_AND_CHARGE = "plug_and_charge"
VALUE = "value"
PERMISSION = "permission"
CHARGEPOINT_STATUS = "CH_STATUS"
CHARGEPOINT_SETTINGS = "CH_SETTINGS"
BLOCK = "block"
UNAVAILABLE = "unavailable"
AVAILABLE = "available"
DELAYED = "delayed"
CHARGING = "charging"
LINKED_CHARGE_CARDS = "linked_charge_cards_only"
PUBLIC_CHARGING = "public_charging"
ACTIVITY = "activity"
VEHICLE_STATUS = "vehicle_status"
VEHICLE_ERROR = "vehicle_error"

DELAYED_CHARGING = "delayed_charging"
PRICE_BASED_CHARGING = "price_based_charging"
SMART_CHARGING = "smart_charging"
