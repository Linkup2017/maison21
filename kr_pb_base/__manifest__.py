{
    "name": "Popbill HomeTax Base",
    "summary": "Popbill HomeTax Base",
    "author": "LinkU Info Tech",
    "license": "OPL-1",
    "application": True,
    "depends": ["base", "account", "kr_etax", "hr_expense"],
    "data": [
        "wizard/point.xml",
        "wizard/point_charger.xml",
        "security/hometax_security.xml",
        "security/ir.model.access.csv",
        "views/hometax.xml",
        "views/res_company_view.xml",
        "views/account_view.xml",
        "views/res_config_settings_views.xml",
             ],
}
