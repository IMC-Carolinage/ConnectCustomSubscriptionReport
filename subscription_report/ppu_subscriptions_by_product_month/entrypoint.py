# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Carolina Giménez Escalante
# All rights reserved.
#

from cnct import R
from subscription_report.subscriptions_by_creation_date.utils import get_basic_value
from .utils import now_str, last_month_period_str, get_first_day_last_month, get_last_day_last_month


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
    requests = _get_subscriptions(client, parameters)

    progress = 0
    total = requests.count()

    for request in requests:
        is_ppu_subscription = False
        reconciliation_param = ''
        description = ''
        mpn = ''
        for item in request['items']:
            if get_basic_value(item, 'quantity') == 'unlimited' \
                    and get_basic_value(item, 'item_type') == 'PPU':
                is_ppu_subscription = True
                description = get_basic_value(item, 'display_name')
                mpn = get_basic_value(item, 'mpn')
                break

        if is_ppu_subscription:
            for param in request['params']:
                if get_basic_value(param, 'id') == parameters['parameter_id']:
                    reconciliation_param = get_basic_value(param, 'value')

            record_note = '#' + reconciliation_param + ' - ' + description + " - " + last_month_period_str()
            yield (
                now_str(),
                record_note,
                'item.mpn',
                mpn,
                '',
                0,
                get_first_day_last_month().strftime('%Y-%m-%d %H:%M:%S'),
                get_last_day_last_month().strftime('%Y-%m-%d %H:%M:%S'),
                'parameter.' + parameters['parameter_id'],
                reconciliation_param
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
