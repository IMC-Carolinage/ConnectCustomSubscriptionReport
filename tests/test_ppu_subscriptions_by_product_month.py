# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Carolina Giménez Escalante
# All rights reserved.
#

from subscription_report.ppu_subscriptions_by_product_month.entrypoint import generate
from subscription_report.ppu_subscriptions_by_product_month.utils import get_last_day_last_month


def test_ppu_subscriptions_by_product_month(progress, client_factory, response_factory, ff_ppu):
    responses = []

    parameters = {
        "product": {
            "all": True,
            "choices": [],
        },
        "parameter_id": "t0_f_text",
        "mkp": {
            "all": True,
            "choices": [],
        },
    }
    responses.append(
        response_factory(
            count=1,
        ),
    )

    responses.append(
        response_factory(
            query='and(in(status,(active,suspended)),in(connection.type,(production)),'
                  'le(events.created.at,'
                  + get_last_day_last_month().strftime('%Y-%m-%dT00:00:00') + '))',
            value=[ff_ppu],
        ),
    )

    client = client_factory(responses)

    result = list(generate(client, parameters, progress))

    assert len(result) == 1


def test_generate_additional(progress, client_factory, response_factory, ff_ppu):
    responses = []

    parameters = {
        "product": {
            "all": False,
            "choices": [
                "PRD-276-377-545",
            ],
        },
        "parameter_id": "t0_f_text",
        "mkp": {
            "all": False,
            "choices": ['MP-91673'],
        },
    }
    responses.append(
        response_factory(
            count=1,
        ),
    )

    responses.append(
        response_factory(
            query='and(in(status,(active,suspended)),in(connection.type,(production)),'
                  'le(events.created.at,'
                  + get_last_day_last_month().strftime('%Y-%m-%dT00:00:00') + '),'
                  'in(product.id,(PRD-276-377-545)),in(marketplace.id,(MP-91673)))',
            value=[ff_ppu],
        ),
    )

    client = client_factory(responses)

    result = list(generate(client, parameters, progress))

    assert len(result) == 1
