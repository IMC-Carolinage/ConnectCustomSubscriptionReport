# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Carolina Giménez Escalante
# All rights reserved.
#

from cnct import R
from .utils import convert_to_datetime, get_basic_value, get_value, today_str


def generate(client, parameters, progress_callback):
    """
    Extracts data from Connect using the ConnectClient instance
    and input parameters provided as arguments, applies
    required transformations (if any) and returns an iterator of rows
    that will be used to fill the Excel file.
    Each element returned by the iterator must be an iterator over
    the columns value.
    :param client: An instance of the CloudBlue Connect
                    client.
    :type client: connect.client.ConnectClient
    :param parameters: Input parameters used to calculate the
                        resulting dataset.
    :type parameters: dict
    :param progress_callback: A function that accepts t
                                argument of type int that must
                                be invoked to notify the progress
                                of the report generation.
    :type progress_callback: func
    """
    subscriptions = _get_subscriptions(client, parameters)

    progress = 0
    total = subscriptions.count()

    for subscription in subscriptions:
        subscription_id = get_basic_value(subscription, 'id')
        for item in _get_items(client, subscription_id):
            if (get_basic_value(item, 'item_type') != 'PPU'
                    and get_basic_value(item, 'quantity') != '0'
                    and get_basic_value(item, 'display_name').__contains__('- Reference') is False):
                yield (
                    get_basic_value(subscription, 'id'),
                    get_basic_value(subscription, 'external_id'),
                    get_basic_value(item, 'display_name'),
                    get_basic_value(item, 'mpn'),
                    get_basic_value(item, 'period'),
                    get_basic_value(item, 'quantity'),
                    get_value(subscription['tiers'], 'customer', 'id'),
                    get_value(subscription['tiers'], 'customer', 'name'),
                    get_value(subscription['tiers'], 'customer', 'external_id'),
                    get_value(subscription['tiers'], 'tier1', 'id'),
                    get_value(subscription['tiers'], 'tier1', 'name'),
                    get_value(subscription['tiers'], 'tier1', 'external_id'),
                    get_value(subscription['tiers'], 'tier2', 'id'),
                    get_value(subscription['tiers'], 'tier2', 'name'),
                    get_value(subscription['tiers'], 'tier2', 'external_id'),
                    get_value(subscription['connection'], 'provider', 'id'),
                    get_value(subscription['connection'], 'provider', 'name'),
                    get_value(subscription, 'marketplace', 'name'),
                    get_value(subscription, 'product', 'id'),
                    get_value(subscription, 'product', 'name'),
                    get_basic_value(subscription, 'status'),
                    convert_to_datetime(
                        get_value(subscription['events'], 'created', 'at'),
                    ),
                    convert_to_datetime(
                        get_value(subscription['events'], 'updated', 'at'),
                    ),
                    today_str(),
                )
        progress += 1
        progress_callback(progress, total)


def _get_subscriptions(client, parameters):
    query = R()
    query &= R().events.updated.at.ge(parameters['date']['after'])
    query &= R().events.updated.at.le(parameters['date']['before'])

    query &= R().connection.type.oneof(['production'])

    if parameters.get('product') and parameters['product']['all'] is False:
        query &= R().product.id.oneof(parameters['product']['choices'])
    if parameters.get('as_status') and parameters['as_status']['all'] is False:
        query &= R().status.oneof(parameters['as_status']['choices'])
    if parameters.get('mkp') and parameters['mkp']['all'] is False:
        query &= R().marketplace.id.oneof(parameters['mkp']['choices'])
    return client.assets.filter(query)


def _get_items(client, subscription_id):
    return client.assets[subscription_id].get()['items']
