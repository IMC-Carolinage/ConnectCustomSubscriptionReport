# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Carolina Giménez Escalante
# All rights reserved.
#

from subscription_report.subscriptions_by_creation_date.entrypoint import generate


def test_subscriptions_by_creation_date(progress, client_factory, response_factory):
    responses = []

    parameters = {
        "date": {
            "after": "2021-01-01T00:00:00",
            "before": "2021-12-01T00:00:00",
        },
        "product": {
            "all": True,
            "choices": [],
        },
        "rr_status": {
            "all": True,
            "choices": [],
        },
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
            query='and(ge(created,2021-01-01T00:00:00),le(created,2021-12-01T00:00:00),in(status,'
                  '(tiers_setup,inquiring,pending,approved,failed,draft)))',
            value=[ff_request],
        ),
    )

    client = client_factory(responses)

    result = list(generate(client, parameters, progress))

    assert len(result) == 18


def test_generate_additional(progress, client_factory, response_factory, ff_request):
    responses = []

    parameters = {
        "date": {
            "after": "2021-01-01T00:00:00",
            "before": "2021-12-01T00:00:00",
        },
        "product": {
            "all": False,
            "choices": [
                "PRD-276-377-545",
            ],
        },
        "rr_status": {
            "all": False,
            "choices": ['approved'],
        },
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
            query='and(ge(created,2021-01-01T00:00:00),le(created,2021-12-01T00:00:00),'
                  'in(asset.product.id,(PRD-276-377-545)),in(status,'
                  '(approved)),in(asset.marketplace.id,(MP-91673)))',
            value=[ff_request],
        ),
    )

    client = client_factory(responses)

    result = list(generate(client, parameters, progress))

    assert len(result) == 18
