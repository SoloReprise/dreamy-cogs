# whismur.py
pokemon_info = {
    "name": "Whismur",
    "description": "Awarded for accumulating 240 minutes in voice chat.",
    # Here, the lambda directly takes voice chat time in seconds
    "award_condition": lambda voice_chat_time: voice_chat_time >= 240 * 60  # 240 minutes to seconds
}