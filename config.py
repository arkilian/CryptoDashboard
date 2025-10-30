"""
Application configuration settings.
"""

# Lista de moedas que queremos acompanhar no dashboard
WATCHED_COINS = [
    "bitcoin",
    "sui",
    "solana",
    "cardano",
    "singularitynet",
    "minswap",
    "indigo-dao-governance-token",
    "liqwid-finance",
    "world-mobile-token",
    "fluidtokens",
    "palm-economy",
    "iagon",
    "optim-finance",
    "talos",
    "genius-yield",
    "dexhunter",
    "nuvola-digital",
    "charli3",
    "metera",
    "aada-finance",
    "djed",
    "iusd"
]

# Cache durations (in seconds)
USERS_CACHE_DURATION = 30  # Cache user list for 30 seconds
GENDER_CACHE_DURATION = 3600  # Cache gender list for 1 hour (static data)
API_CACHE_DURATION = 30  # Cache API responses for 30 seconds
