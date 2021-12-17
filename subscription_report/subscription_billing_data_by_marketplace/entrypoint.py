# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Carolina Giménez Escalante
# All rights reserved.
#

from cnct import R
from subscription_report.subscriptions_by_status.utils import convert_to_datetime, get_basic_value, get_value, today_str
from subscription_report.ppu_subscriptions_by_product_month.utils import get_last_day_last_month, get_first_day_last_month


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
    susbcriptions = _get_subscriptions(client, parameters)

    progress = 0
    total = susbcriptions.count()
    start = ''
    end = ''

    for subscription in susbcriptions:
        end = ''
        start = ''
        price_list_version = ''
        requests = _get_requests(client, get_basic_value(subscription, 'id'))

        for request in requests:
            if request['type'] == 'purchase':
                start = convert_to_datetime(get_basic_value(request, 'effective_date'))
            if request['type'] == 'cancel':
                end = convert_to_datetime(get_basic_value(request, 'effective_date'))
                price_list_version = _get_price_list_version_id(client, request['asset']['product']['id'],
                                                                request['asset']['marketplace']['id'])

        if end != '' and end < get_first_day_last_month():
            continue

        for item in _get_items(client, subscription['id']):
            price = ''
            if item['quantity'].isdigit() and int(item['quantity']) > 0:
                if len(price_list_version) > 0:
                    price = _get_price(client, price_list_version, item['id'])

            yield (
                get_basic_value(subscription, 'id'),  # Subscription ID
                get_basic_value(subscription, 'external_id'),  # Subscription External ID
                get_basic_value(item, 'display_name'),  # Item Name
                get_basic_value(item, 'mpn'),  # Item MPN
                get_basic_value(item, 'period'),  # Item Period
                get_basic_value(item, 'quantity'),  # Quantity
                price,  # Unit Cost
                round(float(price)*float(get_basic_value(item, 'quantity')), 2),  # Total Cost
                get_value(subscription['tiers'], 'customer', 'id'),  # Customer ID
                get_value(subscription['tiers'], 'customer', 'name'),  # Customer Name
                get_value(subscription['tiers'], 'customer', 'external_id'),  # Customer External ID
                get_value(subscription['tiers'], 'tier1', 'id'),  # Tier 1 ID
                get_value(subscription['tiers'], 'tier1', 'name'),  # Tier 1 Name
                get_value(subscription['tiers'], 'tier1', 'external_id'),  # Tier 1 External ID
                get_value(subscription['tiers'], 'tier2', 'id'),  # Tier 2 ID
                get_value(subscription['tiers'], 'tier2', 'name'),  # Tier 2 Name
                get_value(subscription['tiers'], 'tier2', 'external_id'),  # Tier 2 External ID
                get_value(subscription['tiers'], 'provider', 'id'),  # Provider ID
                get_value(subscription['tiers'], 'provider', 'name'),  # Provider Name
                get_value(subscription, 'marketplace', 'name'),  # Marketplace
                get_value(subscription, 'product', 'id'),  # Product ID
                get_value(subscription, 'product', 'name'),  # Product Name
                get_basic_value(subscription, 'status'),  # Subscription Status
                convert_to_datetime(
                    get_value(subscription['events'], 'created', 'at'),  # Transaction  Date
                ),
                start,  # Subscription Start Date
                end,  # Subscription End Date
                today_str(),  # Exported At
            )
        progress += 1
        progress_callback(progress, total)


def _get_subscriptions(client, parameters):
    subs_types = ['active', 'suspended']

    query = R()
    query &= R().status.oneof(subs_types)
    query &= R().connection.type.oneof(['production'])
    query &= R().events.created.at.le(get_last_day_last_month())

    if parameters.get('product') and parameters['product']['all'] is False:
        query &= R().product.id.oneof(parameters['product']['choices'])
    if parameters.get('mkp') and parameters['mkp']['all'] is False:
        query &= R().marketplace.id.oneof(parameters['mkp']['choices'])

    return client.assets.filter(query)


def _get_items(client, subscription_id):
    return client.assets[subscription_id].get()['items']


def _get_requests(client, asset_id):
    query = R()
    query &= R().created.le(get_last_day_last_month())
    query &= R().status.oneof(['approved'])
    query &= R().asset.id.oneof([str(asset_id)])

    return client.requests.filter(query).order_by("-created")


def _get_price_list_version_id(client, product_id, marketplace_id):
    # {{baseUrl}}/listings?product.id=CN-852-370-144&marketplace__id=MP-36993
    # pricelist id
    # {{baseUrl}}/pricing/versions?pricelist.id=PL-297-236-398&status=active
    # id
    query = R()
    query &= R().product.id.oneof([product_id])
    query &= R().marketplace.id.oneof([marketplace_id])

    listings = client.listings.filter(query)
    # TODO: SI no tiene pricelist el listing falla esta instrucción
    if listings.count() > 0 and 'pricelist' in listings.first():
            price_list_id = listings.first()['pricelist']['id']
            query = R()
            query &= R().pricelist.id.oneof([price_list_id])
            query &= R().status.oneof(['active'])

            versions = client('pricing').versions.filter(query)
            if versions.count() > 0:
                return versions[0]['id']

    return ''


def _get_price(client, version_id, item_global_id):
    # {{baseUrl}}/pricing/versions/PLV-384-922-200-0001/points?item.global_id=CN-852-370-144-0002
    # attributes price
    item_global_id = item_global_id.replace('_', '-')
    query = R()
    query &= R().item.global_id.oneof([item_global_id])
    att_list = client('pricing').versions[version_id].points.filter(query)
    if att_list.count() > 0:
        return att_list.first()['attributes']['price']
    return item_global_id

