{
    "name": "Popbill HomeTax Issue",
    "summary": "Popbill HomeTax Issue",
    "author": "LinkUp Info Tech",
    "license": "AGPL-3",
    "application": True,
    "depends": ["base", "product", "account", "kr_etax", "kr_pb_base"],
    "external_dependencies": {"python": ["popbill"]},
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/hometax_move.xml",
        "wizard/orders.xml",

    ],

    "qweb": [],
}
