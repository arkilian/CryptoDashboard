#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.cardano_sync import sync_all_cardano_wallets_for_user

if __name__ == "__main__":
    res = sync_all_cardano_wallets_for_user(wallet_ids=[2], max_pages=20)
    print(res)
