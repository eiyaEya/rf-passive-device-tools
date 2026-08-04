#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal ADS 2020 Datalink round-trip test."""

import ads


data, _strings = ads.get()
ads.send(data)
