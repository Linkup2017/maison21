{
    "name": "Popbill Bank",
    "summary": "Popbill Bank",
    "author": "LinkUp Info Tech",
    "license": "OPL-1",
    "application": True,
    "depends": ["base", "product", "account", "kr_pb_base"],
    "external_dependencies": {"python": ["popbill"]},
    "data": [
        "views/res_bank.xml",
        "views/history_inquiry.xml",
        "views/res_company_view.xml",
        "security/hometax_security.xml",
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "data/res.bank.list.csv",
        "wizard/search_bank.xml",
        "views/bank_list.xml",

    ],

}
