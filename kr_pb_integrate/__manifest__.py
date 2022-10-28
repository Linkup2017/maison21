{
    "name": "Popbill HomeTax Intgerate",
    "summary": "Popbill Hometax Intgerate",
    "author": "LinkUp Info Tech",
    "license": "OPL-1",
    "application": True,
    "depends": ["base", "product", "account", "kr_etax", "kr_pb_base"],
    "external_dependencies": {"python": ["popbill"]},
    "data": [
        "data/ir_cron.xml",
        "views/hometax_move.xml",

    ],

}
